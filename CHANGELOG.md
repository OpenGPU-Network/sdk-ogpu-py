# Changelog

## 0.2.1

### New Features

- **Chain package** (`ogpu.chain`) — new top-level home for `ChainConfig`, `ChainId`, `Web3Manager`, `NonceManager`, ABI files, and RPC URL config. Role-agnostic, used by every SDK module. `from ogpu import ChainConfig` ergonomically re-exports the public surface.
- **IPFS public module** (`ogpu.ipfs`) — `publish_to_ipfs` and `fetch_ipfs_json` are now public and top-level re-exported: `from ogpu import publish_to_ipfs, fetch_ipfs_json`. Providers publishing real compute output and clients fetching confirmed response payloads can use them directly without reaching into private modules.
- **`Response.fetch_data()`** — new convenience method that follows the URL returned by `response.get_data()` and parses the JSON payload. Naming follows A2: `get_*` is cheap/local, `fetch_*` is network I/O.
- **Side-effect-free types** — `SourceInfo.to_source_params()` and `TaskInfo.to_task_params()` deleted. These were type-method calls that triggered hidden IPFS uploads, violating the layering rule that `ogpu.types` is a pure-data leaf package. The IPFS upload + params assembly is now in private `_build_source_params` / `_build_task_params` helpers inside `ogpu/client/__init__.py`. User-facing API is unchanged — `client.publish_source(info)` / `client.publish_task(info)` still do the right thing — but `SourceInfo` and `TaskInfo` are now pure dataclasses you can pass around without surprising side effects.
- **Agent package** (`ogpu.agent`) — high-level wrappers for the agent scheduler role: `register_to`, `unregister_from`, `attempt`. Each signs with the agent's key and passes the target provider address explicitly. Uses `AGENT_PRIVATE_KEY` env var fallback via new `Role.AGENT`. `submit_response` is intentionally absent — agents schedule work, they don't produce responses. Master and Provider high-level wrappers are NOT added in v0.2.1 — the existing `Master(addr)` / `Provider(addr)` synthetic classes already cover those roles cleanly.
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
- **Chain infrastructure moved out of `ogpu.client`** (decision O4). Clean break — no compatibility shims:
  - `from ogpu.client import ChainConfig` → `from ogpu import ChainConfig` (or `from ogpu.chain import ChainConfig`)
  - `from ogpu.client import ChainId` → `from ogpu import ChainId`
  - `from ogpu.client import fix_nonce, reset_nonce_cache, clear_all_nonce_caches, get_nonce_info` → `from ogpu import fix_nonce, ...`
  - `from ogpu.client.chain_config import ChainConfig` → `from ogpu.chain.config import ChainConfig`
  - `from ogpu.client.nonce_manager import NonceManager` → `from ogpu.chain.nonce import NonceManager`
  - `from ogpu.client.web3_manager import Web3Manager` → `from ogpu.chain.web3 import Web3Manager`
  - ABI files moved from `ogpu/client/abis/` to `ogpu/chain/abis/`
  - `ogpu.client` now contains only client-role workflows (publish_source, publish_task, confirm_response, set_agent, cancel_task, update_source, inactivate_source, get_task_responses)

### Internal

- New `ogpu/chain/` directory: config, web3, nonce (merged from old client/chain_config.py + config.py + web3_manager.py + nonce_manager.py + nonce_utils.py), abis/
- New `ogpu/types/` directory: enums, errors, receipt, metadata
- New `ogpu/protocol/` directory: _base, _signer, nexus, controller, terminal, vault, source, task, response, provider, master
- New `ogpu/events/` directory: async event watchers (the one async island)
- `ogpu/agent/` deleted
- `ogpu/client/` trimmed to client-role workflows only
- `ogpu/service/` untouched
