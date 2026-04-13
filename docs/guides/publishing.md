# Publishing sources and tasks

## Publish a source

A **source** is a deployed AI service that providers can register to and
run tasks for. To publish one you need:

- A Docker image (or set of images, one per hardware environment) with
  your task handler wrapped via `ogpu.service` and exposed over HTTP
- Docker compose files hosted somewhere HTTP-fetchable (IPFS, raw
  GitHub content, S3, your own server)

```python
from web3 import Web3
from ogpu.client import (
    publish_source, SourceInfo, ImageEnvironments, DeliveryMethod,
)

source = publish_source(SourceInfo(
    name="sentiment-analyzer",
    description="DistilBERT-based sentiment classifier",
    logoUrl="https://example.com/logo.png",
    imageEnvs=ImageEnvironments(
        cpu="https://raw.githubusercontent.com/you/repo/main/docker-compose.yml",
        nvidia="https://raw.githubusercontent.com/you/repo/main/docker-compose.gpu.yml",
    ),
    minPayment=Web3.to_wei(0.01, "ether"),
    minAvailableLockup=Web3.to_wei(0.5, "ether"),
    maxExpiryDuration=86400,
    deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
))

print(source.address)
```

`publish_source` returns a live `Source` instance bound to the new
contract address. You can read state back immediately:

```python
source.get_status()                     # SourceStatus.ACTIVE
source.get_client()                     # your address
source.get_params().minPayment          # 10000000000000000
source.get_metadata()                   # dict — follows IPFS URL
```

### What the fields mean

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Human-readable name shown in dashboards |
| `description` | `str` | Short description of what the source does |
| `logoUrl` | `str` | URL to a logo image (any HTTP-fetchable location) |
| `imageEnvs` | `ImageEnvironments` | One or more docker-compose URLs, keyed by hardware (`cpu`, `nvidia`, `amd`) |
| `minPayment` | `int` | Minimum payment per task, in wei |
| `minAvailableLockup` | `int` | Minimum vault lockup a provider must hold to register to this source |
| `maxExpiryDuration` | `int` | Maximum seconds a task can live before expiring |
| `deliveryMethod` | `DeliveryMethod` | `FIRST_RESPONSE` (auto-finalize on first submit) or `MANUAL_CONFIRMATION` (client explicitly confirms) |

### Environment support

`ImageEnvironments` is a simple dataclass with three optional fields:

```python
from ogpu.client import ImageEnvironments

# CPU only
ImageEnvironments(cpu="...compose.yml")

# Multi-environment
ImageEnvironments(
    cpu="...compose.cpu.yml",
    nvidia="...compose.gpu.yml",
    amd="...compose.amd.yml",
)
```

The SDK converts this into a bitmask matching the on-chain
`Environment` enum (`CPU=1`, `NVIDIA=2`, `AMD=4`). Providers register
with their preferred environment and only get dispatched matching tasks.

### Delivery methods

| Method | Behavior |
|---|---|
| `FIRST_RESPONSE` | Task finalizes as soon as one provider submits a response. Fast, cheap, no manual action needed. Good for public-result tasks. |
| `MANUAL_CONFIRMATION` | Task sits at `RESPONDED` until the client explicitly calls `confirm_response`. Multiple providers can attempt and submit. Client picks a winner. Slower but you review quality. |

## Publish a task

```python
import time
from ogpu.client import publish_task, TaskInfo, TaskInput

task = publish_task(TaskInfo(
    source="0xYOUR_SOURCE_ADDRESS",
    config=TaskInput(
        function_name="predict",
        data={"prompt": "is this review positive or negative?"},
    ),
    expiryTime=int(time.time()) + 3600,
    payment=Web3.to_wei(0.01, "ether"),
))
```

`TaskInput` is the payload routed to the source's `@expose`d function.
The `function_name` field is mandatory — it tells the source which
handler to invoke. Everything else in `data` is passed through unchanged.

```python
# Use a dict for arbitrary JSON
TaskInput(function_name="predict", data={"text": "hello", "top_k": 5})

# Or a pydantic model for stronger typing
from pydantic import BaseModel
class Req(BaseModel):
    text: str
    top_k: int = 1

TaskInput(function_name="predict", data=Req(text="hello", top_k=5))
```

Extra keyword arguments become top-level fields in the serialized config
alongside `function_name` and `data`:

```python
TaskInput(
    function_name="predict",
    data={"text": "hi"},
    priority="high",      # extra — appears at the top level
    sensitivity="low",    # extra — same
)
```

### Task fields

| Field | Type | Description |
|---|---|---|
| `source` | `str` | Source contract address |
| `config` | `TaskInput` | Function name + input data |
| `expiryTime` | `int` | Unix timestamp after which the task expires and cannot be attempted |
| `payment` | `int` | Payment in wei, held in the vault until the task is confirmed |

## Cancel a task

Before any provider attempts, the client can cancel:

```python
receipt = task.cancel(signer=CLIENT_KEY)
assert task.get_status().name == "CANCELED"
```

After attempts start landing, cancel reverts.

## Update a source

Change `minPayment`, `minAvailableLockup`, or any other parameter:

```python
from ogpu.client import update_source, SourceInfo, ImageEnvironments

update_source(
    source.address,
    SourceInfo(
        name=source.get_params().client,      # same fields except what you're changing
        description="updated description",
        logoUrl="...",
        imageEnvs=ImageEnvironments(cpu="..."),
        minPayment=Web3.to_wei(0.05, "ether"),    # ← the change
        minAvailableLockup=0,
        maxExpiryDuration=86400,
    ),
)
```

The new params go through Nexus so the `SourceUpdated` event fires.

## Inactivate a source

When you're done accepting new tasks to this source:

```python
from ogpu.client import inactivate_source

inactivate_source(source.address)
assert source.get_status().name == "INACTIVE"
```

Publishing new tasks against an inactive source reverts with
`SourceInactiveError`.

## What happens under the hood

1. `SourceInfo` / `TaskInfo` are pure dataclasses — no side effects.
2. `client.publish_source` resolves the signer via `CLIENT_PRIVATE_KEY`
   env var (or the `private_key=` kwarg).
3. It builds a `SourceMetadata` dict and uploads it to IPFS via
   `publish_to_ipfs` — the resulting URL goes into `SourceParams.imageMetadataUrl`.
4. `Nexus.publishSource(params)` is called via `TxExecutor`, which
   handles nonce, gas, retry, and typed revert decoding.
5. The `SourcePublished` event log is parsed to extract the new source
   address.
6. A `Source` instance is constructed around that address and returned.

`publish_task` is the same pattern but with `taskConfig.json` uploaded
to IPFS and `Controller.publishTask`.

## Next

- [Reading state](reading-state.md) — instance classes and snapshots
- [Responses](responses.md) — fetching and confirming response payloads
- [Events](events.md) — watch `TaskPublished`, `Attempted`, etc. live
- [IPFS](ipfs.md) — if you want to upload custom metadata yourself
