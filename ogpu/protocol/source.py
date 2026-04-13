"""Source instance class — bound to a deployed Source contract address."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..ipfs import fetch_ipfs_json
from ..types.enums import Environment, Role, SourceStatus
from ..types.errors import SourceNotFoundError
from ..types.metadata import SourceParams, SourceSnapshot
from ..types.receipt import Receipt
from ._base import _DEFAULT_CHUNK_SIZE, _paginated_call, load_contract
from ._signer import Signer, resolve_signer

if TYPE_CHECKING:
    from .task import Task


class Source:
    """Live, stateless proxy to an on-chain Source contract.

    Holds only ``self.address`` and ``self.chain`` — no cached state.
    Every method is a fresh RPC call. This makes method semantics
    predictable (you always read current chain state) and instance
    construction cheap (no RPC at ``__init__``).

    Two construction modes:

    - ``Source(address)`` — lazy. No RPC. Use when you trust the
      address and want to defer validation until the first read.
    - ``Source.load(address)`` — eager. Runs a cheap ``get_status()``
      probe and raises ``SourceNotFoundError`` if the address isn't
      a valid source contract.

    Equality is address-based and case-insensitive. Hashing matches
    equality, so ``Source`` instances can be used as dict keys or in
    sets.

    Example:
        ```python
        from ogpu.protocol import Source

        source = Source.load("0xSOURCE")
        print(source.get_status())
        # <SourceStatus.ACTIVE: 0>

        print(source.get_client())
        # '0xOWNER...'

        for task in source.get_tasks():
            print(task.address, task.get_status())
        ```

    Attributes:
        address: Checksummed contract address.
        chain: Optional chain binding (defaults to None — most code
            uses the globally-active chain from ``ChainConfig``).
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        """Construct a lazy Source instance (no RPC).

        Args:
            address: Source contract address. Checksummed automatically.
            chain: Optional chain binding for future multi-chain support.
        """
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Source:
        """Eager constructor — validate that the address is a Source contract.

        Runs a cheap ``get_status()`` probe. If the probe reverts, the
        address is either not a contract or not a Source, and
        ``SourceNotFoundError`` is raised immediately.

        Args:
            address: Source contract address.
            chain: Optional chain binding.

        Returns:
            A ``Source`` instance bound to the given address.

        Raises:
            SourceNotFoundError: If the probe call fails.
        """
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise SourceNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        """Return a web3 Contract wrapper for this source address."""
        return load_contract("SourceAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_client(self) -> str:
        """Return the address that owns (published) this source.

        Only this address can call ``set_status``, ``set_params``, or
        ``inactivate``.

        Returns:
            Owner's checksummed address.
        """
        return str(self._contract().functions.getClient().call())

    def get_status(self) -> SourceStatus:
        """Return the current lifecycle status of the source.

        Returns:
            ``SourceStatus.ACTIVE`` or ``SourceStatus.INACTIVE``.
        """
        return SourceStatus(self._contract().functions.getStatus().call())

    def get_params(self) -> SourceParams:
        """Fetch the full on-chain ``SourceParams`` tuple.

        Returns the raw parameters stored on the contract — name,
        description, environment bitmask, min payment, etc. — without
        touching IPFS. For the human-readable metadata (including
        logoUrl and description), call ``get_metadata()``.

        Returns:
            ``SourceParams`` dataclass with every field from the
            contract.
        """
        raw = self._contract().functions.getSourceParams().call()
        return SourceParams(
            client=raw[0],
            imageMetadataUrl=raw[1],
            imageEnvironments=raw[2],
            minPayment=raw[3],
            minAvailableLockup=raw[4],
            maxExpiryDuration=raw[5],
            privacyEnabled=raw[6],
            optionalParamsUrl=raw[7],
            deliveryMethod=raw[8],
            lastUpdateTime=raw[9],
        )

    def get_metadata(self) -> dict[str, Any]:
        """Fetch the off-chain ``SourceMetadata`` JSON from IPFS.

        Makes two calls: one to read ``SourceParams.imageMetadataUrl``
        from chain, and one HTTP GET to fetch the pointed-at JSON.
        Returns the parsed dict — typically matches the structure of
        the ``SourceMetadata`` dataclass (cpu, nvidia, amd, name,
        description, logoUrl).

        Returns:
            Parsed metadata dict.

        Raises:
            IPFSFetchError: Network error, timeout, or invalid JSON.
            IPFSGatewayError: Gateway returned non-200.
        """
        params = self.get_params()
        return fetch_ipfs_json(params.imageMetadataUrl)

    def get_task_count(self) -> int:
        """Return the total number of tasks ever published against this source.

        Returns:
            Integer task count.
        """
        return int(self._contract().functions.getTaskCount().call())

    def get_tasks(self, lower: int = 0, upper: int | None = None) -> list[Task]:
        """Return the tasks published against this source, as ``Task`` instances.

        Paginated — omit ``upper`` (or pass ``None``) to fetch all
        tasks via internal chunking. Results are returned as live
        ``Task`` proxies ready for further reads.

        Args:
            lower: Start index (inclusive). Defaults to 0.
            upper: End index (exclusive). Defaults to all.

        Returns:
            List of ``Task`` instances.
        """
        from .task import Task

        addresses = _paginated_call(
            count_fn=self.get_task_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getTasks(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )
        return [Task(addr) for addr in addresses]

    def get_registrant_count(self) -> int:
        """Return the number of providers currently registered to this source.

        Returns:
            Integer registrant count.
        """
        return int(self._contract().functions.getRegistrantCount().call())

    def get_registrants(self, lower: int = 0, upper: int | None = None) -> list[str]:
        """Return the addresses of providers registered to this source.

        Paginated — omit ``upper`` to fetch all.

        Args:
            lower: Start index (inclusive).
            upper: End index (exclusive). Defaults to all.

        Returns:
            List of provider addresses.
        """
        return _paginated_call(
            count_fn=self.get_registrant_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getRegistrants(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_registrant_id(self, provider: str) -> int:
        """Return the slot index of a provider in the registrant list.

        Args:
            provider: Provider address to look up.

        Returns:
            The integer slot index, or 0 if the provider is not registered.
        """
        return int(self._contract().functions.getRegistrantId(provider).call())

    def get_preferred_environment_of(self, provider: str) -> Environment:
        """Return the hardware environment a provider registered with.

        Every ``Nexus.register`` call records which environment the
        provider registered for (CPU, NVIDIA, or AMD). This reader
        returns the choice as a typed ``Environment`` flag.

        Args:
            provider: Provider address.

        Returns:
            The provider's preferred ``Environment``.
        """
        return Environment(self._contract().functions.preferredEnvironmentOf(provider).call())

    # ------------------------------------------------------------------ #
    # Write methods
    # ------------------------------------------------------------------ #

    def set_status(self, status: SourceStatus, *, signer: Signer | None = None) -> Receipt:
        """Set the source's status by calling ``Source.setStatus(uint8)`` directly.

        Goes straight to the instance contract (owner route) rather
        than through ``Nexus.setSourceStatus`` (admin route). Must be
        called by the source's owner.

        Most client code uses ``inactivate()`` for the common transition
        to ``INACTIVE``; ``set_status`` is the lower-level primitive.

        Args:
            status: The target ``SourceStatus``.
            signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the status change.

        Raises:
            NotSourceOwnerError: If the signer isn't the source's owner.
        """
        from ._base import TxExecutor

        account = resolve_signer(signer, role=Role.CLIENT)
        return TxExecutor(
            self._contract(),
            "setStatus",
            (int(status),),
            signer=account,
            context=f"Source({self.address}).setStatus",
        ).execute()

    def set_params(self, params: SourceParams, *, signer: Signer | None = None) -> Receipt:
        """Update the source's parameters by calling ``Nexus.updateSource``.

        Goes through Nexus (rather than the source contract directly)
        so the ``SourceUpdated`` event fires. Must be called by the
        source's owner.

        Typically you'd build a fresh ``SourceInfo`` and pass it through
        ``client.update_source`` — that wrapper builds the ``SourceParams``
        for you. Use this instance method when you already have a
        ``SourceParams`` tuple.

        Args:
            params: The new ``SourceParams``.
            signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the update.

        Raises:
            NotSourceOwnerError: If the signer isn't the source's owner.
        """
        from . import nexus

        return nexus.update_source(self.address, params, signer=signer)

    def inactivate(self, *, signer: Signer | None = None) -> Receipt:
        """Inactivate the source by calling ``Nexus.inactivateSource``.

        One-way transition — there is no reactivation. After this call,
        publishing new tasks against the source reverts with
        ``SourceInactiveError``. Existing tasks continue their natural
        lifecycle.

        Args:
            signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the inactivation.

        Raises:
            NotSourceOwnerError: If the signer isn't the source's owner.
        """
        from . import nexus

        return nexus.inactivate_source(self.address, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> SourceSnapshot:
        """Return a frozen capture of every non-paginated field.

        Issues one RPC per view call in sequence (not parallel) and
        bundles the results into a ``SourceSnapshot`` dataclass.
        Omits paginated reads (``get_tasks``, ``get_registrants``) and
        IPFS reads (``get_metadata``) — call those explicitly if you
        need them.

        Use ``snapshot()`` for dashboards, logging, and atomic reads
        where you want all the fields to come from roughly the same
        block. For single-field reads, use the getter directly.

        Returns:
            ``SourceSnapshot`` with address, client, status, params,
            task_count, registrant_count.
        """
        return SourceSnapshot(
            address=self.address,
            client=self.get_client(),
            status=self.get_status(),
            params=self.get_params(),
            task_count=self.get_task_count(),
            registrant_count=self.get_registrant_count(),
        )

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        """Case-insensitive address equality.

        Two ``Source`` instances are equal iff their addresses match
        case-insensitively. Useful for deduplicating instances across
        ``0xAbC...`` vs ``0xabc...`` spelling.
        """
        if isinstance(other, Source):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on the lowercase address, matching ``__eq__``."""
        return hash(self.address.lower())

    def __str__(self) -> str:
        """Return the address — so f-strings and logs show the raw address."""
        return self.address

    def __repr__(self) -> str:
        """Return a debugger-friendly ``<Source 0x... @chain>`` label."""
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Source {short} @{chain_label}>"
