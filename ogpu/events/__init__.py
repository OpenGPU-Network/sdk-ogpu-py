"""Async event subscription — the one async island in the SDK.

Usage::

    import asyncio
    from ogpu.events import watch_attempted

    async def monitor(task_addr: str):
        async for event in watch_attempted(task_addr):
            print(f"Attempt from {event.provider}")

    asyncio.run(monitor("0x..."))
"""

from __future__ import annotations

from .types import (
    AttemptedEvent,
    RegisteredEvent,
    ResponseStatusChangedEvent,
    ResponseSubmittedEvent,
    TaskPublishedEvent,
    TaskStatusChangedEvent,
)
from .watchers import (
    watch_attempted,
    watch_registered,
    watch_response_status_changed,
    watch_response_submitted,
    watch_task_published,
    watch_task_status_changed,
)

__all__ = [
    "watch_task_published",
    "watch_attempted",
    "watch_response_submitted",
    "watch_response_status_changed",
    "watch_task_status_changed",
    "watch_registered",
    "TaskPublishedEvent",
    "AttemptedEvent",
    "ResponseSubmittedEvent",
    "ResponseStatusChangedEvent",
    "TaskStatusChangedEvent",
    "RegisteredEvent",
]
