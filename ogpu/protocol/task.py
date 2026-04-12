"""Task instance class — bound to a deployed Task contract address."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._ipfs import fetch_ipfs_json
from ..types.enums import DeliveryMethod, TaskStatus
from ..types.errors import TaskNotFoundError
from ..types.metadata import TaskParams, TaskSnapshot
from ..types.receipt import Receipt
from ._base import _DEFAULT_CHUNK_SIZE, ZERO_ADDRESS, _paginated_call, load_contract
from ._signer import Signer

if TYPE_CHECKING:
    from .response import Response
    from .source import Source


class Task:
    """Live, stateless proxy to an on-chain Task contract."""

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Task:
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise TaskNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        return load_contract("TaskAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_source(self) -> Source:
        from .source import Source

        addr = str(self._contract().functions.getSource().call())
        return Source(addr)

    def get_status(self) -> TaskStatus:
        return TaskStatus(self._contract().functions.getStatus().call())

    def get_params(self) -> TaskParams:
        raw = self._contract().functions.taskParams().call()
        return TaskParams(
            source=raw[0],
            config=raw[1],
            expiryTime=raw[2],
            payment=raw[3],
        )

    def get_metadata(self) -> dict[str, Any]:
        """Fetch the off-chain task config JSON from the IPFS URL in task params."""
        params = self.get_params()
        return fetch_ipfs_json(params.config)

    def get_payment(self) -> int:
        return int(self._contract().functions.getPayment().call())

    def get_expiry_time(self) -> int:
        return int(self._contract().functions.getExpiryTime().call())

    def get_delivery_method(self) -> DeliveryMethod:
        return DeliveryMethod(self._contract().functions.getDeliveryMethod().call())

    def get_attempt_count(self) -> int:
        return int(self._contract().functions.getAttemptCount().call())

    def get_attempters(self, lower: int = 0, upper: int | None = None) -> list[str]:
        return _paginated_call(
            count_fn=self.get_attempt_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getAttempters(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_attempter_id(self, provider: str) -> int:
        return int(self._contract().functions.getAttempterId(provider).call())

    def get_attempt_timestamps(self, lower: int = 0, upper: int | None = None) -> list[int]:
        return _paginated_call(
            count_fn=self.get_attempt_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getAttemptTimestamps(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_response_of(self, provider: str) -> Response | None:
        from .response import Response

        addr = str(self._contract().functions.responseOf(provider).call())
        if addr == ZERO_ADDRESS:
            return None
        return Response(addr)

    def get_responses(self, lower: int = 0, upper: int | None = None) -> list[Response]:
        from .response import Response

        addresses = _paginated_call(
            count_fn=self.get_attempt_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getResponsesOf(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )
        return [Response(addr) for addr in addresses]

    def get_confirmed_response(self) -> Response | None:
        """Return the first confirmed response, or None. Chain-only — no HTTP."""
        for resp in self.get_responses():
            if resp.is_confirmed():
                return resp
        return None

    def get_winning_provider(self) -> str | None:
        addr = str(self._contract().functions.winningProvider().call())
        return None if addr == ZERO_ADDRESS else addr

    def is_already_submitted(self, hash_bytes: bytes) -> bool:
        return bool(self._contract().functions.isAlreadySubmitted(hash_bytes).call())

    # ------------------------------------------------------------------ #
    # Write methods
    # ------------------------------------------------------------------ #

    def cancel(self, *, signer: Signer | None = None) -> Receipt:
        """Call ``Controller.cancelTask(task)``."""
        from . import controller

        return controller.cancel_task(self.address, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> TaskSnapshot:
        return TaskSnapshot(
            address=self.address,
            source=str(self._contract().functions.getSource().call()),
            status=self.get_status(),
            params=self.get_params(),
            payment=self.get_payment(),
            expiry_time=self.get_expiry_time(),
            delivery_method=self.get_delivery_method(),
            attempt_count=self.get_attempt_count(),
            winning_provider=self.get_winning_provider(),
        )

    # ------------------------------------------------------------------ #
    # Dunder
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.address.lower())

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Task {short} @{chain_label}>"
