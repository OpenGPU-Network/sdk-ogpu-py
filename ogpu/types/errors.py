"""Exception hierarchy for the OGPU SDK.

Every SDK exception inherits from ``OGPUError``. Seven abstract intermediate
classes group concrete errors by failure domain so callers can write precise
``except`` clauses without catching unrelated failures.

```
OGPUError
├── NotFoundError   — entity missing at the given address
├── StateError      — operation not valid in current on-chain state
├── PermissionError — caller is not authorized
├── VaultError      — vault-specific failures
├── TxError         — transaction-layer failures
├── ConfigError     — SDK configuration issues
└── IPFSError       — IPFS publish or fetch failures
```

Every concrete error carries the data it was raised with (addresses,
amounts, reasons) as typed attributes, so you can use them for structured
logging without having to parse the message string.

Example:
    ```python
    from ogpu.types import InsufficientBalanceError, VaultError, OGPUError

    try:
        vault.lock(10**20, signer=KEY)
    except InsufficientBalanceError as e:
        print(f"need {e.required}, have {e.available}")
    except VaultError:
        print("other vault failure")
    except OGPUError:
        print("other SDK failure")
    ```
"""

from __future__ import annotations

from .enums import Role


class OGPUError(Exception):
    """Root of all SDK exceptions.

    Catch this when you want to handle any SDK-originated failure
    without distinguishing the specific cause — useful for top-level
    error boundaries, logging, retry loops.
    """


# ---------------------------------------------------------------------------
# NotFoundError domain
# ---------------------------------------------------------------------------


class NotFoundError(OGPUError):
    """Abstract: an on-chain entity could not be resolved at the given address.

    Raised by the ``.load()`` eager constructors of instance classes
    (``Source.load``, ``Task.load``, etc.) when the given address
    doesn't respond to a cheap view call.
    """


class TaskNotFoundError(NotFoundError):
    """No ``Task`` contract exists at the given address.

    Raised by ``Task.load(address)`` when the cheap ``getStatus()`` probe
    reverts. Usually means the address is wrong, was never a task, or
    belongs to a different chain.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Task contract not found at address {address}")


class SourceNotFoundError(NotFoundError):
    """No ``Source`` contract exists at the given address.

    Raised by ``Source.load(address)`` when the cheap ``getStatus()``
    probe reverts.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Source contract not found at address {address}")


class ResponseNotFoundError(NotFoundError):
    """No ``Response`` contract exists at the given address.

    Raised by ``Response.load(address)`` when the cheap ``getStatus()``
    probe reverts.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Response contract not found at address {address}")


class ProviderNotFoundError(NotFoundError):
    """The given address is not registered as a provider.

    Raised by ``Provider.load(address)`` when ``Terminal.isProvider``
    returns False.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Provider not registered at address {address}")


class MasterNotFoundError(NotFoundError):
    """The given address is not registered as a master.

    Raised by ``Master.load(address)`` when ``Terminal.isMaster``
    returns False.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Master not registered at address {address}")


# ---------------------------------------------------------------------------
# StateError domain
# ---------------------------------------------------------------------------


class StateError(OGPUError):
    """Abstract: operation is not valid in the current on-chain state.

    The entity exists, the caller is authorized, but the state machine
    disallows the operation — e.g. cancelling a task that's already
    finalized, confirming a response that's already confirmed.
    """


class TaskExpiredError(StateError):
    """Task's ``expiryTime`` has passed — no more attempts can be submitted.

    Attributes:
        task: Task contract address.
        expiry: Unix timestamp when the task expired.
    """

    def __init__(self, task: str, expiry: int) -> None:
        self.task = task
        self.expiry = expiry
        super().__init__(f"Task {task} expired at unix timestamp {expiry}")


class TaskAlreadyFinalizedError(StateError):
    """Task is in ``FINALIZED`` state and cannot be modified.

    Raised when attempting to cancel or re-finalize a task that has
    already reached terminal state.

    Attributes:
        task: Task contract address.
    """

    def __init__(self, task: str) -> None:
        self.task = task
        super().__init__(f"Task {task} is already finalized")


class ResponseAlreadyConfirmedError(StateError):
    """Response is already confirmed — calling ``confirm`` again reverts.

    Attributes:
        response: Response contract address.
    """

    def __init__(self, response: str) -> None:
        self.response = response
        super().__init__(f"Response {response} is already confirmed")


class SourceInactiveError(StateError):
    """Source is in ``INACTIVE`` state and cannot accept new tasks.

    Raised by ``publish_task`` when the target source has been
    inactivated via ``inactivate_source``.

    Attributes:
        source: Source contract address.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        super().__init__(f"Source {source} is inactive and cannot accept tasks")


# ---------------------------------------------------------------------------
# PermissionError domain
# ---------------------------------------------------------------------------


class PermissionError(OGPUError):  # noqa: A001 — shadows builtins.PermissionError by design
    """Abstract: caller does not have permission for this operation.

    Raised when the signer of a transaction is not authorized to perform
    the requested action — wrong role, wrong owner, not a registered
    provider, etc.
    """


class NotTaskOwnerError(PermissionError):
    """Caller is not the client that owns the target task.

    Raised on operations like ``cancel_task`` or ``confirm_response``
    when the signer is not the address that originally published the task.

    Attributes:
        task: Task contract address.
        caller: Address that tried to call the protected operation.
    """

    def __init__(self, task: str, caller: str) -> None:
        self.task = task
        self.caller = caller
        super().__init__(f"Caller {caller} is not the owner of task {task}")


class NotSourceOwnerError(PermissionError):
    """Caller is not the client that owns the target source.

    Raised on operations like ``update_source`` or ``inactivate_source``
    when the signer is not the original publisher of the source.

    Attributes:
        source: Source contract address.
        caller: Address that tried to call the protected operation.
    """

    def __init__(self, source: str, caller: str) -> None:
        self.source = source
        self.caller = caller
        super().__init__(f"Caller {caller} is not the owner of source {source}")


class NotMasterError(PermissionError):
    """Account is not registered as a master.

    Raised on master-role operations (``announce_provider``,
    ``remove_provider``, etc.) when the signer is not a master.

    Attributes:
        account: Address that tried to call the master-role operation.
    """

    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not registered as a master")


class NotProviderError(PermissionError):
    """Account is not registered as a provider.

    Raised on provider-role operations (``announce_master``,
    ``attempt``) when the signer is not a provider.

    Attributes:
        account: Address that tried to call the provider-role operation.
    """

    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not registered as a provider")


# ---------------------------------------------------------------------------
# VaultError domain
# ---------------------------------------------------------------------------


class VaultError(OGPUError):
    """Abstract: Vault-specific failure.

    Raised by ``ogpu.protocol.vault`` operations when the vault state
    does not allow the requested action (insufficient balance, lockup
    too low, unbonding period not elapsed, etc.).
    """


class InsufficientBalanceError(VaultError):
    """Vault balance is too low for the requested operation.

    Raised by ``withdraw``, ``lock``, or any operation that moves funds
    when the caller's available balance is less than what they asked for.

    Attributes:
        account: Address whose balance is insufficient.
        required: Amount the operation needed, in wei.
        available: Amount actually available, in wei.
    """

    def __init__(self, account: str, required: int, available: int) -> None:
        self.account = account
        self.required = required
        self.available = available
        super().__init__(
            f"Account {account} has insufficient balance: "
            f"required {required}, available {available}"
        )


class InsufficientLockupError(VaultError):
    """Locked (staked) amount is too low for the requested operation.

    Raised by ``unbond`` when the amount requested exceeds the currently
    locked balance, or by registration flows that require a minimum
    lockup per source.

    Attributes:
        account: Address whose lockup is insufficient.
        required: Amount the operation needed, in wei.
        available: Amount actually locked, in wei.
    """

    def __init__(self, account: str, required: int, available: int) -> None:
        self.account = account
        self.required = required
        self.available = available
        super().__init__(
            f"Account {account} has insufficient lockup: "
            f"required {required}, available {available}"
        )


class UnbondingPeriodNotElapsedError(VaultError):
    """Cannot ``claim`` yet — the unbonding cooldown hasn't elapsed.

    Attributes:
        account: Address attempting to claim.
        remaining_seconds: Seconds left before the unbonding period
            matures and the claim will succeed.
    """

    def __init__(self, account: str, remaining_seconds: int) -> None:
        self.account = account
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Unbonding period for {account} has {remaining_seconds} seconds remaining"
        )


class NotEligibleError(VaultError):
    """Account is not eligible for this vault operation.

    Raised when ``Vault.isEligible`` returns False — typically because
    the account is not whitelisted or is below some protocol-level
    eligibility threshold.

    Attributes:
        account: Address that failed the eligibility check.
    """

    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not eligible for this vault operation")


# ---------------------------------------------------------------------------
# TxError domain
# ---------------------------------------------------------------------------


class TxError(OGPUError):
    """Abstract: transaction-layer failure.

    Catches revert, nonce, gas, and RPC issues. These are distinct from
    ``StateError`` in that the problem is at the transaction layer
    (signing, broadcasting, inclusion) rather than the contract's
    business logic — though in practice contract reverts are mapped
    into ``TxRevertError`` for consistency.
    """


class TxRevertError(TxError):
    """Transaction reverted for a reason the SDK could not map to a typed error.

    The SDK maintains a ``REVERT_PATTERN_MAP`` that translates known
    revert strings into specific ``PermissionError`` / ``StateError`` /
    ``VaultError`` subclasses. Any revert that doesn't match a known
    pattern ends up here as a fallback.

    Attributes:
        reason: The raw revert reason string extracted from the
            underlying ``ContractLogicError``.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Transaction reverted: {reason}")


class NonceError(TxError):
    """Nonce collision that ``TxExecutor`` could not auto-recover from.

    ``TxExecutor`` automatically retries on ``nonce too low`` /
    ``already known`` / ``replacement transaction underpriced`` — this
    error is only raised when retries are exhausted. Use
    ``ogpu.fix_nonce`` to manually clear stuck pending transactions.

    Attributes:
        address: Address whose nonce collided.
        tried: Nonce the SDK attempted to use.
        suggested: Nonce the SDK suggests using next (or -1 if unknown).
    """

    def __init__(self, address: str, tried: int, suggested: int) -> None:
        self.address = address
        self.tried = tried
        self.suggested = suggested
        super().__init__(
            f"Nonce error for {address}: tried {tried}, suggested {suggested}"
        )


class GasError(TxError):
    """Gas-related transaction failure.

    Raised when the SDK cannot recover from an underpriced transaction
    after retry with backoff, or when gas estimation fails.

    Attributes:
        reason: Human-readable description of the failure.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Gas error: {reason}")


class InvalidRpcUrlError(TxError):
    """RPC URL is not reachable or failed the connectivity probe.

    Raised by ``ChainConfig.set_rpc`` when ``Web3.is_connected()``
    returns False against the given URL.

    Attributes:
        url: The RPC URL that failed the probe.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"RPC URL is not reachable: {url}")


# ---------------------------------------------------------------------------
# ConfigError domain
# ---------------------------------------------------------------------------


class ConfigError(OGPUError):
    """Abstract: SDK configuration is missing or invalid.

    Raised when the SDK cannot proceed because required configuration
    (signer, chain, RPC) is missing or malformed.
    """


class MissingSignerError(ConfigError):
    """No signer provided and no env-var fallback resolved.

    For role-based calls this means the relevant ``*_PRIVATE_KEY`` env
    var is not set. For vault calls (where env-var fallback is
    disabled by design), this means no ``signer=`` kwarg was passed.

    Attributes:
        role: The ``Role`` the operation expected, or ``None`` for
            vault calls that require an explicit signer.
    """

    def __init__(self, role: Role | None = None) -> None:
        self.role = role
        if role is None:
            msg = (
                "No signer provided and no env-var fallback is allowed "
                "for this operation (e.g. Vault calls require explicit signer=)."
            )
        else:
            env_var = f"{role.value.upper()}_PRIVATE_KEY"
            msg = (
                f"No signer provided and environment variable {env_var} is not set. "
                f"Pass signer= explicitly or set {env_var}."
            )
        super().__init__(msg)


class InvalidSignerError(ConfigError):
    """Signer value was not a valid key or address.

    Raised by ``resolve_signer`` when the given value is neither a hex
    key nor a ``LocalAccount``, or by write operations given malformed
    address arguments.

    Attributes:
        reason: Human-readable description of why the value was rejected.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid signer: {reason}")


class ChainNotSupportedError(ConfigError):
    """Chain identifier does not correspond to a supported OGPU chain.

    Raised by ``ChainConfig.set_chain`` / ``set_rpc`` / ``get_rpc`` when
    the given ``ChainId`` is not in ``CHAIN_CONTRACTS``.

    Attributes:
        chain_id: The chain identifier that failed the check.
    """

    def __init__(self, chain_id: object) -> None:
        self.chain_id = chain_id
        super().__init__(f"Chain {chain_id!r} is not supported")


# ---------------------------------------------------------------------------
# IPFSError domain
# ---------------------------------------------------------------------------


class IPFSError(OGPUError):
    """Abstract: IPFS publish or fetch failure.

    Raised by ``ogpu.ipfs`` helpers and by any method that internally
    uploads or downloads off-chain content (``get_metadata``,
    ``fetch_data``).
    """


class IPFSFetchError(IPFSError):
    """Network or JSON-parse failure while fetching from IPFS.

    Raised when the HTTP GET fails, the response body is not valid
    JSON, or the request times out.

    Attributes:
        url: The URL that was being fetched.
        reason: Human-readable description of the failure.
    """

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch from IPFS {url}: {reason}")


class IPFSGatewayError(IPFSError):
    """IPFS gateway returned a non-success HTTP status.

    Raised when the gateway responded but with a 4xx or 5xx status, or
    when the response body is structurally unexpected (missing ``link``
    field on a publish response, etc.).

    Attributes:
        gateway: The gateway URL that returned the bad status.
        status_code: The HTTP status code received.
    """

    def __init__(self, gateway: str, status_code: int) -> None:
        self.gateway = gateway
        self.status_code = status_code
        super().__init__(
            f"IPFS gateway {gateway} returned HTTP {status_code}"
        )
