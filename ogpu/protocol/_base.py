"""Shared infrastructure for the protocol layer.

Contains the single implementation of transaction sending (``TxExecutor``),
paginated reads (``_paginated_call``), contract loading, the revert-pattern
map, and the ``ZERO_ADDRESS`` / ``_DEFAULT_CHUNK_SIZE`` constants. Everything
in ``ogpu.protocol`` that touches the chain funnels through this module.
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
    """Load a ``web3.contract.Contract`` by ABI name.

    When ``address`` is ``None``, the matching singleton address from
    ``ChainConfig`` is used (for ``NexusAbi`` / ``ControllerAbi`` / ``TerminalAbi``).
    Instance-bound ABIs (``TaskAbi``, ``SourceAbi``, ``ResponseAbi``) require an
    explicit address.
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

    When ``upper`` is ``None``, ``count_fn`` is called to determine the total
    and the fetch is split into ``chunk_size`` chunks. Zero-address entries
    are filtered out silently (per K4 — no warnings, no hard limits).
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


RevertHandler = Callable[[str, str, str], OGPUError]


def _permission_error_for(context: str, caller: str) -> OGPUError:
    """Context-sensitive ``NotOwner`` revert handler.

    The bare ``NotOwner`` revert string is ambiguous — it could come from
    Task, Source, or Response. The handler looks at the contract context
    to choose the correct typed exception.
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


def _extract_revert_reason(exc: BaseException) -> str:
    """Pull the revert reason string out of a web3 ``ContractLogicError``."""
    message = str(exc)
    if message.startswith("execution reverted:"):
        return message.split(":", 1)[1].strip()
    if "revert" in message.lower():
        idx = message.lower().find("revert")
        return message[idx + len("revert") :].strip(": ").strip()
    return message


def decode_revert(exc: BaseException, *, context: str, caller: str) -> OGPUError:
    """Decode a ``ContractLogicError`` into a typed SDK exception."""
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
    """Single-shot transaction sender with retry, nonce management, and revert decoding.

    Replaces the duplicated retry/nonce/revert logic that used to live in
    ``publish_task``, ``publish_source``, ``confirm_response``, and
    ``agent/terminal.set_agent``. Every write in the protocol layer funnels
    through ``TxExecutor(...).execute()``.
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
