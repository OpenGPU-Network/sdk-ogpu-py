# Reading on-chain state

The five instance classes are live proxies bound to a contract address.
Every method is a fresh RPC call — no caching. This guide walks through
the reads available on each class and when to use `snapshot()` for
batch captures.

## Source

```python
from ogpu.protocol import Source

source = Source("0x...")                    # lazy — no RPC
source = Source.load("0x...")                # eager — validates existence
```

### Reads

| Method | Returns | Notes |
|---|---|---|
| `get_client()` | `str` | Owner of the source |
| `get_status()` | `SourceStatus` | `ACTIVE` or `INACTIVE` |
| `get_params()` | `SourceParams` | Raw on-chain tuple as a typed dataclass |
| `get_metadata()` | `dict[str, Any]` | Fetches `imageMetadataUrl` from IPFS and parses JSON |
| `get_task_count()` | `int` | Number of tasks ever published against this source |
| `get_tasks(lower, upper)` | `list[Task]` | Paginated — omit `upper` to fetch all |
| `get_registrant_count()` | `int` | Number of providers registered |
| `get_registrants(lower, upper)` | `list[str]` | Provider addresses, paginated |
| `get_registrant_id(provider)` | `int` | Provider's slot index in the registrant list |
| `get_preferred_environment_of(provider)` | `Environment` | `CPU` / `NVIDIA` / `AMD` |

### Example

```python
source = Source.load("0xSOURCE")

# Basic info
print(source.get_status())                   # SourceStatus.ACTIVE
print(source.get_client())                    # 0xC...
print(source.get_task_count())                # 42

# Iterate over tasks
for task in source.get_tasks():                # list[Task]
    print(f"{task.address}  {task.get_status()}")

# Check registrants
for provider_addr in source.get_registrants():
    env = source.get_preferred_environment_of(provider_addr)
    print(f"{provider_addr} prefers {env.name}")
```

## Task

```python
from ogpu.protocol import Task

task = Task("0x...")
task = Task.load("0x...")
```

### Reads

| Method | Returns |
|---|---|
| `get_source()` | `Source` (instance) |
| `get_status()` | `TaskStatus` — `NEW` / `ATTEMPTED` / `RESPONDED` / `CANCELED` / `EXPIRED` / `FINALIZED` |
| `get_params()` | `TaskParams` |
| `get_metadata()` | `dict[str, Any]` — fetches task config from IPFS |
| `get_payment()` | `int` (wei) |
| `get_expiry_time()` | `int` (unix timestamp) |
| `get_delivery_method()` | `DeliveryMethod` |
| `get_attempt_count()` | `int` |
| `get_attempters(lower, upper)` | `list[str]` (paginated) |
| `get_attempter_id(provider)` | `int` |
| `get_attempt_timestamps(lower, upper)` | `list[int]` |
| `get_response_of(provider)` | `Response \| None` |
| `get_responses(lower, upper)` | `list[Response]` |
| `get_confirmed_response()` | `Response \| None` — iterates responses, returns first confirmed |
| `get_winning_provider()` | `str \| None` |
| `is_already_submitted(hash)` | `bool` |

### Example

```python
task = Task.load("0xTASK")

# Navigate to related entities
source = task.get_source()
print(f"Task's source: {source.address}")

# List all providers who tried
for attempter in task.get_attempters():
    resp = task.get_response_of(attempter)
    if resp:
        print(f"{attempter} submitted {resp.address}")

# Fetch the confirmed response (if any)
final = task.get_confirmed_response()
if final:
    payload = final.fetch_data()   # dict from IPFS
    print(payload)
```

!!! info "Chain-only replacement for HTTP"
    `task.get_confirmed_response()` used to be a separate standalone
    function `get_confirmed_response(task_address)` that hit the
    management-backend HTTP API. That HTTP path is gone in v0.2.1 —
    everything runs over JSON-RPC now.

## Response

```python
from ogpu.protocol import Response

response = Response("0x...")
response = Response.load("0x...")
```

### Reads

| Method | Returns |
|---|---|
| `get_task()` | `Task` (instance) |
| `get_params()` | `ResponseParams` |
| `get_data()` | `str` (raw URL) |
| `fetch_data()` | `dict[str, Any]` — follows the URL and parses JSON |
| `get_status()` | `ResponseStatus` — `SUBMITTED` / `CONFIRMED` |
| `get_timestamp()` | `int` |
| `is_confirmed()` | `bool` |

### get_data vs fetch_data

```python
url = response.get_data()        # "https://cipfs.../Qm123" — cheap, just the string
payload = response.fetch_data()  # dict — follows the URL, parses JSON
```

Use `get_data()` when you want to cache, log, or pass the URL around
without network I/O. Use `fetch_data()` when you want the actual content.

## Provider / Master

Synthetic classes that compose Terminal + Vault + Nexus calls into one
role-scoped instance. Useful for dashboards.

```python
from ogpu.protocol import Provider, Master

provider = Provider.load("0xPROV")
master = Master.load("0xMASTER")

provider.get_master()                # 0xM... (from Terminal)
provider.get_lockup()                # wei (from Vault)
provider.is_eligible()                # bool (from Vault)
provider.get_registered_sources()     # list[Source] (from Nexus)

master.get_provider()                 # 0xP... (from Terminal)
master.is_master()                    # bool
```

See [reference](../reference/protocol.md) for the full surface.

## Snapshots

When you want a frozen capture of every field in one logical batch —
for a dashboard, a log line, a unit test assertion — use `snapshot()`:

```python
snap = task.snapshot()
print(snap.status)                 # TaskStatus.RESPONDED
print(snap.payment)                # 10000000000000000
print(snap.winning_provider)        # None
print(snap.attempt_count)           # 3

# snap is a frozen dataclass — reading its fields costs nothing
# calling task.get_status() again would still trigger a fresh RPC
```

Snapshots do **one logical batch** of reads (several RPCs in sequence).
They do not cover paginated fields (`get_tasks`, `get_attempters`,
`get_responses`) or IPFS fields (`get_metadata`) — those remain
explicit calls.

Available snapshots:

| Class | Snapshot type |
|---|---|
| `Source` | `SourceSnapshot` |
| `Task` | `TaskSnapshot` |
| `Response` | `ResponseSnapshot` |
| `Provider` | `ProviderSnapshot` |
| `Master` | `MasterSnapshot` |

## Pagination

Every list-returning read accepts `lower` and `upper`:

```python
source.get_tasks(lower=0, upper=10)     # first 10
source.get_tasks(lower=100, upper=200)  # next 100
source.get_tasks()                       # fetch ALL (internal chunking)
```

When `upper` is `None` (the default), the SDK calls the matching count
function and paginates in chunks of 100 until everything is returned.
Zero addresses are filtered out silently.

There is **no cap** — if you ask for 100k items, you get 100k items.
That's the user's choice.

## Dunder methods

Instance classes support equality, hashing, repr, and str:

```python
task_a = Task("0xABC")
task_b = Task("0xabc")          # lowercase

task_a == task_b                 # True (address equality, case-insensitive)
hash(task_a) == hash(task_b)     # True
str(task_a)                      # "0xABC..." (the address)
repr(task_a)                     # "<Task 0xABC...xyz @mainnet>"

# f-string/log-friendly
print(f"Task is at {task_a}")   # Task is at 0xABC...
```

None of these trigger RPC calls.

## Next

- [Publishing](publishing.md) — creating sources and tasks
- [Responses](responses.md) — fetching payloads, confirming
- [Errors](errors.md) — exception hierarchy for failed reads
