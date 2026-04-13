"""Shared infrastructure for the protocol layer.

This private module holds the pieces every protocol operation reuses:

- **``TxExecutor``** — single transaction sender with nonce management,
  retry on recoverable errors, gas handling, and typed revert decoding.
  Every write in ``ogpu.protocol`` (and therefore everything higher up)
  goes through this class. It replaces the ~300 lines of copy-pasted
  retry logic that used to live in separate ``publish_*`` functions.
- **``load_contract``** — resolves an ABI name + optional address to a
  ``web3.contract.Contract`` instance. Handles the singleton mapping
  for Nexus/Controller/Terminal/Vault.
- **``_paginated_call``** — shared helper for list-returning reads with
  ``(lower, upper)`` semantics. Transparently handles ``upper=None``
  "fetch all" by calling the matching count function and iterating in
  ``_DEFAULT_CHUNK_SIZE`` chunks.
- **``decode_revert``** — turns a raw ``ContractLogicError`` into a
  typed SDK exception via ``REVERT_PATTERN_MAP``.
- **``ZERO_ADDRESS``** — constant for the null address, used to filter
  unallocated slots out of paginated reads.

This module is private (no leading underscore, but not re-exported from
``ogpu.protocol.__init__``). Users interact with it indirectly through
instance classes and module-level functions. Refer to the
[reference: protocol](../reference/protocol.md) for the public surface.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError

from ..types.errors import (
    GasError,
    InsufficientBalanceError,
    InsufficientLockupError,
    NonceError,
    NotEligibleError,
    NotMasterError,
    NotProviderError,
    NotSourceOwnerError,
    NotTaskOwnerError,
    OGPUError,
    ResponseAlreadyConfirmedError,
    SourceInactiveError,
    TaskAlreadyFinalizedError,
    TaskExpiredError,
    TxError,
    TxRevertError,
    UnbondingPeriodNotElapsedError,
)
from ..types.receipt import Receipt

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
_DEFAULT_CHUNK_SIZE = 100

_NONCE_ERROR_SUBSTRINGS = (
    "nonce too low",
    "known transaction",
    "already known",
)
_UNDERPRICED_SUBSTRING = "replacement transaction underpriced"
_UNDERPRICED_BACKOFF_SECONDS = 5

_SINGLETON_ABI_TO_KEY: dict[str, str] = {
    "NexusAbi": "NEXUS",
    "ControllerAbi": "CONTROLLER",
    "TerminalAbi": "TERMINAL",
    "VaultAbi": "VAULT",
}


def _get_web3() -> Web3:
    from ..chain.web3 import Web3Manager

    return Web3Manager.get_web3_instance()


def load_contract(abi_name: str, address: str | None = None) -> Contract:
    """Load a ``web3.contract.Contract`` for an ABI + address.

    Two modes:

    1. **Singleton resolution** (``address=None``) — for the four
       protocol-level singletons (Nexus, Controller, Terminal, Vault),
       looks up the address from ``ChainConfig.CHAIN_CONTRACTS`` for
       the current chain and wraps it with the matching ABI.
    2. **Explicit address** — for instance-bound contracts (Source, Task,
       Response), pass the deployed contract address directly.

    The ABI is loaded via ``ChainConfig.load_abi`` which caches the
    parsed JSON per chain, so subsequent calls are cheap.

    Args:
        abi_name: ABI file basename without extension. Known singleton
            ABIs: ``"NexusAbi"``, ``"ControllerAbi"``, ``"TerminalAbi"``,
            ``"VaultAbi"``. Known instance ABIs: ``"SourceAbi"``,
            ``"TaskAbi"``, ``"ResponseAbi"``.
        address: Contract address. Omit for singleton ABIs.

    Returns:
        A ``web3.contract.Contract`` bound to the resolved address and
        the requested ABI.

    Raises:
        ValueError: If ``abi_name`` is an instance ABI and no ``address``
            was given.
        FileNotFoundError: If the ABI file doesn't exist for the current
            chain.

    Example:
        ```python
        # Singleton
        nexus = load_contract("NexusAbi")

        # Instance
        task = load_contract("TaskAbi", address="0x...")
        ```
    """
    from ..chain.config import ChainConfig

    web3 = _get_web3()
    abi = ChainConfig.load_abi(abi_name)

    if address is None:
        key = _SINGLETON_ABI_TO_KEY.get(abi_name)
        if key is None:
            raise ValueError(
                f"ABI {abi_name} has no singleton address configured; pass an explicit address"
            )
        address = ChainConfig.get_contract_address(key)

    return web3.eth.contract(address=web3.to_checksum_address(address), abi=abi)


def _paginated_call(
    count_fn: Callable[[], int],
    fetch_fn: Callable[[int, int], Iterable[Any]],
    lower: int = 0,
    upper: int | None = None,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
) -> list[Any]:
    """Fetch a range of items from a paginated contract read.

    Every list-returning read in the protocol layer goes through this
    helper so they share one chunking strategy. When ``upper`` is
    ``None`` (the default on every public method that takes pagination),
    the helper calls ``count_fn()`` to determine the total and iterates
    through ``fetch_fn(lower, min(lower + chunk_size, total))`` until
    the full range is covered.

    Zero-address entries are filtered out silently — on-chain paginated
    arrays can contain sparse holes where slots were removed, and those
    should never surface to user code. No warnings, no hard caps — if
    you ask for 100k items, you get 100k items.

    Args:
        count_fn: Callable that returns the total number of items.
            Called only when ``upper is None``.
        fetch_fn: Callable ``(lower, upper) -> iterable`` that returns
            a slice of items between the given indices.
        lower: Start index (inclusive). Defaults to 0.
        upper: End index (exclusive). When ``None``, the full list is
            fetched via ``count_fn``.
        chunk_size: Maximum number of items to fetch in one RPC call.
            Defaults to 100.

    Returns:
        A flat list of non-zero items in the requested range.
    """
    if upper is None:
        upper = int(count_fn())

    results: list[Any] = []
    current = lower
    while current < upper:
        chunk_end = min(current + chunk_size, upper)
        chunk = fetch_fn(current, chunk_end)
        for item in chunk:
            if item != ZERO_ADDRESS:
                results.append(item)
        current = chunk_end
    return results


# ---------------------------------------------------------------------------
# Revert decoding
# ---------------------------------------------------------------------------


#: Type alias for entries in ``REVERT_PATTERN_MAP``. A handler takes
#: ``(reason_string, operation_context, caller_address)`` and returns a
#: fully-typed ``OGPUError`` subclass instance, ready to raise.
RevertHandler = Callable[[str, str, str], OGPUError]


def _permission_error_for(context: str, caller: str) -> OGPUError:
    """Pick the right ``PermissionError`` subclass for a bare ``NotOwner`` revert.

    The ``NotOwner`` revert string is ambiguous — it could come from
    Task, Source, or Response, each with their own typed exception.
    This helper inspects the free-form ``context`` string (which
    ``TxExecutor`` fills in as ``"Controller.cancelTask(0x...)"`` or
    similar) to decide which typed exception to raise.
    """
    lowered = context.lower()
    if "source" in lowered:
        return NotSourceOwnerError(source=context, caller=caller)
    return NotTaskOwnerError(task=context, caller=caller)


REVERT_PATTERN_MAP: dict[str, RevertHandler] = {
    "NotOwner": lambda reason, context, caller: _permission_error_for(context, caller),
    "NotMaster": lambda reason, context, caller: NotMasterError(account=caller),
    "NotProvider": lambda reason, context, caller: NotProviderError(account=caller),
    "Expired": lambda reason, context, caller: TaskExpiredError(task=context, expiry=0),
    "AlreadyConfirmed": lambda reason, context, caller: ResponseAlreadyConfirmedError(
        response=context
    ),
    "AlreadyFinalized": lambda reason, context, caller: TaskAlreadyFinalizedError(task=context),
    "InsufficientBalance": lambda reason, context, caller: InsufficientBalanceError(
        account=caller, required=0, available=0
    ),
    "InsufficientLockup": lambda reason, context, caller: InsufficientLockupError(
        account=caller, required=0, available=0
    ),
    "UnbondingNotElapsed": lambda reason, context, caller: UnbondingPeriodNotElapsedError(
        account=caller, remaining_seconds=0
    ),
    "NotEligible": lambda reason, context, caller: NotEligibleError(account=caller),
    "SourceInactive": lambda reason, context, caller: SourceInactiveError(source=context),
}


#: Map from known Solidity revert strings to typed exception factories.
#:
#: Seeded from the v0.2 contract set. Unknown revert reasons fall through
#: to ``TxRevertError(reason=...)`` — still typed, still catchable, but
#: without the specific subclass. Custom error decoding (Solidity 0.8.4+
#: typed errors) is deferred to a later release; v0.2.1 does string-based
#: matching only.
REVERT_PATTERN_MAP  # noqa: F821 — documentation anchor for the dict below


def _extract_revert_reason(exc: BaseException) -> str:
    """Pull the revert reason string out of a web3 ``ContractLogicError``.

    web3.py wraps the revert reason in different shapes depending on
    provider and version. This helper handles the common formats:
    ``"execution reverted: <reason>"``, ``"... revert <reason>"``, and
    falls back to the raw exception message otherwise.
    """
    message = str(exc)
    if message.startswith("execution reverted:"):
        return message.split(":", 1)[1].strip()
    if "revert" in message.lower():
        idx = message.lower().find("revert")
        return message[idx + len("revert") :].strip(": ").strip()
    return message


def decode_revert(exc: BaseException, *, context: str, caller: str) -> OGPUError:
    """Decode a raw ``ContractLogicError`` into a typed SDK exception.

    Extracts the revert reason, looks it up in ``REVERT_PATTERN_MAP``,
    and returns the matching typed exception. If no exact match is
    found, does a substring scan. If nothing matches, returns a generic
    ``TxRevertError(reason=...)`` — still typed and catchable via
    ``TxError``.

    Called by ``TxExecutor`` from its exception handler. The returned
    exception is **not raised by this function** — the caller raises
    it (with ``from exc`` to preserve the chain).

    Args:
        exc: The underlying ``ContractLogicError`` from web3.
        context: Free-form operation context, e.g.
            ``"Controller.cancelTask(0x...)"``. Used to disambiguate
            ``NotOwner`` reverts across Task/Source/Response.
        caller: Address of the signer that attempted the transaction.
            Embedded into the resulting ``PermissionError`` subclasses
            for better error messages.

    Returns:
        A typed ``OGPUError`` subclass ready to raise.
    """
    reason = _extract_revert_reason(exc)
    handler = REVERT_PATTERN_MAP.get(reason)
    if handler is not None:
        return handler(reason, context, caller)
    for key, hdlr in REVERT_PATTERN_MAP.items():
        if key in reason:
            return hdlr(reason, context, caller)
    return TxRevertError(reason=reason)


# ---------------------------------------------------------------------------
# TxExecutor
# ---------------------------------------------------------------------------


class TxExecutor:
    """Single-shot transaction sender with retry, nonce, and revert decoding.

    Every write operation in the SDK — ``publish_source``, ``publish_task``,
    ``confirm_response``, ``set_agent``, ``vault.lock``, etc. — constructs
    a ``TxExecutor`` and calls ``.execute()``. The executor handles:

    - **Nonce resolution** via ``NonceManager`` (with automatic retry on
      nonce collisions)
    - **Transaction building** via ``contract.functions.X.build_transaction``
    - **Signing** with the provided ``LocalAccount``
    - **Broadcasting** via ``eth.send_raw_transaction``
    - **Confirmation** via ``wait_for_transaction_receipt``
    - **Retry** on ``nonce too low`` / ``replacement transaction underpriced``
      errors, up to ``max_retries`` attempts
    - **Revert decoding** — ``ContractLogicError`` is passed through
      ``decode_revert`` and re-raised as a typed ``OGPUError`` subclass
    - **Receipt wrapping** — returns a frozen ``Receipt`` dataclass
      instead of the raw web3 ``AttributeDict``

    You usually don't construct this class directly — use the module-level
    functions (``nexus.publish_source``, ``controller.cancel_task``, etc.)
    or instance methods (``task.cancel()``, ``source.inactivate()``) and
    let them handle it.

    Attributes:
        contract: The ``web3.contract.Contract`` to call into.
        function_name: Name of the contract function to invoke.
        args: Positional arguments to pass to the function.
        signer: ``LocalAccount`` used to sign the transaction.
        value: ETH value (wei) to attach to the call. Only non-zero for
            payable functions (``Vault.deposit``, ``Terminal.announceProvider``).
        context: Free-form string used in revert decoding for
            disambiguating errors. Defaults to ``"{contract.address}.{function_name}"``.
        max_retries: Maximum retry attempts on recoverable errors
            (nonce/underpriced). Defaults to 3.

    Example:
        ```python
        from ogpu.protocol import TxExecutor, load_contract
        from eth_account import Account

        signer = Account.from_key("0x...")
        contract = load_contract("ControllerAbi")
        receipt = TxExecutor(
            contract,
            "cancelTask",
            ("0xTASK",),
            signer=signer,
        ).execute()
        print(receipt.tx_hash)
        # '0x...'
        ```
    """

    def __init__(
        self,
        contract: Contract,
        function_name: str,
        args: tuple[Any, ...] = (),
        *,
        signer: LocalAccount,
        value: int = 0,
        context: str | None = None,
        max_retries: int = 3,
    ) -> None:
        self.contract = contract
        self.function_name = function_name
        self.args = args
        self.signer = signer
        self.value = value
        self.context = context or f"{contract.address}.{function_name}"
        self.max_retries = max(1, max_retries)

    def execute(self) -> Receipt:
        """Build, sign, broadcast, and wait for the transaction.

        Runs the full retry/revert/receipt pipeline. On success returns
        a ``Receipt`` with the tx hash, block number, gas used, and
        decoded log list. On failure raises a typed ``OGPUError``
        subclass — never a raw ``ContractLogicError`` or web3 exception.

        Returns:
            A ``Receipt`` dataclass for the mined transaction.

        Raises:
            TxRevertError: Contract reverted with a reason not in
                ``REVERT_PATTERN_MAP``, or mined with ``status == 0``.
            PermissionError: Contract reverted with a known permission
                check (``NotTaskOwnerError``, ``NotSourceOwnerError``,
                ``NotMasterError``, ``NotProviderError``, etc.).
            StateError: Contract reverted in a state that doesn't allow
                the operation (``TaskExpiredError``,
                ``TaskAlreadyFinalizedError``,
                ``ResponseAlreadyConfirmedError``,
                ``SourceInactiveError``).
            VaultError: On-chain vault check failed
                (``InsufficientBalanceError``, ``InsufficientLockupError``,
                ``UnbondingPeriodNotElapsedError``, ``NotEligibleError``).
            NonceError: Nonce collision exhausted all retries.
            GasError: Underpriced transaction couldn't be recovered.
        """
        from ..chain.nonce import NonceManager

        web3 = _get_web3()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            nonce = NonceManager.get_nonce(self.signer.address, web3)
            try:
                fn = getattr(self.contract.functions, self.function_name)(*self.args)
                tx_params: dict[str, Any] = {
                    "from": self.signer.address,
                    "nonce": nonce,
                }
                if self.value:
                    tx_params["value"] = self.value
                tx = fn.build_transaction(tx_params)

                signed = web3.eth.account.sign_transaction(tx, self.signer.key)
                tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
                web3_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

                NonceManager.increment_nonce(self.signer.address, web3)

                if int(web3_receipt["status"]) != 1:
                    raise TxRevertError(
                        reason=f"Transaction {self._hex(tx_hash)} mined but reverted"
                    )

                return Receipt.from_web3_receipt(web3_receipt, timestamp=int(time.time()))

            except ContractLogicError as exc:
                raise decode_revert(exc, context=self.context, caller=self.signer.address) from exc

            except TxError:
                raise

            except Exception as exc:  # noqa: BLE001 — categorized below
                last_error = exc
                if self._is_nonce_error(exc):
                    NonceManager.reset_nonce(self.signer.address, web3)
                    if attempt < self.max_retries - 1:
                        continue
                    raise NonceError(
                        address=self.signer.address, tried=nonce, suggested=-1
                    ) from exc
                if self._is_underpriced(exc):
                    NonceManager.reset_nonce(self.signer.address, web3)
                    if attempt < self.max_retries - 1:
                        time.sleep(_UNDERPRICED_BACKOFF_SECONDS)
                        continue
                    raise GasError(reason=str(exc)) from exc
                raise

        assert last_error is not None
        raise last_error

    @staticmethod
    def _is_nonce_error(exc: BaseException) -> bool:
        msg = str(exc).lower()
        return any(s in msg for s in _NONCE_ERROR_SUBSTRINGS)

    @staticmethod
    def _is_underpriced(exc: BaseException) -> bool:
        return _UNDERPRICED_SUBSTRING in str(exc).lower()

    @staticmethod
    def _hex(tx_hash: Any) -> str:
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()
        if isinstance(tx_hash, (bytes, bytearray)):
            return tx_hash.hex()
        return str(tx_hash)
