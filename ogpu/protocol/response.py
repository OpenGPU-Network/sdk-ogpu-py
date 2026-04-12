"""Response instance class — bound to a deployed Response contract address."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..ipfs import fetch_ipfs_json
from ..types.enums import ResponseStatus
from ..types.errors import ResponseNotFoundError
from ..types.metadata import ResponseParams, ResponseSnapshot
from ..types.receipt import Receipt
from ._base import load_contract
from ._signer import Signer

if TYPE_CHECKING:
    from .task import Task


class Response:
    """Live, stateless proxy to an on-chain Response contract."""

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Response:
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise ResponseNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        return load_contract("ResponseAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_task(self) -> Task:
        from .task import Task

        params = self.get_params()
        return Task(params.task)

    def get_params(self) -> ResponseParams:
        raw = self._contract().functions.getResponseParams().call()
        return ResponseParams(
            task=raw[0],
            provider=raw[1],
            data=raw[2],
            payment=raw[3],
        )

    def get_data(self) -> str:
        """Return the raw ``data`` field from ``ResponseParams`` (usually an IPFS URL)."""
        return str(self.get_params().data)

    def fetch_data(self) -> dict[str, Any]:
        """Fetch and parse the off-chain response payload as JSON.

        ``get_data`` returns the URL string; ``fetch_data`` actually follows
        it and parses the JSON body. Raises ``IPFSFetchError`` / ``IPFSGatewayError``
        on network failure. Use ``get_data`` if you need the raw URL (for
        caching, custom decoding, binary payloads, etc.).
        """
        return fetch_ipfs_json(self.get_data())

    def get_status(self) -> ResponseStatus:
        return ResponseStatus(self._contract().functions.getStatus().call())

    def get_timestamp(self) -> int:
        return int(self._contract().functions.responseTimestamp().call())

    def is_confirmed(self) -> bool:
        return bool(self._contract().functions.confirmedFinal().call())

    # ------------------------------------------------------------------ #
    # Write methods
    # ------------------------------------------------------------------ #

    def confirm(self, *, signer: Signer | None = None) -> Receipt:
        """Call ``Controller.confirmResponse(response)``."""
        from . import controller

        return controller.confirm_response(self.address, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> ResponseSnapshot:
        params = self.get_params()
        return ResponseSnapshot(
            address=self.address,
            task=params.task,
            params=params,
            data=params.data,
            status=self.get_status(),
            timestamp=self.get_timestamp(),
            confirmed=self.is_confirmed(),
        )

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Response):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.address.lower())

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Response {short} @{chain_label}>"
