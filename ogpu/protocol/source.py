"""Source instance class — bound to a deployed Source contract address."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._ipfs import fetch_ipfs_json
from ..types.enums import Environment, SourceStatus
from ..types.errors import SourceNotFoundError
from ..types.metadata import SourceParams, SourceSnapshot
from ._base import _DEFAULT_CHUNK_SIZE, _paginated_call, load_contract

if TYPE_CHECKING:
    from .task import Task


class Source:
    """Live, stateless proxy to an on-chain Source contract.

    Only ``self.address`` is persisted — every method issues a fresh RPC call.
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Source:
        """Eager constructor — validates existence via a cheap view call."""
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise SourceNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        return load_contract("SourceAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_client(self) -> str:
        return str(self._contract().functions.getClient().call())

    def get_status(self) -> SourceStatus:
        return SourceStatus(self._contract().functions.getStatus().call())

    def get_params(self) -> SourceParams:
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
        """Fetch the off-chain metadata JSON from the IPFS URL in source params."""
        params = self.get_params()
        return fetch_ipfs_json(params.imageMetadataUrl)

    def get_task_count(self) -> int:
        return int(self._contract().functions.getTaskCount().call())

    def get_tasks(self, lower: int = 0, upper: int | None = None) -> list[Task]:
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
        return int(self._contract().functions.getRegistrantCount().call())

    def get_registrants(self, lower: int = 0, upper: int | None = None) -> list[str]:
        return _paginated_call(
            count_fn=self.get_registrant_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getRegistrants(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_registrant_id(self, provider: str) -> int:
        return int(self._contract().functions.getRegistrantId(provider).call())

    def get_preferred_environment_of(self, provider: str) -> Environment:
        return Environment(self._contract().functions.preferredEnvironmentOf(provider).call())

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> SourceSnapshot:
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
        if isinstance(other, Source):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.address.lower())

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Source {short} @{chain_label}>"
