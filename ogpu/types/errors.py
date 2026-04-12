"""Exception hierarchy for the OGPU SDK.

All SDK errors inherit from ``OGPUError``. Seven abstract intermediate classes
group them by failure domain so callers can narrow their ``except`` clauses
(``except VaultError:``) without catching every unrelated failure.
"""

from __future__ import annotations

from .enums import Role


class OGPUError(Exception):
    """Root of all SDK exceptions."""


# ---------------------------------------------------------------------------
# NotFoundError domain
# ---------------------------------------------------------------------------


class NotFoundError(OGPUError):
    """Abstract: an on-chain entity could not be resolved at the given address."""


class TaskNotFoundError(NotFoundError):
    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Task contract not found at address {address}")


class SourceNotFoundError(NotFoundError):
    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Source contract not found at address {address}")


class ResponseNotFoundError(NotFoundError):
    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Response contract not found at address {address}")


class ProviderNotFoundError(NotFoundError):
    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Provider not registered at address {address}")


class MasterNotFoundError(NotFoundError):
    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Master not registered at address {address}")


# ---------------------------------------------------------------------------
# StateError domain
# ---------------------------------------------------------------------------


class StateError(OGPUError):
    """Abstract: operation is not valid in the current on-chain state."""


class TaskExpiredError(StateError):
    def __init__(self, task: str, expiry: int) -> None:
        self.task = task
        self.expiry = expiry
        super().__init__(f"Task {task} expired at unix timestamp {expiry}")


class TaskAlreadyFinalizedError(StateError):
    def __init__(self, task: str) -> None:
        self.task = task
        super().__init__(f"Task {task} is already finalized")


class ResponseAlreadyConfirmedError(StateError):
    def __init__(self, response: str) -> None:
        self.response = response
        super().__init__(f"Response {response} is already confirmed")


class SourceInactiveError(StateError):
    def __init__(self, source: str) -> None:
        self.source = source
        super().__init__(f"Source {source} is inactive and cannot accept tasks")


# ---------------------------------------------------------------------------
# PermissionError domain
# ---------------------------------------------------------------------------


class PermissionError(OGPUError):  # noqa: A001 — shadows builtins.PermissionError by design
    """Abstract: caller does not have permission for this operation."""


class NotTaskOwnerError(PermissionError):
    def __init__(self, task: str, caller: str) -> None:
        self.task = task
        self.caller = caller
        super().__init__(f"Caller {caller} is not the owner of task {task}")


class NotSourceOwnerError(PermissionError):
    def __init__(self, source: str, caller: str) -> None:
        self.source = source
        self.caller = caller
        super().__init__(f"Caller {caller} is not the owner of source {source}")


class NotMasterError(PermissionError):
    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not registered as a master")


class NotProviderError(PermissionError):
    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not registered as a provider")


# ---------------------------------------------------------------------------
# VaultError domain
# ---------------------------------------------------------------------------


class VaultError(OGPUError):
    """Abstract: Vault-specific failure."""


class InsufficientBalanceError(VaultError):
    def __init__(self, account: str, required: int, available: int) -> None:
        self.account = account
        self.required = required
        self.available = available
        super().__init__(
            f"Account {account} has insufficient balance: "
            f"required {required}, available {available}"
        )


class InsufficientLockupError(VaultError):
    def __init__(self, account: str, required: int, available: int) -> None:
        self.account = account
        self.required = required
        self.available = available
        super().__init__(
            f"Account {account} has insufficient lockup: required {required}, available {available}"
        )


class UnbondingPeriodNotElapsedError(VaultError):
    def __init__(self, account: str, remaining_seconds: int) -> None:
        self.account = account
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Unbonding period for {account} has {remaining_seconds} seconds remaining"
        )


class NotEligibleError(VaultError):
    def __init__(self, account: str) -> None:
        self.account = account
        super().__init__(f"Account {account} is not eligible for this vault operation")


# ---------------------------------------------------------------------------
# TxError domain
# ---------------------------------------------------------------------------


class TxError(OGPUError):
    """Abstract: transaction-layer failure."""


class TxRevertError(TxError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Transaction reverted: {reason}")


class NonceError(TxError):
    def __init__(self, address: str, tried: int, suggested: int) -> None:
        self.address = address
        self.tried = tried
        self.suggested = suggested
        super().__init__(f"Nonce error for {address}: tried {tried}, suggested {suggested}")


class GasError(TxError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Gas error: {reason}")


class InvalidRpcUrlError(TxError):
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"RPC URL is not reachable: {url}")


# ---------------------------------------------------------------------------
# ConfigError domain
# ---------------------------------------------------------------------------


class ConfigError(OGPUError):
    """Abstract: SDK configuration is missing or invalid."""


class MissingSignerError(ConfigError):
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
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid signer: {reason}")


class ChainNotSupportedError(ConfigError):
    def __init__(self, chain_id: object) -> None:
        self.chain_id = chain_id
        super().__init__(f"Chain {chain_id!r} is not supported")


# ---------------------------------------------------------------------------
# IPFSError domain
# ---------------------------------------------------------------------------


class IPFSError(OGPUError):
    """Abstract: IPFS publish or fetch failure."""


class IPFSFetchError(IPFSError):
    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch from IPFS {url}: {reason}")


class IPFSGatewayError(IPFSError):
    def __init__(self, gateway: str, status_code: int) -> None:
        self.gateway = gateway
        self.status_code = status_code
        super().__init__(f"IPFS gateway {gateway} returned HTTP {status_code}")
