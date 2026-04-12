"""Master synthetic class — composes Terminal + Vault reads/writes."""

from __future__ import annotations

from ..types.errors import MasterNotFoundError
from ..types.metadata import MasterSnapshot
from ..types.receipt import Receipt
from ._signer import Signer


class Master:
    """Synthetic instance wrapping master-scoped operations across contracts."""

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Master:
        instance = cls(address, chain)
        if not instance.is_master():
            raise MasterNotFoundError(address=address)
        return instance

    # ------------------------------------------------------------------ #
    # Terminal reads
    # ------------------------------------------------------------------ #

    def get_provider(self) -> str:
        from . import terminal

        return terminal.get_provider_of(self.address)

    def is_master(self) -> bool:
        from . import terminal

        return terminal.is_master(self.address)

    # ------------------------------------------------------------------ #
    # Vault reads
    # ------------------------------------------------------------------ #

    def get_balance(self) -> int:
        from . import vault

        return vault.get_balance_of(self.address)

    def get_lockup(self) -> int:
        from . import vault

        return vault.get_lockup_of(self.address)

    def get_unbonding(self) -> int:
        from . import vault

        return vault.get_unbonding_of(self.address)

    def get_total_earnings(self) -> int:
        from . import vault

        return vault.get_total_earnings_of(self.address)

    def get_frozen_payment(self) -> int:
        from . import vault

        return vault.get_frozen_payment(self.address)

    def is_eligible(self) -> bool:
        from . import vault

        return vault.is_eligible(self.address)

    def is_whitelisted(self) -> bool:
        from . import vault

        return vault.is_whitelisted(self.address)

    # ------------------------------------------------------------------ #
    # Terminal writes (master-role)
    # ------------------------------------------------------------------ #

    def announce_provider(
        self, provider: str, amount: int, *, signer: Signer | None = None
    ) -> Receipt:
        from . import terminal

        return terminal.announce_provider(provider, amount, signer=signer)

    def remove_provider(self, provider: str, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.remove_provider(provider, signer=signer)

    def remove_container(
        self, provider: str, source: str, *, signer: Signer | None = None
    ) -> Receipt:
        from . import terminal

        return terminal.remove_container(provider, source, signer=signer)

    def set_agent(self, agent: str, value: bool, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.set_agent(agent, value, signer=signer)

    # ------------------------------------------------------------------ #
    # Vault convenience wrappers (signer required, no fallback)
    # ------------------------------------------------------------------ #

    def stake(self, amount: int, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.lock(amount, signer=signer)

    def unstake(self, amount: int, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.unbond(amount, signer=signer)

    def cancel_unbonding(self, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.cancel_unbonding(signer=signer)

    def claim_earnings(self, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.claim(signer=signer)

    def deposit_to_vault(self, amount: int, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.deposit(self.address, amount, signer=signer)

    def withdraw_from_vault(self, amount: int, *, signer: Signer) -> Receipt:
        from . import vault

        return vault.withdraw(amount, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> MasterSnapshot:
        return MasterSnapshot(
            address=self.address,
            provider=self.get_provider(),
            is_master=self.is_master(),
            balance=self.get_balance(),
            lockup=self.get_lockup(),
            unbonding=self.get_unbonding(),
            total_earnings=self.get_total_earnings(),
            frozen_payment=self.get_frozen_payment(),
            is_eligible=self.is_eligible(),
            is_whitelisted=self.is_whitelisted(),
        )

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Master):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.address.lower())

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Master {short} @{chain_label}>"
