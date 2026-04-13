# `ogpu.events`

Async event subscriptions. Six `watch_*` generators for the critical
Nexus events, plus typed event dataclasses. This is the only async
module in the SDK — every other package is synchronous. Users who
don't need event streaming never touch async.

Each watcher is an `async def ... -> AsyncIterator[Event]` that polls
for new logs via HTTP filter subscriptions (no WebSocket provider —
works against any standard Ethereum JSON-RPC endpoint). Every yielded
event is a frozen dataclass with a typed payload and the usual trio of
block number, transaction hash, and log index.

Start with [the events guide](../guides/events.md) for async patterns
and composition with the sync publishing/reading APIs.

!!! info "Mixing sync and async"
    Publish a task synchronously, then await an async generator for
    events on that task:

    ```python
    from ogpu.client import publish_task, TaskInfo
    from ogpu.events import watch_attempted

    task = publish_task(TaskInfo(...))   # sync

    async def wait_for_attempt():
        async for event in watch_attempted(task.address):
            return event

    attempt = asyncio.run(wait_for_attempt())
    ```

---



## Watchers

::: ogpu.events.watchers.watch_task_published
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.events.watchers.watch_attempted
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.events.watchers.watch_response_submitted
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.events.watchers.watch_response_status_changed
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.events.watchers.watch_task_status_changed
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.events.watchers.watch_registered
    options:
      show_root_heading: true
      heading_level: 3

## Event dataclasses

::: ogpu.events.types.TaskPublishedEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []

::: ogpu.events.types.AttemptedEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []

::: ogpu.events.types.ResponseSubmittedEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []

::: ogpu.events.types.ResponseStatusChangedEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []

::: ogpu.events.types.TaskStatusChangedEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []

::: ogpu.events.types.RegisteredEvent
    options:
      show_root_heading: true
      heading_level: 3
      members: []
