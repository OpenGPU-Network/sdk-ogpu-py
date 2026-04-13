"""Master synthetic class — composes Terminal + Vault reads/writes."""

from __future__ import annotations

from ..types.errors import MasterNotFoundError
from ..types.metadata import MasterSnapshot
from ..types.receipt import Receipt
from ._signer import Signer


class Master:
    """Synthetic instance class wrapping master-scoped operations.

    Like ``Provider``, the Master class is NOT backed by a single
    contract ABI — ``Master(address)`` composes calls across Terminal
    and Vault into a cleaner per-master API surface. Lighter than
    ``Provider`` because masters have a smaller operational surface:

    - **Terminal** — pairing with a provider, setting agents, removing
      providers/containers
    - **Vault** — balance, lockup, earnings, eligibility

    Masters do not touch Nexus directly — provider-side operations
    (register, attempt, submit_response) are provider-role calls,
    though masters can authorize an agent to drive them via
    ``set_agent`` + ``ogpu.agent``.

    Lazy by default; use ``Master.load(address)`` for eager existence
    checking (``Terminal.isMaster`` must return True).

    Example:
        ```python
        from ogpu.protocol import Master

        m = Master.load("0xMASTER")
        print(m.get_provider())        # paired provider
        print(m.get_lockup())          # master's staked amount

        # Master authorizes an agent to act on their behalf
        m.set_agent("0xTHE_ORDER", True, signer=MASTER_KEY)
        ```

    Attributes:
        address: Checksummed master address.
        chain: Optional chain binding.
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        """Construct a lazy Master instance (no RPC).

        Args:
            address: Master address.
            chain: Optional chain binding.
        """
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Master:
        """Eager constructor — validate that the address is a registered master.

        Runs ``Terminal.isMaster(address)`` and raises
        ``MasterNotFoundError`` if it returns False.

        Args:
            address: Master address.
            chain: Optional chain binding.

        Returns:
            A ``Master`` instance.

        Raises:
            MasterNotFoundError: If the address is not a registered master.
        """
        instance = cls(address, chain)
        if not instance.is_master():
            raise MasterNotFoundError(address=address)
        return instance

    # ------------------------------------------------------------------ #
    # Terminal reads
    # ------------------------------------------------------------------ #

    def get_provider(self) -> str:
        """Return the provider this master is paired with.

        Delegates to ``Terminal.providerOf(self.address)``. Returns
        the zero address if unpaired.
        """
        from . import terminal

        return terminal.get_provider_of(self.address)

    def is_master(self) -> bool:
        """Return whether this address is registered as a master.

        Delegates to ``Terminal.isMaster(self.address)``.
        """
        from . import terminal

        return terminal.is_master(self.address)

    # ------------------------------------------------------------------ #
    # Vault reads
    # ------------------------------------------------------------------ #

    def get_balance(self) -> int:
        """Return available vault balance in wei."""
        from . import vault

        return vault.get_balance_of(self.address)

    def get_lockup(self) -> int:
        """Return locked (staked) amount in wei."""
        from . import vault

        return vault.get_lockup_of(self.address)

    def get_unbonding(self) -> int:
        """Return amount currently unbonding in wei."""
        from . import vault

        return vault.get_unbonding_of(self.address)

    def get_total_earnings(self) -> int:
        """Return cumulative earnings in wei."""
        from . import vault

        return vault.get_total_earnings_of(self.address)

    def get_frozen_payment(self) -> int:
        """Return the amount escrowed against pending task work in wei."""
        from . import vault

        return vault.get_frozen_payment(self.address)

    def is_eligible(self) -> bool:
        """Return whether the master is eligible for vault operations."""
        from . import vault

        return vault.is_eligible(self.address)

    def is_whitelisted(self) -> bool:
        """Return whether the master is on the vault whitelist."""
        from . import vault

        return vault.is_whitelisted(self.address)

    # ------------------------------------------------------------------ #
    # Terminal writes (master-role)
    # ------------------------------------------------------------------ #

    def announce_provider(
        self, provider: str, amount: int, *, signer: Signer | None = None
    ) -> Receipt:
        """Claim a provider by calling ``Terminal.announceProvider`` (payable).

        First half of master/provider pairing. Sends ``amount`` as
        ``msg.value`` — gets credited to the provider's vault lockup.
        The pairing is completed when the provider subsequently calls
        ``announceMaster``.

        Args:
            provider: Provider address being claimed.
            amount: Initial funding amount in wei.
            signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.announce_provider(provider, amount, signer=signer)

    def remove_provider(self, provider: str, *, signer: Signer | None = None) -> Receipt:
        """Break the pairing with a provider by calling ``Terminal.removeProvider``.

        Args:
            provider: Provider address to remove.
            signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.remove_provider(provider, signer=signer)

    def remove_container(
        self, provider: str, source: str, *, signer: Signer | None = None
    ) -> Receipt:
        """Signal a provider should stop running a source's container.

        Delegates to ``Terminal.removeContainer``. Doesn't actually
        stop the docker container — emits an event the Provider App
        watches and acts on.

        Args:
            provider: Provider whose container should stop.
            source: Source whose container should stop.
            signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.
        """
        from . import terminal

        return terminal.remove_container(provider, source, signer=signer)

    def set_agent(self, agent: str, value: bool, *, signer: Signer | None = None) -> Receipt:
        """Authorize (or revoke) an agent to sign on this master's behalf.

        Delegates to ``Terminal.setAgent(agent, value)``. After
        ``value=True``, the agent's key can sign Nexus operations
        (register, attempt, etc.) for providers managed by this master.

        Args:
            agent: Agent address.
            value: True to authorize, False to revoke.
            signer: Master signer. Falls back to ``CLIENT_PRIVATE_KEY``
                via the protocol-level ``set_agent`` — pass
                ``signer=MASTER_KEY`` explicitly to sign as a master.
        """
        from . import terminal

        return terminal.set_agent(agent, value, signer=signer)

    # ------------------------------------------------------------------ #
    # Vault convenience wrappers (signer required, no fallback)
    # ------------------------------------------------------------------ #

    def stake(self, amount: int, *, signer: Signer) -> Receipt:
        """Lock ``amount`` into this master's vault lockup.

        Convenience wrapper for ``vault.lock``. ``signer`` must be
        explicit — vault operations do not fall back to env vars.
        """
        from . import vault

        return vault.lock(amount, signer=signer)

    def unstake(self, amount: int, *, signer: Signer) -> Receipt:
        """Start unbonding ``amount`` from this master's lockup.

        Convenience wrapper for ``vault.unbond``.
        """
        from . import vault

        return vault.unbond(amount, signer=signer)

    def cancel_unbonding(self, *, signer: Signer) -> Receipt:
        """Abort any pending unbonding for this master.

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
        """Deposit ``amount`` into this master's vault balance.

        Convenience wrapper for ``vault.deposit(self.address, amount)``.
        """
        from . import vault

        return vault.deposit(self.address, amount, signer=signer)

    def withdraw_from_vault(self, amount: int, *, signer: Signer) -> Receipt:
        """Withdraw ``amount`` from this master's liquid vault balance.

        Convenience wrapper for ``vault.withdraw``. ``signer`` must
        hold the keys for ``self.address``.
        """
        from . import vault

        return vault.withdraw(amount, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> MasterSnapshot:
        """Return a frozen capture of Terminal + Vault state in one batch.

        Returns:
            ``MasterSnapshot`` with address, paired provider, master
            status, and all vault balance fields.
        """
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
        """Case-insensitive address equality."""
        if isinstance(other, Master):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on the lowercase address."""
        return hash(self.address.lower())

    def __str__(self) -> str:
        """Return the address — f-string and log friendly."""
        return self.address

    def __repr__(self) -> str:
        """Return a debugger-friendly ``<Master 0x... @chain>`` label."""
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Master {short} @{chain_label}>"
