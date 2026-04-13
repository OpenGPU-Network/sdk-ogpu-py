# Changelog

The canonical changelog lives in the repo root at
[`CHANGELOG.md`](https://github.com/OpenGPU-Network/sdk-ogpu-py/blob/main/CHANGELOG.md).
The current release is **v0.2.1**.

## v0.2.1 — highlights

### New features

- **`ogpu.chain`** — new top-level home for `ChainConfig`, `ChainId`,
  `Web3Manager`, `NonceManager`, ABI files, and RPC URL config.
  Role-agnostic, used by every SDK module. `from ogpu import ChainConfig`
  ergonomically re-exports the public surface.
- **`ogpu.ipfs`** — public module (previously `_ipfs`) with
  `publish_to_ipfs` and `fetch_ipfs_json`, top-level re-exported:
  `from ogpu import publish_to_ipfs, fetch_ipfs_json`.
- **Instance classes** — `Source`, `Task`, `Response`, `Provider`,
  `Master` as live stateless proxies bound to contract addresses. Full
  read + write methods and `snapshot()` batch capture.
- **Vault module** (`ogpu.protocol.vault`) — deposit, withdraw, lock,
  unbond, cancel_unbonding, claim, plus 9 reads and 2 constants.
  Previously 0% covered from Python.
- **Event subscription** (`ogpu.events`) — 6 async generators for
  critical Nexus events. The one async island — rest of SDK stays sync.
- **Agent package** (`ogpu.agent`) — scheduler wrappers for agent-role
  operations (`register_to`, `unregister_from`, `attempt`). Uses
  `AGENT_PRIVATE_KEY` env var fallback.
- **Exception hierarchy** — 22 concrete exception classes under
  `OGPUError` base, grouped by domain (NotFound, State, Permission,
  Vault, Tx, Config, IPFS).
- **`TxExecutor`** — unified transaction sender with nonce retry,
  underpriced backoff, and typed revert decoding. Replaces ~300 lines
  of duplicated retry logic.
- **`Receipt` dataclass** — unified return type for all write operations.
- **`ChainConfig.set_rpc / get_rpc / reset_rpc`** — custom RPC endpoint support.
- **Type-safe status enums** — `TaskStatus`, `SourceStatus`,
  `ResponseStatus`, `Environment`, `DeliveryMethod`.
- **`Response.fetch_data()`** — follows the URL returned by
  `response.get_data()` and parses the JSON body.
- **Pagination helper** — transparent internal chunking for all
  list-returning methods.

### Breaking changes

- **`publish_source()` now returns `Source`** (was `str`). Use `.address`
  for the raw address.
- **`publish_task()` now returns `Task`** (was `str`).
- **Default chain flipped to `OGPU_MAINNET`** (was `OGPU_TESTNET`).
  Testnet users must prepend
  `ChainConfig.set_chain(ChainId.OGPU_TESTNET)`.
- **`get_confirmed_response()` standalone function deleted.** Use
  `Task(addr).get_confirmed_response()` instead (chain-only, no HTTP).
- **`get_task_responses()` returns `list[Response]` instances** (was
  list of old dataclass).
- **`ogpu.agent` module previously existed for `set_agent` — that has
  been replaced.** `set_agent` is now at `ogpu.protocol.terminal.set_agent`
  or `ogpu.client.set_agent`; `ogpu.agent` is now the scheduler-role
  high-level package.
- **`ImageMetadata` renamed to `SourceMetadata`.**
- **Old `Response` and `ConfirmedResponse` dataclasses deleted.**
  Replaced by `Response` instance class.
- **`requires-python` bumped to `>=3.10`.**
- **No HTTP dependency for contract reads.** The management-backend
  HTTP call in the old `get_confirmed_response` is removed entirely.
- **Chain infrastructure moved out of `ogpu.client`** (clean break):
    - `from ogpu.client import ChainConfig` → `from ogpu import ChainConfig`
    - `from ogpu.client.chain_config import ChainId` → `from ogpu.chain.config import ChainId`
    - `from ogpu.client import fix_nonce` → `from ogpu import fix_nonce`
    - ABI files moved from `ogpu/client/abis/` to `ogpu/chain/abis/`
- **`SourceInfo.to_source_params` / `TaskInfo.to_task_params` deleted.**
  These type-methods triggered hidden IPFS uploads. The work is now in
  private helpers in `ogpu.client` — user-facing API is unchanged, but
  `SourceInfo` and `TaskInfo` are now pure dataclasses.

See the [full changelog](https://github.com/OpenGPU-Network/sdk-ogpu-py/blob/main/CHANGELOG.md) for every entry.
