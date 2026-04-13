"""Vault contract — low-level wrappers.

The Vault contract holds all staked tokens: provider lockups that back
source registration, client deposits that escrow task payment, and
master funds that back their managed providers. Every role in the
protocol eventually interacts with the vault to deposit, lock, unbond,
or claim.

All write functions require ``signer=`` as an explicit keyword argument.
There is **no env-var fallback** — this is intentional (per decision
C1-vault in the PRD). Vault operations are role-agnostic (any account
can hold a balance), and falling back to a role-specific env var
invites accidents when multiple roles share a process. Always pass
``signer=`` explicitly.
"""

from __future__ import annotations

from typing import Any

from ..types.receipt import Receipt
from ._base import TxExecutor, _get_web3, load_contract
from ._signer import Signer, resolve_signer

# ---------------------------------------------------------------------------
# Write functions (signer REQUIRED — no role fallback)
# ---------------------------------------------------------------------------


def deposit(account: str, amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.deposit(account)`` to credit ``amount`` to ``account``.

    The Solidity function is payable — ``account`` is the beneficiary
    address being credited, ``amount`` is sent as ``msg.value``. The
    signer pays gas and funds the deposit from their own balance;
    ``account`` receives the credit.

    Typically ``signer`` and ``account`` are the same (you deposit for
    yourself) but they don't have to be — a master can deposit on
    behalf of a managed provider, and ``Provider.deposit_to_vault``
    uses this pattern to pre-fill ``account=self.address``.

    Args:
        account: The address being credited (beneficiary).
        amount: Amount to deposit in wei. Must match what the signer
            is willing to send as ``msg.value``.
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the deposit.

    Raises:
        MissingSignerError: If no signer is passed (vault calls do not
            fall back to env vars).

    Example:
        ```python
        from web3 import Web3
        from ogpu.protocol import vault
        vault.deposit(
            "0xBENEFICIARY",
            amount=Web3.to_wei(1, "ether"),
            signer=MY_KEY,
        )
        ```
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    addr = _get_web3().to_checksum_address(account)
    return TxExecutor(
        contract,
        "deposit",
        (addr,),
        signer=local,
        value=amount,
        context=f"Vault.deposit({addr})",
    ).execute()


def withdraw(amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.withdraw(amount)`` to pull funds out of the signer's balance.

    Only works on the unlocked portion of the signer's vault balance —
    locked or unbonding funds cannot be withdrawn until they return
    to the liquid balance via ``claim``.

    Args:
        amount: Amount to withdraw in wei.
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the withdraw.

    Raises:
        InsufficientBalanceError: If the signer's unlocked balance is
            less than ``amount``.
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "withdraw", (amount,), signer=local, context="Vault.withdraw"
    ).execute()


def lock(amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.lock(amount)`` to stake ``amount`` from the liquid balance.

    Moves funds from the signer's liquid (available) balance into the
    locked (staked) portion. Locked tokens are what make a provider
    eligible to register to sources — ``Vault.minLockupPerSource`` is
    checked on every ``Nexus.register`` call.

    Args:
        amount: Amount to lock in wei.
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the lock.

    Raises:
        InsufficientBalanceError: If the signer's liquid balance is
            less than ``amount``.
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "lock", (amount,), signer=local, context="Vault.lock"
    ).execute()


def unbond(amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.unbond(amount)`` to start unbonding ``amount`` of locked funds.

    Begins the unbonding cooldown. Tokens move from the locked balance
    into the unbonding bucket and stay there for ``Vault.UNBONDING_PERIOD``
    seconds. After the period elapses, ``claim`` moves them to the
    liquid balance where they can be withdrawn.

    Args:
        amount: Amount to begin unbonding, in wei.
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the unbond.

    Raises:
        InsufficientLockupError: If the signer's locked balance is less
            than ``amount``.
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "unbond", (amount,), signer=local, context="Vault.unbond"
    ).execute()


def cancel_unbonding(*, signer: Signer) -> Receipt:
    """Call ``Vault.cancelUnbonding()`` to abort a pending unbonding.

    Moves any in-flight unbonding amount back to the locked balance.
    Useful when you change your mind before the cooldown elapses.

    Args:
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the cancellation.
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "cancelUnbonding", (), signer=local, context="Vault.cancelUnbonding"
    ).execute()


def claim(*, signer: Signer) -> Receipt:
    """Call ``Vault.claim()`` to move matured unbonding back to the liquid balance.

    Only works after the unbonding period has fully elapsed (check
    ``get_unbonding_timestamp`` vs. current time). After a successful
    claim, the matured amount is available for ``withdraw``.

    Args:
        signer: Required. Hex key or ``LocalAccount``.

    Returns:
        ``Receipt`` for the claim.

    Raises:
        UnbondingPeriodNotElapsedError: If the cooldown hasn't finished.
    """
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "claim", (), signer=local, context="Vault.claim"
    ).execute()


# ---------------------------------------------------------------------------
# Read functions
# ---------------------------------------------------------------------------


def _vault() -> Any:
    """Return the Vault contract instance (singleton for the current chain)."""
    return load_contract("VaultAbi")


def get_balance_of(address: str) -> int:
    """Return the available (liquid) balance for an address, in wei.

    The portion of the vault deposit that isn't locked, unbonding, or
    escrowed in a frozen payment. This is what can be withdrawn.

    Args:
        address: Account to query.

    Returns:
        Available balance in wei.
    """
    return int(_vault().functions.balanceOf(address).call())


def get_lockup_of(address: str) -> int:
    """Return the locked (staked) amount for an address, in wei.

    The portion backing source registrations. Can be moved to unbonding
    via ``unbond``.

    Args:
        address: Account to query.

    Returns:
        Locked amount in wei.
    """
    return int(_vault().functions.lockupOf(address).call())


def get_unbonding_of(address: str) -> int:
    """Return the amount currently unbonding for an address, in wei.

    Tokens in the cooldown window between ``unbond`` and ``claim``.
    Zero once ``claim`` has been called for all matured unbondings.

    Args:
        address: Account to query.

    Returns:
        Unbonding amount in wei.
    """
    return int(_vault().functions.unbondingOf(address).call())


def get_unbonding_timestamp(address: str) -> int:
    """Return the unix timestamp when the current unbonding matures.

    After this time, ``claim`` will succeed. Zero if no unbonding is
    in progress.

    Args:
        address: Account to query.

    Returns:
        Unix timestamp.
    """
    return int(_vault().functions.unbondingTimestamp(address).call())


def get_total_earnings_of(address: str) -> int:
    """Return cumulative earnings for an address, in wei.

    Monotonically-increasing counter of everything earned through
    completed tasks, regardless of whether it's still in the vault.

    Args:
        address: Account to query.

    Returns:
        Cumulative earnings in wei.
    """
    return int(_vault().functions.totalEarningsOf(address).call())


def get_frozen_payment(address: str) -> int:
    """Return the amount escrowed against pending task work, in wei.

    Funds earmarked for pending attempts that haven't been confirmed
    or refunded yet. Not available for withdraw.

    Args:
        address: Account to query.

    Returns:
        Frozen payment in wei.
    """
    return int(_vault().functions.frozenPayment(address).call())


def get_sanction_of(address: str) -> int:
    """Return the sanction amount for an address, in wei.

    Protocol-level sanctions applied for misbehavior. Usually zero;
    non-zero values indicate the account has been penalized.

    Args:
        address: Account to query.

    Returns:
        Sanction amount in wei.
    """
    return int(_vault().functions.sanctionOf(address).call())


def is_eligible(address: str) -> bool:
    """Return whether an account is eligible for vault operations.

    Accounts that fail this check cannot participate in protocol flows
    (registration, attempts, etc.). Usually a combination of lockup
    thresholds, whitelist status, and sanction state.

    Args:
        address: Account to check.

    Returns:
        True if eligible.
    """
    return bool(_vault().functions.isEligible(address).call())


def is_whitelisted(address: str) -> bool:
    """Return whether an account is on the vault whitelist.

    Used for protocol-level access control — whitelisted accounts may
    get preferential eligibility or sanction handling.

    Args:
        address: Account to check.

    Returns:
        True if whitelisted.
    """
    return bool(_vault().functions.isWhitelisted(address).call())


# ---------------------------------------------------------------------------
# Constants (view)
# ---------------------------------------------------------------------------


def get_min_lockup_per_source() -> int:
    """Return ``Vault.MIN_LOCKUP_PER_SOURCE`` in wei.

    The minimum lockup a provider must hold in the vault to register
    to any source. Sources can enforce a higher minimum via their own
    ``minAvailableLockup`` field, but this is the protocol-wide floor.

    Returns:
        Minimum lockup amount in wei.
    """
    return int(_vault().functions.MIN_LOCKUP_PER_SOURCE().call())


def get_unbonding_period() -> int:
    """Return ``Vault.UNBONDING_PERIOD`` in seconds.

    The cooldown window between ``unbond`` and ``claim``. After
    calling ``unbond``, you must wait at least this many seconds
    before you can ``claim``.

    Returns:
        Unbonding period in seconds.
    """
    return int(_vault().functions.UNBONDING_PERIOD().call())
