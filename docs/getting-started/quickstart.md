# Quickstart

A complete client-side flow: publish a source, publish a task against it,
watch for an attempt, fetch the response, and confirm. Under 30 lines of
real code.

## Prerequisites

- `ogpu` installed ([installation](installation.md))
- `CLIENT_PRIVATE_KEY` env var set, with testnet gas in the account
- A source already running on testnet **or** you're publishing your own

```bash
export CLIENT_PRIVATE_KEY=0xYOUR_TESTNET_KEY
```

## Full flow

```python
import time
from web3 import Web3

from ogpu import ChainConfig, ChainId
from ogpu.client import (
    publish_source, publish_task,
    SourceInfo, TaskInfo, TaskInput, ImageEnvironments, DeliveryMethod,
)

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

# 1. Publish a source
source = publish_source(SourceInfo(
    name="quickstart-demo",
    description="Quickstart guide demo source",
    logoUrl="https://example.com/logo.png",
    imageEnvs=ImageEnvironments(
        cpu="https://cipfs.ogpuscan.io/ipfs/QmNWFLL13ujf3KUTJvfNx42bA5fWDV96qqUdjY6nwpuwD9",
    ),
    minPayment=Web3.to_wei(0.01, "ether"),
    minAvailableLockup=0,
    maxExpiryDuration=86400,
    deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
))

print(f"Source: {source.address}")       # live Source instance
print(f"Status: {source.get_status()}")  # SourceStatus.ACTIVE

# 2. Publish a task against it
task = publish_task(TaskInfo(
    source=source.address,
    config=TaskInput(function_name="predict", data={"prompt": "hello world"}),
    expiryTime=int(time.time()) + 3600,
    payment=Web3.to_wei(0.01, "ether"),
))

print(f"Task: {task.address}")            # live Task instance
print(f"Status: {task.get_status()}")     # TaskStatus.NEW
```

That's the core flow. `publish_source` returns a `Source` and
`publish_task` returns a `Task` — each is a live proxy bound to the new
contract address. Method calls hit the chain fresh every time.

## Reading state back

Once your task is published, inspect it in real time:

```python
task.get_status()                # TaskStatus.NEW / ATTEMPTED / FINALIZED
task.get_attempt_count()         # int
task.get_attempters()            # list[str] of provider addresses
task.get_source().get_status()   # navigate to the source
task.get_payment()               # wei

snap = task.snapshot()           # frozen capture of every field
print(snap.payment, snap.winning_provider)
```

## Confirming a response

```python
from ogpu.protocol import Response

# After some provider attempts and submits, get the response
responses = task.get_responses()
target = responses[0]

print(target.get_data())         # URL of payload (usually IPFS)
payload = target.fetch_data()    # follow URL, parse JSON

# Confirm it — releases payment, task finalizes
receipt = target.confirm(signer="YOUR_CLIENT_KEY")
print(f"Confirmed in {receipt.tx_hash}")

assert task.get_status().name == "FINALIZED"
```

## Watching events (async)

```python
import asyncio
from ogpu.events import watch_attempted

async def wait_for_attempt(task_addr: str):
    async for event in watch_attempted(task_addr):
        print(f"Attempted by {event.provider} at block {event.block_number}")
        return event

asyncio.run(wait_for_attempt(task.address))
```

Six `watch_*` functions cover the critical Nexus events
(`TaskPublished`, `Attempted`, `ResponseSubmitted`, `ResponseStatusChanged`,
`TaskStatusChanged`, `Registered`). See
[watching events](../guides/events.md).

## Cleaning up

If you published a task but nobody attempted it and you want to cancel:

```python
task.cancel(signer="YOUR_CLIENT_KEY")
assert task.get_status().name == "CANCELED"
```

## What just happened

- **`publish_source` / `publish_task`** build metadata off-chain, upload it to
  IPFS, then call the `Nexus.publishSource` / `Controller.publishTask`
  contracts. They return `Source` / `Task` instances, not strings.
- **Instance classes** are stateless — only `self.address` is stored. Every
  method call is a fresh on-chain read.
- **`task.snapshot()`** batches reads into one frozen dataclass if you need
  all fields atomically (for dashboards, logging, etc.).
- **Signer** defaults to `CLIENT_PRIVATE_KEY` env var; pass `signer=` or
  `private_key=` to override.

## Next

- [Concepts](concepts.md) — the package layout and layer model
- [Publishing guide](../guides/publishing.md) — deeper dive on source/task publishing
- [Reading state](../guides/reading-state.md) — instance classes, snapshots, metadata
- [Responses](../guides/responses.md) — fetching, confirming, fulfillment lifecycle
