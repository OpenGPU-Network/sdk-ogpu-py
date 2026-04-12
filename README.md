# OpenGPU Python SDK

Python SDK for the [OpenGPU Network](https://opengpu.network) distributed AI compute marketplace.

```
pip install ogpu
```

## Overview

The SDK has two sides:

- **`ogpu.client` / `ogpu.protocol`** — interact with the blockchain: publish sources and tasks, manage vault staking, monitor events
- **`ogpu.service`** — framework for source developers to expose task handlers inside Docker containers

## Quick Start

### Publish a Task

```python
import time
from web3 import Web3
from ogpu.client import ChainConfig, ChainId, TaskInfo, TaskInput, publish_task

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

task = publish_task(TaskInfo(
    source="0xYOUR_SOURCE_ADDRESS",
    config=TaskInput(function_name="predict", data={"prompt": "hello"}),
    expiryTime=int(time.time()) + 3600,
    payment=Web3.to_wei(0.01, "ether"),
))

print(task.address)             # contract address
print(task.get_status())        # TaskStatus.NEW
print(task.get_source().address)  # navigate to the source
```

### Instance Classes

Every on-chain entity has a live proxy class. Methods hit the chain on every call — no stale cache.

```python
from ogpu.protocol import Source, Task, Response, Provider, Master

task = Task.load("0xTASK_ADDRESS")   # validates existence on-chain
task.get_status()                     # TaskStatus
task.get_attempters()                 # list[str]
task.get_confirmed_response()         # Response | None (chain-only)
task.cancel(signer=my_key)            # Receipt

snap = task.snapshot()                # frozen capture of all fields
print(snap.status, snap.payment, snap.attempt_count)
```

### Vault Operations

```python
from ogpu.protocol import vault

vault.deposit("0xBENEFICIARY", amount=10**18, signer=my_key)
vault.lock(amount=5 * 10**17, signer=my_key)
vault.get_balance_of("0xADDRESS")    # int (wei)
vault.is_eligible("0xADDRESS")       # bool
```

### Event Watching (Async)

```python
import asyncio
from ogpu.events import watch_attempted

async def monitor(task_addr: str):
    async for event in watch_attempted(task_addr):
        print(f"Attempt from {event.provider} @ block {event.block_number}")

asyncio.run(monitor("0xTASK_ADDRESS"))
```

### Custom RPC

```python
from ogpu.client import ChainConfig

ChainConfig.set_rpc("https://my-private-node.example")
ChainConfig.get_rpc()     # current URL
ChainConfig.reset_rpc()   # restore default
```

## Architecture

```
ogpu/
  protocol/     # low-level 1:1 contract wrappers
    nexus, controller, terminal, vault
    Source, Task, Response, Provider, Master
  client/       # high-level client workflows
  events/       # async event watchers (the one async island)
  types/        # enums, errors, Receipt, metadata
  service/      # source developer framework (separate concern)
```

**Protocol layer** — every Solidity view has a Python accessor, every state-changing function has a writer. Signer management via per-call `signer=` parameter with role-based env-var fallback (`CLIENT_PRIVATE_KEY`, `PROVIDER_PRIVATE_KEY`, `MASTER_PRIVATE_KEY`).

**Instance classes** — `Source(addr)`, `Task(addr)`, `Response(addr)`, `Provider(addr)`, `Master(addr)`. Stateless — only `self.address` is stored. `Task.load(addr)` validates existence eagerly.

**Events** — async generators in `ogpu.events`. HTTP filter polling, not WebSocket. Rest of SDK is sync.

## Requirements

- Python >= 3.10
- `web3 >= 7.0`

## Documentation

Full docs: **https://opengpu-network.github.io/sdk-ogpu-py/**

## Writing a Task Handler (ogpu.service)

```python
import ogpu.service
from pydantic import BaseModel

class MultiplyInput(BaseModel):
    a: int
    b: int

class MultiplyOutput(BaseModel):
    result: int

@ogpu.service.expose()
def multiply(data: MultiplyInput) -> MultiplyOutput:
    return MultiplyOutput(result=data.a * data.b)

ogpu.service.start()
```

## License

MIT
