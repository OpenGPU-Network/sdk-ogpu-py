"""Task instance class — bound to a deployed Task contract address."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..ipfs import fetch_ipfs_json
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
    """Live, stateless proxy to an on-chain Task contract.

    Holds only ``self.address`` and ``self.chain`` — no cached state.
    Every method is a fresh RPC call.

    A task's lifecycle: ``NEW`` → ``ATTEMPTED`` (first attempt arrives)
    → ``RESPONDED`` (first response submitted) → ``FINALIZED`` (response
    confirmed or first-response auto-finalization). Alternative exits:
    ``CANCELED`` (client canceled before any attempts) or ``EXPIRED``
    (``expiryTime`` passed without resolution).

    Two construction modes:

    - ``Task(address)`` — lazy, no RPC.
    - ``Task.load(address)`` — eager, probes ``get_status()`` and
      raises ``TaskNotFoundError`` on failure.

    Equality is case-insensitive address comparison; hashing matches,
    so ``Task`` instances are usable as dict keys or in sets.

    Example:
        ```python
        from ogpu.protocol import Task

        task = Task.load("0xTASK")
        print(task.get_status())
        # <TaskStatus.NEW: 0>

        source = task.get_source()  # navigate back to the source
        for attempter in task.get_attempters():
            print(attempter)
        ```

    Attributes:
        address: Checksummed contract address.
        chain: Optional chain binding.
    """

    __slots__ = ("address", "chain")

    def __init__(self, address: str, chain: object = None) -> None:
        """Construct a lazy Task instance (no RPC).

        Args:
            address: Task contract address. Checksummed automatically.
            chain: Optional chain binding.
        """
        from ._base import _get_web3

        self.address: str = _get_web3().to_checksum_address(address)
        self.chain = chain

    @classmethod
    def load(cls, address: str, chain: object = None) -> Task:
        """Eager constructor — validate that the address is a Task contract.

        Runs a cheap ``get_status()`` probe. If the probe reverts,
        raises ``TaskNotFoundError``.

        Args:
            address: Task contract address.
            chain: Optional chain binding.

        Returns:
            A ``Task`` instance bound to the given address.

        Raises:
            TaskNotFoundError: If the probe call fails.
        """
        instance = cls(address, chain)
        try:
            instance.get_status()
        except Exception as exc:
            raise TaskNotFoundError(address=address) from exc
        return instance

    def _contract(self) -> Any:
        """Return a web3 Contract wrapper for this task address."""
        return load_contract("TaskAbi", address=self.address)

    # ------------------------------------------------------------------ #
    # Read methods
    # ------------------------------------------------------------------ #

    def get_source(self) -> Source:
        """Navigate from this task back to its parent source.

        Returns a fresh ``Source`` instance (no RPC beyond the one
        that reads the address). Useful for chaining reads:
        ``task.get_source().get_status()``.

        Returns:
            A ``Source`` instance bound to the source contract.
        """
        from .source import Source

        addr = str(self._contract().functions.getSource().call())
        return Source(addr)

    def get_status(self) -> TaskStatus:
        """Return the current lifecycle status of the task.

        Returns:
            One of ``TaskStatus.NEW``, ``ATTEMPTED``, ``RESPONDED``,
            ``CANCELED``, ``EXPIRED``, ``FINALIZED``.
        """
        return TaskStatus(self._contract().functions.getStatus().call())

    def get_params(self) -> TaskParams:
        """Fetch the full on-chain ``TaskParams`` tuple.

        Includes the source address, IPFS config URL, expiry time, and
        payment. For the actual task input (function name + data), use
        ``get_metadata()`` which follows the IPFS URL.

        Returns:
            ``TaskParams`` dataclass with every field from the contract.
        """
        raw = self._contract().functions.taskParams().call()
        return TaskParams(
            source=raw[0],
            config=raw[1],
            expiryTime=raw[2],
            payment=raw[3],
        )

    def get_metadata(self) -> dict[str, Any]:
        """Fetch the task's config JSON from IPFS.

        Reads ``TaskParams.config`` (an IPFS URL) and fetches the
        pointed-at JSON body. The returned dict typically matches the
        structure of the ``TaskInput`` that was uploaded when the
        task was published — ``function_name``, ``data``, and any
        extra fields the client added.

        Returns:
            Parsed config dict.

        Raises:
            IPFSFetchError / IPFSGatewayError: On fetch failure.
        """
        params = self.get_params()
        return fetch_ipfs_json(params.config)

    def get_payment(self) -> int:
        """Return the payment offered by this task, in wei.

        Returns:
            Payment amount in wei.
        """
        return int(self._contract().functions.getPayment().call())

    def get_expiry_time(self) -> int:
        """Return the task's expiry as a Unix timestamp.

        After this time, attempts and responses revert. Nexus will
        mark the task ``EXPIRED`` on the next attempt.

        Returns:
            Unix timestamp.
        """
        return int(self._contract().functions.getExpiryTime().call())

    def get_delivery_method(self) -> DeliveryMethod:
        """Return the delivery method inherited from the source.

        Tasks inherit their delivery method from the source at publish
        time — it cannot be changed after publication.

        Returns:
            ``DeliveryMethod.MANUAL_CONFIRMATION`` or
            ``DeliveryMethod.FIRST_RESPONSE``.
        """
        return DeliveryMethod(self._contract().functions.getDeliveryMethod().call())

    def get_attempt_count(self) -> int:
        """Return the number of providers who've attempted this task.

        Returns:
            Integer attempt count.
        """
        return int(self._contract().functions.getAttemptCount().call())

    def get_attempters(self, lower: int = 0, upper: int | None = None) -> list[str]:
        """Return the addresses of providers who attempted this task.

        Paginated — omit ``upper`` to fetch all.

        Args:
            lower: Start index (inclusive).
            upper: End index (exclusive). Defaults to all.

        Returns:
            List of provider addresses.
        """
        return _paginated_call(
            count_fn=self.get_attempt_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getAttempters(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_attempter_id(self, provider: str) -> int:
        """Return the slot index of a provider in the attempter list.

        Args:
            provider: Provider address.

        Returns:
            The integer slot index, or 0 if the provider hasn't attempted.
        """
        return int(self._contract().functions.getAttempterId(provider).call())

    def get_attempt_timestamps(self, lower: int = 0, upper: int | None = None) -> list[int]:
        """Return the timestamps at which attempts were submitted.

        Each attempter has a corresponding timestamp, stored at the same
        index as in ``get_attempters``. Useful for latency analysis or
        dispatching timeouts based on how long ago a provider claimed
        the task.

        Args:
            lower: Start index.
            upper: End index. Defaults to all.

        Returns:
            List of Unix timestamps.
        """
        return _paginated_call(
            count_fn=self.get_attempt_count,
            fetch_fn=lambda lo, hi: self._contract().functions.getAttemptTimestamps(lo, hi).call(),
            lower=lower,
            upper=upper,
            chunk_size=_DEFAULT_CHUNK_SIZE,
        )

    def get_response_of(self, provider: str) -> Response | None:
        """Return the response submitted by a specific provider.

        Args:
            provider: Provider address to query.

        Returns:
            A ``Response`` instance, or ``None`` if the provider hasn't
            submitted a response for this task.
        """
        from .response import Response

        addr = str(self._contract().functions.responseOf(provider).call())
        if addr == ZERO_ADDRESS:
            return None
        return Response(addr)

    def get_responses(self, lower: int = 0, upper: int | None = None) -> list[Response]:
        """Return all responses submitted for this task, as ``Response`` instances.

        Paginated — omit ``upper`` to fetch all.

        Args:
            lower: Start index.
            upper: End index. Defaults to all.

        Returns:
            List of ``Response`` instances.
        """
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
        """Return the confirmed response for this task, if any.

        Chain-only replacement for the old HTTP-based
        ``get_confirmed_response(task_address)`` function. Iterates
        through ``get_responses()`` and returns the first one with
        ``is_confirmed() == True``. Since at most one response per task
        can be confirmed, this is the winning response.

        Returns:
            A confirmed ``Response``, or ``None`` if no response has
            been confirmed yet.
        """
        for resp in self.get_responses():
            if resp.is_confirmed():
                return resp
        return None

    def get_winning_provider(self) -> str | None:
        """Return the address of the provider whose response was confirmed.

        Returns:
            Provider address if the task has been finalized, otherwise
            ``None``.
        """
        addr = str(self._contract().functions.winningProvider().call())
        return None if addr == ZERO_ADDRESS else addr

    def is_already_submitted(self, hash_bytes: bytes) -> bool:
        """Return whether a given response hash has already been submitted.

        Used by providers to deduplicate response content — the
        contract tracks submitted hashes to prevent double-submission
        of the same payload from the same provider.

        Args:
            hash_bytes: 32-byte hash of the response payload.

        Returns:
            True if a response with this hash has already been recorded.
        """
        return bool(self._contract().functions.isAlreadySubmitted(hash_bytes).call())

    # ------------------------------------------------------------------ #
    # Write methods
    # ------------------------------------------------------------------ #

    def cancel(self, *, signer: Signer | None = None) -> Receipt:
        """Cancel the task by calling ``Controller.cancelTask``.

        Only works while the task is still in ``NEW`` state — once any
        provider has called ``attempt``, cancel reverts with
        ``TaskAlreadyFinalizedError`` (or similar). Must be called by
        the task's client.

        On success, the escrowed payment is released back to the client
        and the task transitions to ``CANCELED``.

        Args:
            signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

        Returns:
            ``Receipt`` for the cancellation.

        Raises:
            NotTaskOwnerError: If the signer isn't the task's client.
            TaskAlreadyFinalizedError: If the task is past ``NEW`` state.
        """
        from . import controller

        return controller.cancel_task(self.address, signer=signer)

    # ------------------------------------------------------------------ #
    # Snapshot
    # ------------------------------------------------------------------ #

    def snapshot(self) -> TaskSnapshot:
        """Return a frozen capture of every non-paginated field.

        Issues one RPC per view call (sequential, not parallel) and
        bundles the results into a ``TaskSnapshot`` dataclass. Omits
        paginated fields (``get_attempters``, ``get_responses``) and
        IPFS-fetching fields (``get_metadata``) — call those explicitly.

        Returns:
            ``TaskSnapshot`` with address, source, status, params,
            payment, expiry_time, delivery_method, attempt_count, and
            winning_provider.
        """
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
        """Case-insensitive address equality."""
        if isinstance(other, Task):
            return self.address.lower() == other.address.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on the lowercase address."""
        return hash(self.address.lower())

    def __str__(self) -> str:
        """Return the address — f-string and log friendly."""
        return self.address

    def __repr__(self) -> str:
        """Return a debugger-friendly ``<Task 0x... @chain>`` label."""
        chain_label = getattr(self.chain, "name", "mainnet") if self.chain else "mainnet"
        short = self.address[:8] + "..." + self.address[-4:]
        return f"<Task {short} @{chain_label}>"
