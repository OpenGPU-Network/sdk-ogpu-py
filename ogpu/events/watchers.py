"""Six critical event watchers — async generators over Nexus events.

Each ``watch_*`` function is an async generator that polls for new event logs
using HTTP filter polling (no WebSocket). Events are filtered in Python by the
scoping address (task / source / response) since the Nexus events do not have
indexed parameters.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from ..types.enums import ResponseStatus, TaskStatus
from ._async_web3 import get_async_web3
from ._filters import _tx_hash_hex, get_nexus_contract
from .types import (
    AttemptedEvent,
    RegisteredEvent,
    ResponseStatusChangedEvent,
    ResponseSubmittedEvent,
    TaskPublishedEvent,
    TaskStatusChangedEvent,
)


async def _poll_event(
    event_name: str,
    filter_field: str,
    filter_value: str,
    builder: Any,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[Any]:
    """Generic polling loop shared by all watchers."""
    w3 = await get_async_web3()
    contract = await get_nexus_contract(w3)

    start = from_block if from_block is not None else await w3.eth.block_number

    event_filter = await getattr(contract.events, event_name).create_filter(fromBlock=start)

    while True:
        try:
            entries = await event_filter.get_new_entries()
        except Exception:
            await asyncio.sleep(poll_interval)
            continue

        for entry in entries:
            args = entry.get("args", {})
            addr = str(args.get(filter_field, ""))
            if addr.lower() != filter_value.lower():
                continue
            yield builder(entry)

        await asyncio.sleep(poll_interval)


def _base_fields(entry: Any) -> dict[str, Any]:
    return {
        "block_number": int(entry.get("blockNumber", 0)),
        "transaction_hash": _tx_hash_hex(entry.get("transactionHash", b"")),
        "log_index": int(entry.get("logIndex", 0)),
    }


async def watch_task_published(
    source_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[TaskPublishedEvent]:
    """Stream ``TaskPublished`` events scoped to a specific source."""

    def build(entry: Any) -> TaskPublishedEvent:
        args = entry["args"]
        return TaskPublishedEvent(
            task=str(args["task"]),
            source=str(args["source"]),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "TaskPublished",
        "source",
        source_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event


async def watch_attempted(
    task_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[AttemptedEvent]:
    """Stream ``Attempted`` events scoped to a specific task."""

    def build(entry: Any) -> AttemptedEvent:
        args = entry["args"]
        return AttemptedEvent(
            task=str(args["task"]),
            provider=str(args["provider"]),
            suggested_payment=int(args["suggestedPayment"]),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "Attempted",
        "task",
        task_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event


async def watch_response_submitted(
    task_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[ResponseSubmittedEvent]:
    """Stream ``ResponseSubmitted`` events scoped to a specific task."""

    def build(entry: Any) -> ResponseSubmittedEvent:
        args = entry["args"]
        return ResponseSubmittedEvent(
            response=str(args["response"]),
            task=str(args["task"]),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "ResponseSubmitted",
        "task",
        task_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event


async def watch_response_status_changed(
    response_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[ResponseStatusChangedEvent]:
    """Stream ``ResponseStatusChanged`` events scoped to a specific response."""

    def build(entry: Any) -> ResponseStatusChangedEvent:
        args = entry["args"]
        return ResponseStatusChangedEvent(
            response=str(args["response"]),
            status=ResponseStatus(int(args["status"])),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "ResponseStatusChanged",
        "response",
        response_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event


async def watch_task_status_changed(
    task_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[TaskStatusChangedEvent]:
    """Stream ``TaskStatusChanged`` events scoped to a specific task."""

    def build(entry: Any) -> TaskStatusChangedEvent:
        args = entry["args"]
        return TaskStatusChangedEvent(
            task=str(args["task"]),
            status=TaskStatus(int(args["status"])),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "TaskStatusChanged",
        "task",
        task_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event


async def watch_registered(
    source_address: str,
    *,
    from_block: int | None = None,
    poll_interval: float = 2.0,
) -> AsyncIterator[RegisteredEvent]:
    """Stream ``Registered`` events scoped to a specific source."""

    def build(entry: Any) -> RegisteredEvent:
        args = entry["args"]
        return RegisteredEvent(
            provider=str(args["provider"]),
            registrant_id=int(args["registrantId"]),
            source=str(args["source"]),
            **_base_fields(entry),
        )

    async for event in _poll_event(
        "Registered",
        "source",
        source_address,
        build,
        from_block=from_block,
        poll_interval=poll_interval,
    ):
        yield event
