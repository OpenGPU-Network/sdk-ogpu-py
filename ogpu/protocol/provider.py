"""Provider synthetic class — composes Terminal + Vault + Nexus reads/writes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.errors import ProviderNotFoundError
from ..types.metadata import ProviderSnapshot, ResponseParams
from ..types.receipt import Receipt
from ._signer import Signer

if TYPE_CHECKING:
    from .source import Source


class Provider:
    """Synthetic instance class wrapping provider-scoped operations.

    Unlike ``Source`` / ``Task`` / ``Response``, the Provider class is
    NOT backed by a single contract ABI — there is no "Provider" contract
    on-chain. Instead, ``Provider(address)`` is a convenience wrapper
    that composes calls across three contracts:

    - **Terminal** — identity, pairing, base/live data
    - **Vault** — balance, lockup, unbonding, earnings, eligibility
    - **Nexus** — source registrations, attempts, submissions

    Every method delegates to a module-level protocol function, filling
    in ``self.address`` as the provider argument where appropriate.
    This gives you a cleaner API surface when your code holds a
    "provider" concept (dashboards, provisioning scripts, scheduler
    code) without needing to pass the address around repeatedly.

    Lazy by default — ``Provider(address)`` does no RPC. Use
    ``Provider.load(address)`` if you want an eager existence check
    (``Terminal.isProvider`` must return True).

    Example:
        ```python
        from ogpu.protocol import Provider

        p = Provider.load("0xPROVIDER")
        print(p.get_master())           # from Terminal
        print(p.get_lockup())           # from Vault
        print(p.is_eligible())          # from Vault
        for source in p.get_registered_sources():  # from Nexus
            print(source.address)

        snap = p.snapshot()             # batch capture across all three contracts
        ```

    Attributes:
        address: Checksummed provider address.
        chain: Optional chain binding.
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        """Construct a lazy Provider instance (no RPC).

        Args:
            address: Provider address. Checksummed automatically.
            chain: Optional chain binding.
        """
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Provider:
        """Eager constructor — validate that the address is a registered provider.

        Runs ``Terminal.isProvider(address)`` and raises
        ``ProviderNotFoundError`` if it returns False.

        Args:
            address: Provider address.
            chain: Optional chain binding.

        Returns:
            A ``Provider`` instance.

        Raises:
            ProviderNotFoundError: If the address is not a registered provider.
        """
        instance = cls(address, chain)
        if not instance.is_provider():
            raise ProviderNotFoundError(address=address)
        return instance

    # ------------------------------------------------------------------ #
    # Terminal reads
    # ------------------------------------------------------------------ #

    def get_master(self) -> str:
        """Return the master this provider is paired with.

        Delegates to ``Terminal.masterOf(self.address)``. Returns the
        zero address if the provider isn't paired.
        """
        from . import terminal

        return terminal.get_master_of(self.address)

    def get_base_data(self) -> str:
        """Return the long-lived metadata URL for this provider.

        Delegates to ``Terminal.baseDataOf(self.address)``. Typically
        an IPFS URL pointing at a JSON document describing the
        provider's hardware and capabilities.
        """
        from . import terminal

        return terminal.get_base_data_of(self.address)

    def get_live_data(self) -> str:
        """Return the short-lived status URL for this provider.

        Delegates to ``Terminal.liveDataOf(self.address)``. Typically
        refreshed more frequently than base data — current load,
        health, etc.
        """
        from . import terminal

        return terminal.get_live_data_of(self.address)

    def is_provider(self) -> bool:
        """Return whether this address is registered as a provider.

        Delegates to ``Terminal.isProvider(self.address)``.
        """
        from . import terminal

        return terminal.is_provider(self.address)

    def get_default_agent_disabled(self) -> bool:
        """Return whether the provider opted out of default agent delegation.

        Delegates to ``Terminal.defaultAgentDisabled(self.address)``.
        When True, the built-in scheduling agent (The Order) no
        longer dispatches tasks to this provider automatically.
        """
        from . import terminal

        return terminal.is_default_agent_disabled(self.address)

    # ------------------------------------------------------------------ #
    # Vault reads
    # ------------------------------------------------------------------ #

    def get_balance(self) -> int:
        """Return available (liquid) vault balance in wei.

        Delegates to ``Vault.balanceOf(self.address)``.
        """
        from . import vault

        return vault.get_balance_of(self.address)

    def get_lockup(self) -> int:
        """Return locked (staked) amount in wei.

        Delegates to ``Vault.lockupOf(self.address)``. This is what
        backs source registrations.
        """
        from . import vault

        return vault.get_lockup_of(self.address)

    def get_unbonding(self) -> int:
        """Return amount currently unbonding in wei.

        Delegates to ``Vault.unbondingOf(self.address)``. Zero unless
        the provider has called ``unbond`` and hasn't yet ``claim``'d.
        """
        from . import vault

        return vault.get_unbonding_of(self.address)

    def get_unbonding_timestamp(self) -> int:
        """Return the Unix timestamp when the current unbonding matures.

        Delegates to ``Vault.unbondingTimestamp(self.address)``.
        """
        from . import vault

        return vault.get_unbonding_timestamp(self.address)

    def get_total_earnings(self) -> int:
        """Return cumulative earnings in wei.

        Delegates to ``Vault.totalEarningsOf(self.address)``.
        """
        from . import vault

        return vault.get_total_earnings_of(self.address)

    def get_frozen_payment(self) -> int:
        """Return the amount escrowed against pending attempts in wei.

        Delegates to ``Vault.frozenPayment(self.address)``.
        """
        from . import vault

        return vault.get_frozen_payment(self.address)

    def get_sanction(self) -> int:
        """Return protocol sanction amount in wei.

        Delegates to ``Vault.sanctionOf(self.address)``. Usually zero.
        """
        from . import vault

        return vault.get_sanction_of(self.address)

    def is_eligible(self) -> bool:
        """Return whether the provider is eligible for vault operations.

        Delegates to ``Vault.isEligible(self.address)``.
        """
        from . import vault

        return vault.is_eligible(self.address)

    def is_whitelisted(self) -> bool:
        """Return whether the provider is on the vault whitelist.

        Delegates to ``Vault.isWhitelisted(self.address)``.
        """
        from . import vault

        return vault.is_whitelisted(self.address)

    # ------------------------------------------------------------------ #
    # Terminal writes (provider-role)
    # ------------------------------------------------------------------ #

    def announce_master(self, master: str, *, signer: Signer | None = None) -> Receipt:
        """Pair this provider with a master by calling ``Terminal.announceMaster``.

        Must be called by the provider's own key.

        Args:
            master: Master address to pair with.
            signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the call.
        """
        from . import terminal

        return terminal.announce_master(master, signer=signer)

    def set_base_data(self, data: str, *, signer: Signer | None = None) -> Receipt:
        """Update this provider's long-lived metadata URL.

        Delegates to ``Terminal.setBaseData``. Must be called by the
        provider's own key — agents cannot set base data on behalf of
        a provider (the contract uses ``msg.sender`` to identify the
        provider).

        Args:
            data: New base data URL.
            signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.set_base_data(data, signer=signer)

    def set_live_data(self, data: str, *, signer: Signer | None = None) -> Receipt:
        """Update this provider's short-lived status URL.

        Delegates to ``Terminal.setLiveData``. Must be called by the
        provider's own key.

        Args:
            data: New live data URL.
            signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.set_live_data(data, signer=signer)

    def set_default_agent_disabled(self, value: bool, *, signer: Signer | None = None) -> Receipt:
        """Opt this provider out of (or back into) default agent delegation.

        Delegates to ``Terminal.setDefaultAgentDisabled``. Must be
        called by the provider's own key.

        Args:
            value: True to disable, False to enable.
            signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.set_default_agent_disabled(value, signer=signer)

    # ------------------------------------------------------------------ #
    # Nexus writes (provider-role)
    # ------------------------------------------------------------------ #

    def register_to(self, source: str, env: int, *, signer: Signer | None = None) -> Receipt:
        """Register this provider to a source.

        Delegates to ``Nexus.register(source, self.address, env)``.
        Can be called by the provider directly, the master, or an
        authorized agent.

        Args:
            source: Source contract address to register to.
            env: Preferred environment bitmask (``Environment.CPU`` etc.).
            signer: Provider/master/agent signer. Falls back to
                ``PROVIDER_PRIVATE_KEY``.
        """
        from . import nexus

        return nexus.register(source, self.address, env, signer=signer)

    def unregister_from(self, source: str, *, signer: Signer | None = None) -> Receipt:
        """Unregister this provider from a source.

        Delegates to ``Nexus.unregister(source, self.address)``.

        Args:
            source: Source contract address.
            signer: Provider/master/agent signer.
        """
        from . import nexus

        return nexus.unregister(source, self.address, signer=signer)

    def attempt(self, task: str, suggested_payment: int, *, signer: Signer | None = None) -> Receipt:
        """Submit an attempt on a task for this provider.

        Delegates to ``Nexus.attempt(task, self.address, suggested_payment)``.

        Args:
            task: Task contract address.
            suggested_payment: Advisory payment amount in wei.
            signer: Provider/master/agent signer.
        """
        from . import nexus

        return nexus.attempt(task, self.address, suggested_payment, signer=signer)

    def submit_response(
        self, response_params: ResponseParams, *, signer: Signer | None = None
    ) -> Receipt:
        """Submit a response on behalf of this provider.

        Delegates to ``Nexus.submitResponse``. The ``response_params``
        should already carry ``provider=self.address``.

        Args:
            response_params: The pre-built response parameters.
            signer: Provider signer.
        """
        from . import nexus

        return nexus.submit_response(response_params, signer=signer)

    # ------------------------------------------------------------------ #
    # Vault convenience wrappers (per decision H2 — signer required, no fallback)
    # ------------------------------------------------------------------ #

    def stake(self, amount: int, *, signer: Signer) -> Receipt:
        """Lock ``amount`` into this provider's vault lockup.

        Convenience wrapper for ``vault.lock``. ``signer`` must be
        explicit — vault operations do not fall back to env vars.

        Args:
            amount: Amount to lock in wei.
            signer: Required hex key or ``LocalAccount``.
        """
        from . import vault

        return vault.lock(amount, signer=signer)

    def unstake(self, amount: int, *, signer: Signer) -> Receipt:
        """Start unbonding ``amount`` from this provider's lockup.

        Convenience wrapper for ``vault.unbond``.
        """
        from . import vault

        return vault.unbond(amount, signer=signer)

    def cancel_unbonding(self, *, signer: Signer) -> Receipt:
        """Abort any pending unbonding for this provider.

        Convenience wrapper for ``vault.cancel_unbonding``.
        """
        from . import vault

        return vault.cancel_unbonding(signer=signer)

    def claim_earnings(self, *, signer: Signer) -> Receipt:
        """Claim matured unbonded amounts into the liquid balance.

        Convenience wrapper for ``vault.claim``.
        """
        from . import vault

        return vault.claim(signer=signer)

    def deposit_to_vault(self, amount: int, *, signer: Signer) -> Receipt:
        """Deposit ``amount`` into this provider's vault balance.

        Convenience wrapper for ``vault.deposit(self.address, amount)``.
        The signer can be the provider themselves or anyone funding
        the provider (e.g. the master).
        """
        from . import vault

        return vault.deposit(self.address, amount, signer=signer)

    def withdraw_from_vault(self, amount: int, *, signer: Signer) -> Receipt:
        """Withdraw ``amount`` from this provider's liquid vault balance.

        Convenience wrapper for ``vault.withdraw``. ``signer`` must
        hold the keys for ``self.address`` — vault withdraw uses
        ``msg.sender``.
        """
        from . import vault

        return vault.withdraw(amount, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> ProviderSnapshot:
        """Return a frozen capture of Terminal + Vault state in one batch.

        Issues one RPC per field (sequential) and bundles the results
        into a ``ProviderSnapshot``. Omits paginated Nexus fields
        (``get_registered_sources``) — call those explicitly.

        Returns:
            ``ProviderSnapshot`` with every terminal and vault field.
        """
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
        """Case-insensitive address equality."""
        if isinstance(other, Provider):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on the lowercase address."""
        return hash(self.address.lower())

    def __str__(self) -> str:
        """Return the address — f-string and log friendly."""
        return self.address

    def __repr__(self) -> str:
        """Return a debugger-friendly ``<Provider 0x... @chain>`` label."""
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Provider {short} @{chain_label}>"
