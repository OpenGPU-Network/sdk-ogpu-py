# Concepts

The SDK is organized by **layer** (how low-level the code is) and by
**role** (which actor uses it). Understanding these two axes is the fastest
way to figure out where to look for a given operation.

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  ogpu.client / ogpu.agent / ogpu.events                 │  role-first
│  ─────────────────────────────────────                  │  high-level
│  publish_source, publish_task, cancel_task,             │  workflows
│  watch_attempted, agent.register_to, ...                │
├─────────────────────────────────────────────────────────┤
│  ogpu.protocol                                          │  1:1 with
│  ─────────────                                          │  contract ABIs
│  nexus, controller, terminal, vault (modules)           │
│  Source, Task, Response, Provider, Master (instances)   │
│  TxExecutor, load_contract, _paginated_call (shared)    │
├─────────────────────────────────────────────────────────┤
│  ogpu.types         ogpu.chain          ogpu.ipfs       │  leaves —
│  ──────────         ──────────          ─────────       │  pure data
│  enums              ChainConfig         publish_to_ipfs │  or shared
│  errors             Web3Manager         fetch_ipfs_json │  infrastructure
│  Receipt            NonceManager                        │
│  metadata           ABIs                                │
└─────────────────────────────────────────────────────────┘
```

**Rules:**

- `ogpu.types`, `ogpu.chain`, and `ogpu.ipfs` are leaves — they do not
  import anything from higher layers. `ogpu.types` is pure data (no network I/O).
- `ogpu.protocol` wraps every user-callable contract function 1:1 with
  the ABI. Function names match the Solidity method names (snake_cased).
- `ogpu.client` / `ogpu.agent` / `ogpu.events` are **workflow layers**
  that compose protocol calls and resolve signers from role-specific
  env vars.
- `ogpu.service` is a **separate product** that happens to ship in the
  same package — the framework source developers use inside their Docker
  containers. It does not participate in the layer hierarchy above.

## Roles

| Role | Environment variable | Typical operations |
|---|---|---|
| **Client** | `CLIENT_PRIVATE_KEY` | publish source, publish task, confirm response, cancel task |
| **Provider** | `PROVIDER_PRIVATE_KEY` | announce master, register to source, attempt task, submit response |
| **Master** | `MASTER_PRIVATE_KEY` | announce provider, remove provider, set agent |
| **Agent** | `AGENT_PRIVATE_KEY` | scheduler: register / attempt on behalf of a master |
| _Vault actor_ | _explicit `signer=` required_ | deposit, withdraw, lock, unbond, claim |

Vault operations deliberately have **no env-var fallback**. You must pass
`signer=` explicitly to prevent accidentally transacting from the wrong
account.

## Instance classes vs module functions

The protocol layer gives you two ways to do almost everything:

=== "Instance classes"

    Stateless live proxies bound to a contract address. Clean for
    dashboards, long-lived references, and anything where you already
    know the address up front.

    ```python
    from ogpu.protocol import Task

    task = Task.load("0x...")
    task.get_status()
    task.get_attempters()
    task.cancel(signer=KEY)
    task.snapshot()          # frozen batch capture
    ```

=== "Module functions"

    Function-style API for one-off calls. Good for scripts where you're
    iterating through many addresses or don't want to hold an instance.

    ```python
    from ogpu.protocol import controller, terminal, vault

    controller.cancel_task("0x...", signer=KEY)
    terminal.get_master_of("0x...")
    vault.get_balance_of("0x...")
    ```

Both hit the same underlying contracts via `TxExecutor`. Use whichever
feels cleaner for your code.

## Stateless by design

Instance classes store **only `self.address`**. They never cache on-chain
state. Every method call is a fresh RPC. This is on purpose:

- Method calls have predictable network cost — no surprise staleness
- Property access (`str(task)`, `repr(task)`) never triggers I/O
- Concurrent code can share instances without coordination

If you want atomic batch reads, call `snapshot()`:

```python
snap = task.snapshot()   # one logical batch of RPC calls
print(snap.status, snap.payment, snap.attempt_count)
# snap is a frozen dataclass — no further RPCs when you read fields
```

## Honest API: `get_*` vs `fetch_*`

Two prefixes carry different cost contracts:

- **`get_*`** — always a single RPC call, no indexer wrapping, no IPFS.
  Example: `task.get_params()` returns the raw `TaskParams` tuple.
- **`fetch_*`** — follows an off-chain URL (IPFS gateway, etc.) and
  decodes the result. Network I/O beyond the chain.
  Example: `task.get_metadata()` fetches the task config JSON from IPFS,
  `response.fetch_data()` fetches the response payload.

Nothing is ever triggered by property access or `__repr__`. If your
debugger hovers over a `Task` instance, it doesn't cost you anything.

## Signers

Every write method accepts `signer=`:

```python
from eth_account import Account

# Explicit hex string
controller.cancel_task("0x...", signer="0x" + "11" * 32)

# Or a LocalAccount (hardware wallets, KMS providers, etc.)
acc = Account.from_key("0x" + "11" * 32)
controller.cancel_task("0x...", signer=acc)

# Or omit — falls back to the env var for the role
controller.cancel_task("0x...")    # reads CLIENT_PRIVATE_KEY
```

The client-layer wrappers (`publish_source`, `cancel_task`, etc.)
traditionally use `private_key=` for backward compatibility, but you can
also pass `signer=` to the underlying protocol functions directly.

## Errors

Every SDK error inherits from [`OGPUError`](../reference/types.md#errors).
Catch the root for broad handling or any specific subclass for precision:

```python
from ogpu.types import OGPUError, TaskNotFoundError, InsufficientBalanceError

try:
    task = Task.load("0x...")
except TaskNotFoundError:
    print("no such task")

try:
    vault.lock(10**18, signer=KEY)
except InsufficientBalanceError as e:
    print(f"need {e.required}, have {e.available}")
except OGPUError:
    print("something else went wrong")
```

See [error handling](../guides/errors.md) for the full hierarchy.

## Next

- [Publishing guide](../guides/publishing.md)
- [Reading state](../guides/reading-state.md)
- [API reference](../reference/client.md)
