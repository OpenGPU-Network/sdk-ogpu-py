"""Provider synthetic class — composes Terminal + Vault + Nexus reads/writes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.errors import ProviderNotFoundError
from ..types.metadata import ProviderSnapshot, ResponseParams
from ..types.receipt import Receipt
from ._signer import Signer

if TYPE_CHECKING:
    pass


class Provider:
    """Synthetic instance wrapping provider-scoped operations across contracts."""

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Provider:
        instance = cls(address, chain)
        if not instance.is_provider():
            raise ProviderNotFoundError(address=address)
        return instance

    # ------------------------------------------------------------------ #
    # Terminal reads
    # ------------------------------------------------------------------ #

    def get_master(self) -> str:
        from . import terminal

        return terminal.get_master_of(self.address)

    def get_base_data(self) -> str:
        from . import terminal

        return terminal.get_base_data_of(self.address)

    def get_live_data(self) -> str:
        from . import terminal

        return terminal.get_live_data_of(self.address)

    def is_provider(self) -> bool:
        from . import terminal

        return terminal.is_provider(self.address)

    def get_default_agent_disabled(self) -> bool:
        from . import terminal

        return terminal.is_default_agent_disabled(self.address)

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

    def get_unbonding_timestamp(self) -> int:
        from . import vault

        return vault.get_unbonding_timestamp(self.address)

    def get_total_earnings(self) -> int:
        from . import vault

        return vault.get_total_earnings_of(self.address)

    def get_frozen_payment(self) -> int:
        from . import vault

        return vault.get_frozen_payment(self.address)

    def get_sanction(self) -> int:
        from . import vault

        return vault.get_sanction_of(self.address)

    def is_eligible(self) -> bool:
        from . import vault

        return vault.is_eligible(self.address)

    def is_whitelisted(self) -> bool:
        from . import vault

        return vault.is_whitelisted(self.address)

    # ------------------------------------------------------------------ #
    # Terminal writes (provider-role)
    # ------------------------------------------------------------------ #

    def announce_master(self, master: str, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.announce_master(master, signer=signer)

    def set_base_data(self, data: str, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.set_base_data(data, signer=signer)

    def set_live_data(self, data: str, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.set_live_data(data, signer=signer)

    def set_default_agent_disabled(self, value: bool, *, signer: Signer | None = None) -> Receipt:
        from . import terminal

        return terminal.set_default_agent_disabled(value, signer=signer)

    # ------------------------------------------------------------------ #
    # Nexus writes (provider-role)
    # ------------------------------------------------------------------ #

    def register_to(self, source: str, env: int, *, signer: Signer | None = None) -> Receipt:
        from . import nexus

        return nexus.register(source, self.address, env, signer=signer)

    def unregister_from(self, source: str, *, signer: Signer | None = None) -> Receipt:
        from . import nexus

        return nexus.unregister(source, self.address, signer=signer)

    def attempt(
        self, task: str, suggested_payment: int, *, signer: Signer | None = None
    ) -> Receipt:
        from . import nexus

        return nexus.attempt(task, self.address, suggested_payment, signer=signer)

    def submit_response(
        self, response_params: ResponseParams, *, signer: Signer | None = None
    ) -> Receipt:
        from . import nexus

        return nexus.submit_response(response_params, signer=signer)

    # ------------------------------------------------------------------ #
    # Vault convenience wrappers (per H2 — signer required, no fallback)
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

    def snapshot(self) -> ProviderSnapshot:
        return ProviderSnapshot(
            address=self.address,
            master=self.get_master(),
            base_data=self.get_base_data(),
            live_data=self.get_live_data(),
            is_provider=self.is_provider(),
            default_agent_disabled=self.get_default_agent_disabled(),
            balance=self.get_balance(),
            lockup=self.get_lockup(),
            unbonding=self.get_unbonding(),
            unbonding_timestamp=self.get_unbonding_timestamp(),
            total_earnings=self.get_total_earnings(),
            frozen_payment=self.get_frozen_payment(),
            sanction=self.get_sanction(),
            is_eligible=self.is_eligible(),
            is_whitelisted=self.is_whitelisted(),
        )

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Provider):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.address.lower())

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Provider {short} @{chain_label}>"
