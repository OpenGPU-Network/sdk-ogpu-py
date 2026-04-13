# Error handling

Every SDK error inherits from `OGPUError`. Catch the root for broad
handling, or any specific subclass for precision.

```python
from ogpu.types import OGPUError

try:
    do_something()
except OGPUError as e:
    log.error(f"SDK failure: {type(e).__name__}: {e}")
```

## The hierarchy

```
OGPUError
├── NotFoundError
│   ├── TaskNotFoundError
│   ├── SourceNotFoundError
│   ├── ResponseNotFoundError
│   ├── ProviderNotFoundError
│   └── MasterNotFoundError
│
├── StateError
│   ├── TaskExpiredError
│   ├── TaskAlreadyFinalizedError
│   ├── ResponseAlreadyConfirmedError
│   └── SourceInactiveError
│
├── PermissionError
│   ├── NotTaskOwnerError
│   ├── NotSourceOwnerError
│   ├── NotMasterError
│   └── NotProviderError
│
├── VaultError
│   ├── InsufficientBalanceError
│   ├── InsufficientLockupError
│   ├── UnbondingPeriodNotElapsedError
│   └── NotEligibleError
│
├── TxError
│   ├── TxRevertError
│   ├── NonceError
│   ├── GasError
│   └── InvalidRpcUrlError
│
├── ConfigError
│   ├── MissingSignerError
│   ├── InvalidSignerError
│   └── ChainNotSupportedError
│
└── IPFSError
    ├── IPFSFetchError
    └── IPFSGatewayError
```

All seven abstract intermediate classes (`NotFoundError`, `StateError`,
`PermissionError`, `VaultError`, `TxError`, `ConfigError`, `IPFSError`)
are catchable themselves — use them to handle a whole domain at once.

## Domain catchers

=== "Not found"

    ```python
    from ogpu.types import NotFoundError
    from ogpu.protocol import Task

    try:
        task = Task.load("0xMAYBE_NOT_THERE")
    except NotFoundError:
        print("no such task")
    ```

=== "State errors"

    ```python
    from ogpu.types import StateError

    try:
        task.cancel(signer=KEY)
    except StateError:
        print("task already canceled / finalized / expired")
    ```

=== "Permissions"

    ```python
    from ogpu.types import PermissionError

    try:
        some_task.cancel(signer=WRONG_KEY)
    except PermissionError as e:
        print(f"not authorized: {e}")
    ```

=== "Vault"

    ```python
    from ogpu.types import VaultError, InsufficientBalanceError

    try:
        vault.lock(10**20, signer=KEY)
    except InsufficientBalanceError as e:
        print(f"short by {e.required - e.available}")
    except VaultError:
        print("other vault failure")
    ```

## Typed fields

Every concrete error carries the data it was raised with — use it for
structured logging:

```python
from ogpu.types import (
    TaskNotFoundError,
    InsufficientBalanceError,
    UnbondingPeriodNotElapsedError,
    MissingSignerError,
)

try:
    Task.load("0x...")
except TaskNotFoundError as e:
    print(e.address)               # the address that wasn't found

try:
    vault.lock(10**20, signer=KEY)
except InsufficientBalanceError as e:
    print(e.account, e.required, e.available)

try:
    vault.claim(signer=KEY)
except UnbondingPeriodNotElapsedError as e:
    print(f"wait {e.remaining_seconds} more seconds")

try:
    client.publish_task(info)        # no CLIENT_PRIVATE_KEY set
except MissingSignerError as e:
    print(f"missing env var for role {e.role}")
```

## Revert decoding

When a transaction reverts on-chain, the SDK catches the underlying
`ContractLogicError`, extracts the revert reason, and looks it up in
`REVERT_PATTERN_MAP`. If the reason matches a known pattern, you get a
typed exception. Otherwise you get a generic `TxRevertError` with the
reason string.

```python
from ogpu.types import TxRevertError

try:
    task.cancel(signer=KEY)
except TxRevertError as e:
    print(f"revert reason: {e.reason}")
```

Known patterns (as of v0.2.1):

| Revert string | Typed error |
|---|---|
| `NotOwner` | `NotTaskOwnerError` or `NotSourceOwnerError` (context-dependent) |
| `NotMaster` | `NotMasterError` |
| `NotProvider` | `NotProviderError` |
| `Expired` | `TaskExpiredError` |
| `AlreadyConfirmed` | `ResponseAlreadyConfirmedError` |
| `AlreadyFinalized` | `TaskAlreadyFinalizedError` |
| `InsufficientBalance` | `InsufficientBalanceError` |
| `InsufficientLockup` | `InsufficientLockupError` |
| `UnbondingNotElapsed` | `UnbondingPeriodNotElapsedError` |
| `NotEligible` | `NotEligibleError` |
| `SourceInactive` | `SourceInactiveError` |

Unknown reasons fall through to `TxRevertError(reason=...)`.

## Nonce errors

Sometimes transactions get stuck in the mempool with a nonce collision
(e.g. two processes signing from the same account). `TxExecutor`
automatically retries on nonce errors, but if that doesn't resolve it,
the recovery tools are in `ogpu.chain.nonce`:

```python
from ogpu import fix_nonce, get_nonce_info, reset_nonce_cache

# See what's going on
info = get_nonce_info()
print(info)
# {'address': '0x...', 'mined_nonce': 42, 'pending_nonce': 45,
#  'cached_nonce': 43, 'has_pending': True, 'pending_count': 3}

# Cancel pending transactions by replacing them with 0-value self-transfers
next_nonce = fix_nonce()
print(f"ready with nonce {next_nonce}")

# Just clear the cache without touching the chain
reset_nonce_cache()
```

`fix_nonce` requires `CLIENT_PRIVATE_KEY` or an explicit `private_key=`
argument since it has to sign cancellation transactions.

## IPFS failures

```python
from ogpu.types import IPFSFetchError, IPFSGatewayError

try:
    payload = response.fetch_data()
except IPFSGatewayError as e:
    print(f"gateway {e.gateway} returned HTTP {e.status_code}")
except IPFSFetchError as e:
    print(f"network or JSON parse failure: {e.reason}")
```

## Next

- [API reference: ogpu.types.errors](../reference/types.md#errors)
- [Nonce management](custom-rpc.md) for stuck transactions
