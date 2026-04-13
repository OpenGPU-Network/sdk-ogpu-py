# Recipes

Short snippets for common patterns. Each one is standalone — copy it
into your code and adapt.

## Publish and wait for finalization

```python
import asyncio, time
from web3 import Web3
from ogpu import ChainConfig, ChainId
from ogpu.client import publish_task, TaskInfo, TaskInput
from ogpu.events import watch_task_status_changed
from ogpu.types import TaskStatus

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

task = publish_task(TaskInfo(
    source="0x...",
    config=TaskInput(function_name="predict", data={"x": 1}),
    expiryTime=int(time.time()) + 3600,
    payment=Web3.to_wei(0.01, "ether"),
))

async def wait_until_finalized(addr: str):
    async for event in watch_task_status_changed(addr):
        if event.status == TaskStatus.FINALIZED:
            return event

asyncio.run(wait_until_finalized(task.address))
print(f"done: {task.get_winning_provider()}")
```

## Batch-fetch state for N tasks

```python
from ogpu.protocol import Task

task_addresses = ["0x...", "0x...", "0x..."]
snapshots = [Task(addr).snapshot() for addr in task_addresses]

for snap in snapshots:
    print(f"{snap.address}  {snap.status}  {snap.attempt_count} attempts")
```

`snapshot()` is the efficient way — each instance issues one logical
batch of RPCs per call, rather than four or five separate getter calls.

## Filter responses by provider

```python
task = Task.load("0x...")
my_provider = "0xMY_PROVIDER"

my_response = task.get_response_of(my_provider)
if my_response and my_response.is_confirmed():
    payload = my_response.fetch_data()
```

## Only confirm responses above a quality threshold

```python
task = Task.load("0x...")

for r in task.get_responses():
    payload = r.fetch_data()
    if payload.get("confidence", 0) > 0.95:
        r.confirm(signer=CLIENT_KEY)
        break
```

## Check provider health before dispatching

```python
from ogpu.protocol import Provider

def is_healthy(addr: str) -> bool:
    p = Provider(addr)
    snap = p.snapshot()
    return (
        snap.is_provider
        and snap.is_eligible
        and snap.lockup > 10**18          # at least 1 OGPU locked
        and not snap.default_agent_disabled
    )

for addr in source.get_registrants():
    if is_healthy(addr):
        # dispatch a task to this provider
        ...
```

## Dashboard line for a source

```python
from ogpu.protocol import Source

def format_source(addr: str) -> str:
    s = Source.load(addr)
    snap = s.snapshot()
    return (
        f"{snap.address[:10]} "
        f"{snap.status.name:8s} "
        f"tasks={snap.task_count:4d} "
        f"providers={snap.registrant_count:3d} "
        f"min_payment={snap.params.minPayment:>20d} wei"
    )

for addr in my_sources:
    print(format_source(addr))
```

## Retry on nonce collision

`TxExecutor` already does this automatically — you shouldn't need to
write it manually. But if you want manual control:

```python
from ogpu import fix_nonce
from ogpu.types import NonceError

try:
    result = client.publish_task(info)
except NonceError:
    fix_nonce()            # cancel stuck pending txs
    result = client.publish_task(info)   # retry once
```

## Cancel every task for a source

```python
source = Source.load("0xSOURCE")
for task in source.get_tasks():
    if task.get_status().name == "NEW":
        task.cancel(signer=CLIENT_KEY)
```

## Load a Provider and check earnings

```python
from ogpu.protocol import Provider

provider = Provider.load("0xPROVIDER")
snap = provider.snapshot()

print(f"Master:         {snap.master}")
print(f"Balance:        {snap.balance}")
print(f"Lockup:         {snap.lockup}")
print(f"Total earnings: {snap.total_earnings}")
print(f"Eligible:       {snap.is_eligible}")
```

## Publish once, read fields many times

```python
source = publish_source(source_info)

# Multiple fields, multiple RPCs — the stateless way
print(source.get_client())
print(source.get_status())
print(source.get_task_count())

# Or: one batch capture, many local reads
snap = source.snapshot()
print(snap.client, snap.status, snap.task_count)
```

Use whichever is cleaner. `snapshot()` wins when you need more than
three fields at once.

## Next

- [Publishing](publishing.md)
- [Reading state](reading-state.md)
- [Events](events.md)
