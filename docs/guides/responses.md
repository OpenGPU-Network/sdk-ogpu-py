# Responses

Responses are the output of a task attempt. A provider runs the source's
docker image, produces a payload (JSON, usually pointing to IPFS), and
submits it via `Nexus.submitResponse`. The response lives as its own
`Response` contract on-chain.

## Listing responses for a task

```python
from ogpu.protocol import Task

task = Task.load("0xTASK")
responses = task.get_responses()

for r in responses:
    print(f"  {r.address}")
    print(f"  provider: {r.get_params().provider}")
    print(f"  status:   {r.get_status()}")
    print(f"  confirmed: {r.is_confirmed()}")
```

Or use the thin client wrapper if you don't want to hold a `Task` instance:

```python
from ogpu.client import get_task_responses

responses = get_task_responses("0xTASK")    # returns list[Response]
```

## Fetching the payload

A `Response`'s on-chain `data` field is a URL (usually IPFS) pointing to
the actual content. Use one of two methods:

```python
response = task.get_responses()[0]

# Just the URL — no network call
url = response.get_data()
print(url)   # "https://cipfs.ogpuscan.io/ipfs/QmAbC..."

# Follow the URL, parse JSON — one HTTP GET
payload = response.fetch_data()
print(payload)   # {"result": "positive", "confidence": 0.97, ...}
```

The split is intentional:

- **`get_data()`** is local — it only reads a field from the params tuple.
  Use it when you want to log or cache the URL.
- **`fetch_data()`** is network I/O — it fetches from the IPFS gateway
  and parses JSON. Use it when you want the actual content.

## Confirming a response

If the source's delivery method is `MANUAL_CONFIRMATION`, the task
stays at `RESPONDED` until the client explicitly confirms one of the
submitted responses. Confirmation releases payment and finalizes the task.

```python
target = responses[0]

# Option A: Response instance method
receipt = target.confirm(signer=CLIENT_KEY)

# Option B: client wrapper (CLIENT_PRIVATE_KEY env fallback)
from ogpu.client import confirm_response
tx_hash = confirm_response(target.address)

# Option C: protocol-level module function
from ogpu.protocol import controller
receipt = controller.confirm_response(target.address, signer=CLIENT_KEY)
```

All three do the same thing — pick whichever fits your code.

After confirmation:

```python
assert target.is_confirmed() is True
assert task.get_status().name == "FINALIZED"
assert task.get_winning_provider() == target.get_params().provider
```

## Delivery methods and their effect

`FIRST_RESPONSE` skips the confirm step:

```python
# Source published with DeliveryMethod.FIRST_RESPONSE
# As soon as any provider submits a response:
#   - Response.status       → CONFIRMED (automatic)
#   - Task.status           → FINALIZED
#   - winning_provider      → the submitting provider
```

`MANUAL_CONFIRMATION` requires an explicit confirm:

```python
# Source published with DeliveryMethod.MANUAL_CONFIRMATION
# Providers submit:
#   - Response.status       → SUBMITTED
#   - Task.status           → RESPONDED
# Client reviews, then calls confirm_response on the preferred one:
#   - Response.status       → CONFIRMED
#   - Task.status           → FINALIZED
```

## Getting the confirmed response

A shortcut for "find the one confirmed response for this task":

```python
final = task.get_confirmed_response()

if final is None:
    print("not confirmed yet")
else:
    print(final.get_data())
    print(final.fetch_data())
```

Internally this iterates `task.get_responses()` and returns the first
with `is_confirmed() == True`. It is chain-only — no HTTP fallback, no
management-backend dependency.

## Error cases

Confirming returns a typed error if something is wrong:

```python
from ogpu.types import (
    ResponseNotFoundError,
    ResponseAlreadyConfirmedError,
    NotTaskOwnerError,
    OGPUError,
)

try:
    target.confirm(signer=CLIENT_KEY)
except ResponseAlreadyConfirmedError:
    print("already done")
except NotTaskOwnerError:
    print("you're not the task client")
except ResponseNotFoundError:
    print("response contract doesn't exist at this address")
except OGPUError as e:
    print(f"other SDK failure: {type(e).__name__}: {e}")
```

See [errors](errors.md) for the full exception hierarchy.

## Response snapshot

For dashboards or logging, capture every field in one batch:

```python
snap = response.snapshot()
print(snap.address)
print(snap.task)
print(snap.data)
print(snap.status)
print(snap.timestamp)
print(snap.confirmed)
```

The snapshot is a frozen dataclass — no further RPCs when you read fields.

## Next

- [Publishing](publishing.md)
- [Events](events.md) — subscribe to `ResponseSubmitted` / `ResponseStatusChanged`
- [IPFS](ipfs.md) — more on fetching off-chain content
