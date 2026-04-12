# Changelog

## 0.2.1

### New Features

- **Protocol layer** (`ogpu.protocol`) — low-level, 1:1 wrappers for every user-callable contract function across Nexus, Controller, Terminal, and Vault
- **Instance classes** — `Source`, `Task`, `Response`, `Provider`, `Master` as live stateless proxies bound to contract addresses, with full read + write methods and `snapshot()` batch capture
- **Vault module** (`ogpu.protocol.vault`) — deposit, withdraw, lock, unbond, cancel_unbonding, claim + all view functions. Previously 0% coverage from Python
- **Terminal expansion** — announce_master/provider, remove_provider/container, set_base_data/live_data, 8 read functions
- **Provider/Master synthetic classes** — compose Terminal + Vault + Nexus calls into role-scoped instances with convenience wrappers (stake, unstake, claim_earnings, etc.)
- **Event subscription** (`ogpu.events`) — 6 async generators for critical Nexus events: `watch_task_published`, `watch_attempted`, `watch_response_submitted`, `watch_response_status_changed`, `watch_task_status_changed`, `watch_registered`
- **Exception hierarchy** — 22 concrete exception classes under `OGPUError` base, grouped by domain (NotFound, State, Permission, Vault, Tx, Config, IPFS)
- **`TxExecutor`** — unified transaction sender with nonce retry, underpriced backoff, and typed revert decoding. Replaces ~300 lines of duplicated retry logic
- **`Receipt` dataclass** — unified return type for all write operations
- **`ChainConfig.set_rpc` / `get_rpc` / `reset_rpc`** — custom RPC endpoint support
- **Type-safe status enums** — `TaskStatus`, `SourceStatus`, `ResponseStatus`, `Environment`, `DeliveryMethod`
- **Pagination helper** — transparent internal chunking for all list-returning methods

### Breaking Changes

- **`publish_source()` now returns `Source`** (was `str`). Use `.address` for the raw address.
- **`publish_task()` now returns `Task`** (was `str`). Use `.address` for the raw address.
- **Default chain flipped to `OGPU_MAINNET`** (was `OGPU_TESTNET`). Testnet users must prepend `ChainConfig.set_chain(ChainId.OGPU_TESTNET)`.
- **`get_confirmed_response()` standalone function deleted.** Use `Task(addr).get_confirmed_response()` instead (chain-only, no HTTP).
- **`get_task_responses()` returns `list[Response]` instances** (was list of old dataclass).
- **`ogpu.agent` module deleted.** `set_agent` is now at `ogpu.protocol.terminal.set_agent` or `ogpu.client.set_agent`.
- **`ImageMetadata` renamed to `SourceMetadata`.**
- **Old `Response` and `ConfirmedResponse` dataclasses deleted.** Replaced by `Response` instance class.
- **`requires-python` bumped to `>=3.10`.**
- **No HTTP dependency for contract reads.** The management-backend HTTP call in the old `get_confirmed_response` is removed entirely.

### Internal

- New `ogpu/types/` directory: enums, errors, receipt, metadata
- New `ogpu/protocol/` directory: _base, _signer, nexus, controller, terminal, vault, source, task, response, provider, master
- New `ogpu/events/` directory: async event watchers (the one async island)
- `ogpu/agent/` deleted
- `ogpu/client/` simplified to thin re-export wrappers
- `ogpu/service/` untouched
