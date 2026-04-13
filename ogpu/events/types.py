"""Typed event dataclasses — frozen snapshots of on-chain Nexus events.

Each watcher function in ``ogpu.events.watchers`` yields instances of
the matching dataclass here. They're all ``@dataclass(frozen=True)`` so
you can treat them as value objects — pass them through channels, put
them in sets, use them as dict keys.

Every event carries three common fields — ``block_number``,
``transaction_hash``, ``log_index`` — plus its event-specific payload.
Status fields (``TaskStatus``, ``ResponseStatus``) are decoded into
typed enums, not raw integers.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..types.enums import ResponseStatus, TaskStatus


@dataclass(frozen=True)
class TaskPublishedEvent:
    """Yielded by ``watch_task_published`` when a new task is published to a source.

    Attributes:
        task: New Task contract address.
        source: Source the task was published to (matches the watcher's
            scoping address).
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string) that emitted the event.
        log_index: Log index within the transaction receipt.
    """

    task: str
    source: str
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class AttemptedEvent:
    """Yielded by ``watch_attempted`` when a provider attempts a task.

    Attributes:
        task: Task being attempted (matches the watcher's scoping
            address).
        provider: Provider making the attempt.
        suggested_payment: Advisory payment amount in wei the provider
            expects.
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string).
        log_index: Log index within the receipt.
    """

    task: str
    provider: str
    suggested_payment: int
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class ResponseSubmittedEvent:
    """Yielded by ``watch_response_submitted`` when a provider submits a response.

    Attributes:
        response: Address of the newly-deployed Response contract.
        task: Task the response is for (matches the watcher's scoping
            address).
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string).
        log_index: Log index within the receipt.
    """

    response: str
    task: str
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class ResponseStatusChangedEvent:
    """Yielded by ``watch_response_status_changed`` when a response transitions state.

    Attributes:
        response: Response contract (matches the watcher's scoping
            address).
        status: Typed ``ResponseStatus`` (``SUBMITTED`` or ``CONFIRMED``)
            — decoded from the raw ``uint8`` log field.
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string).
        log_index: Log index within the receipt.
    """

    response: str
    status: ResponseStatus
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class TaskStatusChangedEvent:
    """Yielded by ``watch_task_status_changed`` when a task transitions state.

    Attributes:
        task: Task contract (matches the watcher's scoping address).
        status: Typed ``TaskStatus`` (``NEW``, ``ATTEMPTED``, ``RESPONDED``,
            ``CANCELED``, ``EXPIRED``, ``FINALIZED``) — decoded from
            the raw ``uint8`` log field.
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string).
        log_index: Log index within the receipt.
    """

    task: str
    status: TaskStatus
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class RegisteredEvent:
    """Yielded by ``watch_registered`` when a provider registers to a source.

    Attributes:
        provider: Provider being registered.
        registrant_id: Slot index assigned to this registration.
        source: Source being registered to (matches the watcher's
            scoping address).
        block_number: Block the event was emitted in.
        transaction_hash: Tx hash (hex string).
        log_index: Log index within the receipt.
    """

    provider: str
    registrant_id: int
    source: str
    block_number: int
    transaction_hash: str
    log_index: int
