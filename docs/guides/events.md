# Watching events

`ogpu.events` is the one async module in the SDK. It exposes six
async generators — one per critical Nexus event — that poll for new
logs and yield typed event dataclasses.

```python
import asyncio
from ogpu.events import watch_attempted

async def monitor(task_addr: str):
    async for event in watch_attempted(task_addr):
        print(f"Attempt from {event.provider}")
        print(f"Suggested payment: {event.suggested_payment} wei")
        print(f"Block: {event.block_number}")

asyncio.run(monitor("0x..."))
```

## The six watchers

All live in `ogpu.events`:

| Watcher | Scope | Yields |
|---|---|---|
| `watch_task_published(source)` | Tasks published against a source | `TaskPublishedEvent` |
| `watch_attempted(task)` | Provider attempts on a task | `AttemptedEvent` |
| `watch_response_submitted(task)` | Response submissions for a task | `ResponseSubmittedEvent` |
| `watch_response_status_changed(response)` | Status changes on a response | `ResponseStatusChangedEvent` |
| `watch_task_status_changed(task)` | Status changes on a task | `TaskStatusChangedEvent` |
| `watch_registered(source)` | Provider registrations to a source | `RegisteredEvent` |

## Event dataclasses

All frozen dataclasses, all under `ogpu.events`:

```python
from ogpu.events import (
    TaskPublishedEvent, AttemptedEvent, ResponseSubmittedEvent,
    ResponseStatusChangedEvent, TaskStatusChangedEvent, RegisteredEvent,
)
```

Each includes common fields (`block_number`, `transaction_hash`,
`log_index`) plus the event-specific payload.

```python
@dataclass(frozen=True)
class AttemptedEvent:
    task: str                    # task contract address
    provider: str                # attempting provider
    suggested_payment: int       # wei
    block_number: int
    transaction_hash: str
    log_index: int
```

Status events decode the raw `uint8` status into the typed enum:

```python
@dataclass(frozen=True)
class TaskStatusChangedEvent:
    task: str
    status: TaskStatus           # typed, not raw int
    block_number: int
    ...
```

## Parameters

Every watcher accepts the same keyword arguments:

| Kwarg | Default | Description |
|---|---|---|
| `from_block` | `None` | Start block — `None` means "latest" (only new events) |
| `poll_interval` | `2.0` | Seconds between polls. Raise for less RPC chatter, lower for faster reaction |

```python
# Start from a specific block
async for event in watch_attempted("0x...", from_block=1234567):
    ...

# Poll more aggressively
async for event in watch_attempted("0x...", poll_interval=0.5):
    ...
```

## Mixing sync and async

The SDK's publish/confirm calls are sync. Event watching is async. Mix
them with `asyncio.run`:

```python
from ogpu.client import publish_task, TaskInfo
from ogpu.events import watch_attempted

task = publish_task(TaskInfo(...))   # sync

async def wait_for_first_attempt():
    async for event in watch_attempted(task.address):
        return event

attempt = asyncio.run(wait_for_first_attempt())
print(f"{attempt.provider} got there first")
```

## Early termination

Async generators naturally stop when you `break` or `return`:

```python
async def count_attempts(task_addr: str, limit: int = 3):
    attempts = []
    async for event in watch_attempted(task_addr):
        attempts.append(event)
        if len(attempts) >= limit:
            return attempts
```

## Timeout

`asyncio.wait_for` gives you a hard deadline:

```python
async def wait_for_attempt_with_timeout(task_addr: str, seconds: float):
    async def inner():
        async for event in watch_attempted(task_addr):
            return event
    return await asyncio.wait_for(inner(), timeout=seconds)

attempt = await wait_for_attempt_with_timeout("0x...", 120.0)
```

## How it works

Under the hood, each watcher:

1. Creates a single `AsyncWeb3` instance for the current chain (cached
   across watchers in the same process)
2. Loads the Nexus contract ABI at the configured address
3. Creates an `eth_newFilter` subscription on the event signature
4. Polls `eth_getFilterChanges` every `poll_interval` seconds
5. Decodes each log into the typed dataclass
6. Filters out events that don't match the scoping address (the Nexus
   events have non-indexed parameters, so filtering happens in Python
   after the fetch)

This is HTTP filter polling — not WebSocket. It works against any
standard Ethereum JSON-RPC endpoint.

## Async isolation

`ogpu.events` is the **only** async module in the SDK. Everything else
(client, protocol, chain, agent, ipfs) is sync. Users who don't need
event streaming never touch async.

Per the design, there is no `ogpu.aio.*` namespace. The async code
lives under the regular `ogpu.events` path and you `asyncio.run` your
way in and out when you need it.

## Next

- [Agents](agents.md) — schedulers that drive Nexus calls in response to events
- [API reference: ogpu.events](../reference/events.md)
