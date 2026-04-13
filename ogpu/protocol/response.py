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
    """Live, stateless proxy to an on-chain Response contract.

    Responses are deployed by ``Nexus.submitResponse`` whenever a
    provider produces output for a task. The Response contract carries
    the provider's signature, the payment they claimed, and a ``data``
    field holding a URL (usually IPFS) to the actual payload.

    Lifecycle: ``SUBMITTED`` → ``CONFIRMED``. The transition happens
    when the client calls ``confirm_response`` (``MANUAL_CONFIRMATION``
    delivery) or automatically on the first submit
    (``FIRST_RESPONSE`` delivery).

    Construction:

    - ``Response(address)`` — lazy, no RPC.
    - ``Response.load(address)`` — eager, probes ``get_status()``.

    Attributes:
        address: Checksummed contract address.
        chain: Optional chain binding.
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        """Construct a lazy Response instance (no RPC).

        Args:
            address: Response contract address.
            chain: Optional chain binding.
        """
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Response:
        """Eager constructor — validate that the address is a Response contract.

        Runs a ``get_status()`` probe and raises
        ``ResponseNotFoundError`` on failure.

        Args:
            address: Response contract address.
            chain: Optional chain binding.

        Returns:
            A ``Response`` instance bound to the given address.

        Raises:
            ResponseNotFoundError: If the probe fails.
        """
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise ResponseNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        """Return a web3 Contract wrapper for this response address."""
        return load_contract("ResponseAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_task(self) -> Task:
        """Navigate from this response back to its parent task.

        Returns a fresh ``Task`` instance. Useful for chaining:
        ``response.get_task().get_status()``.

        Returns:
            A ``Task`` instance bound to the parent task's address.
        """
        from .task import Task

        params = self.get_params()
        return Task(params.task)

    def get_params(self) -> ResponseParams:
        """Fetch the full on-chain ``ResponseParams`` tuple.

        Returns:
            ``ResponseParams`` with task, provider, data URL, and payment.
        """
        raw = self._contract().functions.getResponseParams().call()
        return ResponseParams(
            task=raw[0],
            provider=raw[1],
            data=raw[2],
            payment=raw[3],
        )

    def get_data(self) -> str:
        """Return the raw ``data`` field (usually an IPFS URL) as a string.

        Cheap — just reads the params tuple. For the actual content
        behind the URL, use ``fetch_data()``.

        Returns:
            The data URL string.
        """
        return str(self.get_params().data)

    def fetch_data(self) -> dict[str, Any]:
        """Fetch the off-chain payload from the data URL and parse as JSON.

        Performs one HTTP GET and returns the parsed dict. Only handles
        JSON bodies — if a provider produced binary output (model
        weights, images), use ``get_data()`` to get the URL and fetch
        it with your own client.

        Follows the A2 naming rule: ``get_data()`` is cheap/local
        (reads a field), ``fetch_data()`` is network I/O.

        Returns:
            Parsed JSON payload as a dict.

        Raises:
            IPFSFetchError: Network error or invalid JSON.
            IPFSGatewayError: Gateway returned non-200.

        Example:
            ```python
            response = task.get_confirmed_response()
            if response:
                payload = response.fetch_data()
                print(payload["result"])
            ```
        """
        return fetch_ipfs_json(self.get_data())

    def get_status(self) -> ResponseStatus:
        """Return the current status of the response.

        Returns:
            ``ResponseStatus.SUBMITTED`` or ``ResponseStatus.CONFIRMED``.
        """
        return ResponseStatus(self._contract().functions.getStatus().call())

    def get_timestamp(self) -> int:
        """Return the Unix timestamp when the response was submitted.

        Returns:
            Unix timestamp.
        """
        return int(self._contract().functions.responseTimestamp().call())

    def is_confirmed(self) -> bool:
        """Return whether this response has been confirmed by the client.

        Returns True if the response is the winning response for its
        parent task. For ``FIRST_RESPONSE`` delivery this flips to True
        immediately on submission; for ``MANUAL_CONFIRMATION`` it
        requires a separate ``confirm_response`` call from the client.

        Returns:
            True if confirmed.
        """
        return bool(self._contract().functions.confirmedFinal().call())

    # ------------------------------------------------------------------ #
    # Write methods
    # ------------------------------------------------------------------ #

    def confirm(self, *, signer: Signer | None = None) -> Receipt:
        """Confirm this response by calling ``Controller.confirmResponse``.

        Must be called by the parent task's client. On success:

        - This response transitions to ``CONFIRMED``.
        - The parent task transitions to ``FINALIZED``.
        - The escrowed payment is released from the vault to the
          response's provider.

        Only meaningful for ``MANUAL_CONFIRMATION`` delivery — for
        ``FIRST_RESPONSE``, confirmation happens automatically on
        submission.

        Args:
            signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the confirmation.

        Raises:
            NotTaskOwnerError: Caller isn't the task's client.
            ResponseAlreadyConfirmedError: Already confirmed.
        """
        from . import controller

        return controller.confirm_response(self.address, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> ResponseSnapshot:
        """Return a frozen capture of every field.

        Issues a few RPCs in sequence and bundles the results into a
        ``ResponseSnapshot`` dataclass. Note that ``fetch_data()`` is
        NOT included — the snapshot is chain-only, fetching IPFS is
        still an explicit call.

        Returns:
            ``ResponseSnapshot`` with address, task, params, data URL,
            status, timestamp, confirmed.
        """
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
        """Case-insensitive address equality."""
        if isinstance(other, Response):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on the lowercase address."""
        return hash(self.address.lower())

    def __str__(self) -> str:
        """Return the address — f-string and log friendly."""
        return self.address

    def __repr__(self) -> str:
        """Return a debugger-friendly ``<Response 0x... @chain>`` label."""
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Response {short} @{chain_label}>"
