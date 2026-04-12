"""Vault contract — low-level wrappers.

All write functions require an explicit ``signer`` keyword argument — there is
no env-var fallback for Vault operations (per decision C1-vault). This prevents
accidental deposit/withdraw from the wrong account.
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
    """Call ``Vault.deposit(account)`` with ``msg.value = amount``.

    The ``account`` parameter is the beneficiary address being credited.
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
    """Call ``Vault.withdraw(amount)``."""
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "withdraw", (amount,), signer=local, context="Vault.withdraw"
    ).execute()


def lock(amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.lock(amount)``."""
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(contract, "lock", (amount,), signer=local, context="Vault.lock").execute()


def unbond(amount: int, *, signer: Signer) -> Receipt:
    """Call ``Vault.unbond(amount)``."""
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(contract, "unbond", (amount,), signer=local, context="Vault.unbond").execute()


def cancel_unbonding(*, signer: Signer) -> Receipt:
    """Call ``Vault.cancelUnbonding()``."""
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(
        contract, "cancelUnbonding", (), signer=local, context="Vault.cancelUnbonding"
    ).execute()


def claim(*, signer: Signer) -> Receipt:
    """Call ``Vault.claim()``."""
    local = resolve_signer(signer, role=None)
    contract = load_contract("VaultAbi")
    return TxExecutor(contract, "claim", (), signer=local, context="Vault.claim").execute()


# ---------------------------------------------------------------------------
# Read functions
# ---------------------------------------------------------------------------


def _vault() -> Any:
    return load_contract("VaultAbi")


def get_balance_of(address: str) -> int:
    return int(_vault().functions.balanceOf(address).call())


def get_lockup_of(address: str) -> int:
    return int(_vault().functions.lockupOf(address).call())


def get_unbonding_of(address: str) -> int:
    return int(_vault().functions.unbondingOf(address).call())


def get_unbonding_timestamp(address: str) -> int:
    return int(_vault().functions.unbondingTimestamp(address).call())


def get_total_earnings_of(address: str) -> int:
    return int(_vault().functions.totalEarningsOf(address).call())


def get_frozen_payment(address: str) -> int:
    return int(_vault().functions.frozenPayment(address).call())


def get_sanction_of(address: str) -> int:
    return int(_vault().functions.sanctionOf(address).call())


def is_eligible(address: str) -> bool:
    return bool(_vault().functions.isEligible(address).call())


def is_whitelisted(address: str) -> bool:
    return bool(_vault().functions.isWhitelisted(address).call())


# ---------------------------------------------------------------------------
# Constants (view)
# ---------------------------------------------------------------------------


def get_min_lockup_per_source() -> int:
    return int(_vault().functions.MIN_LOCKUP_PER_SOURCE().call())


def get_unbonding_period() -> int:
    return int(_vault().functions.UNBONDING_PERIOD().call())
