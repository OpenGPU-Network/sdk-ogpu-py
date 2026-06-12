# Changelog

## 0.2.3

Bounded & typed task-publish path: every leg of `publish_task` (IPFS pin, send, receipt wait) is now time-bounded, configurable, and fails with a typed error.

### New Features

- **IPFS pin retry** — `publish_to_ipfs(..., retries=2, backoff=0.5)`: transient failures (connection error, timeout, 5xx) are retried with exponential backoff; 4xx and malformed bodies fail immediately without retry. Reachable from `publish_task` via `ipfs_timeout=` / `ipfs_retries=` / `ipfs_backoff=` — the pin still happens exactly once per call.
- **Bounded receipt wait** — `publish_task(..., receipt_timeout=120)` caps `wait_for_transaction_receipt` explicitly (never web3's implicit default) and raises `TxReceiptTimeoutError` on expiry. The error carries `tx_hash`: the transaction WAS broadcast and may still be mined — reconcile before retrying.
- **Total publish budget** — `publish_task(..., total_timeout=B)`: one budget covering pin (incl. retries) + send + receipt. The call returns or raises within `B`; the transaction is never broadcast once the budget is exhausted (`PublishTimeoutError`, no gas spent), and the receipt wait is capped by the remaining budget.
- **Typed errors on every leg** — no raw `requests`/`web3` exception escapes `publish_task`. New types: `TxReceiptTimeoutError`, `TxRpcError` (unmapped RPC/transport failures, original chained as `__cause__`), `PublishTimeoutError`. Transient RPC blips observed on mainnet under load (`block 0x... not found` from lagging replicas, dropped connections) are retried once before `TxRpcError` is raised — post-broadcast transport errors are never retried (a blind re-send could double-publish).

### Notes

- Defaults: `ipfs_timeout=30`, `ipfs_retries=2`, `ipfs_backoff=0.5`, `receipt_timeout=120`, `total_timeout=None` (budget opt-in). All knobs are per-call keyword args.
- `private_key=` (raw hex) stays accepted on `publish_task`.
- All 0.2.2 import paths and dependency ranges unchanged.

## 0.2.2

### New Features

- **Verbose logging** (`ogpu.set_verbose()` / `OGPU_VERBOSE=1`) — the SDK now logs through the standard `logging` module under the `ogpu` namespace (`ogpu.ipfs`, `ogpu.tx`). Silent by default (`NullHandler`); `set_verbose()` attaches a millisecond-timestamped stderr handler. IPFS uploads/fetches and every transaction stage (build, send, receipt wait) report durations, and previously-silent nonce/underpriced retries are logged as warnings — so you can see at a glance whether a slow `publish_task` is losing time in IPFS or RPC. The env var also works from `.env`.
- **Late-publish guard** — `publish_task` now refuses to send the transaction when the task's `expiryTime` has already passed, checked both before the IPFS upload and right before the transaction. A stalled pin can no longer produce an orphaned on-chain task (published late, 0 attempters, gas wasted). Raises `TaskExpiredError` and logs a warning under `ogpu.client`.
- **Configurable IPFS timeouts** — `publish_to_ipfs` and `fetch_ipfs_json` accept a `timeout` keyword (default 30s, unchanged).

### Bug Fixes

- **Concurrent writes from one account collided on nonces** — `NonceManager.get_nonce` returned the cached value without advancing it (the increment happened only after the receipt), so concurrent `publish_task` calls from the same signer grabbed the same nonce and failed with `replacement transaction underpriced`. Measured on mainnet: 50% failure at 20 concurrent publishes. `TxExecutor` now allocates through the new `NonceManager.reserve_nonce`, which hands out the nonce and advances the cache in one atomic step; pre-broadcast failures reset the cache so leaked reservations get re-read from chain. After the fix: 20/20 concurrent publishes, zero retries. `increment_nonce` remains for backward compatibility but is no longer used by `TxExecutor`.

- **Paginated reads panicked on real chain data** — `_paginated_call` assumed the on-chain getters take an exclusive upper bound, but the deployed contracts treat both bounds as inclusive, so every full-range read (`get_responses()`, `get_attempters()`, `get_confirmed_response()`, `Source.get_tasks()`, ...) reverted with `Panic 0x32: array out of bounds`. The helper now translates the SDK's half-open `[lower, upper)` range to inclusive contract bounds. Additionally, the `Source` contract's getters (`getTasks`, `getRegistrants`) panic whenever `lower > 0` — those reads now fetch from index 0 in a single call and slice client-side (`fetch_from_zero`). Verified against deployed mainnet contracts.

### Changed

- **Dependency pins relaxed** — `pyproject.toml` no longer pins exact versions (`==`). Core dependencies now use compatible ranges (`pydantic>=2.11,<3`, `web3>=7.12,<8`, ...), so the SDK no longer forces resolver conflicts or downgrades in user environments.
- **Service deps moved to an extra** — `fastapi`, `uvicorn`, `sentry_sdk`, and `colorama` are only used by `ogpu.service` and are no longer installed by default. Source developers who serve handlers should install `pip install "ogpu[service]"`. `import ogpu` works without them; accessing `ogpu.service` without the extra raises an `ImportError` with install instructions.
- **`requirements.txt` removed** — it duplicated (and contradicted) `pyproject.toml`. The package metadata is the single source of truth; contributors use `pip install -e ".[dev]"`.
- **`ogpu.service` logger renamed to `"ogpu.service"`** (was `"ogpu"`) — the service module's colorized handler and INFO level now live on a child logger instead of fighting the SDK-wide `"ogpu"` root that `set_verbose()` manages. `ogpu.service.logger` keeps working unchanged; only code that did `logging.getLogger("ogpu")` expecting the service handler needs the new name.
- **`service` removed from `ogpu.__all__`** — `from ogpu import *` no longer forces the optional service import; access `ogpu.service` (lazy) or `import ogpu.service` explicitly.

## 0.2.1

### New Features

- **Chain package** (`ogpu.chain`) — new top-level home for `ChainConfig`, `ChainId`, `Web3Manager`, `NonceManager`, ABI files, and RPC URL config. Role-agnostic, used by every SDK module. `from ogpu import ChainConfig` ergonomically re-exports the public surface.
- **IPFS public module** (`ogpu.ipfs`) — `publish_to_ipfs` and `fetch_ipfs_json` are now public and top-level re-exported: `from ogpu import publish_to_ipfs, fetch_ipfs_json`. Providers publishing real compute output and clients fetching confirmed response payloads can use them directly without reaching into private modules.
- **`Response.fetch_data()`** — new convenience method that follows the URL returned by `response.get_data()` and parses the JSON payload. Naming follows A2: `get_*` is cheap/local, `fetch_*` is network I/O.
- **Side-effect-free types** — `SourceInfo.to_source_params()` and `TaskInfo.to_task_params()` deleted. These were type-method calls that triggered hidden IPFS uploads, violating the layering rule that `ogpu.types` is a pure-data leaf package. The IPFS upload + params assembly is now in private `_build_source_params` / `_build_task_params` helpers inside `ogpu/client/__init__.py`. User-facing API is unchanged — `client.publish_source(info)` / `client.publish_task(info)` still do the right thing — but `SourceInfo` and `TaskInfo` are now pure dataclasses you can pass around without surprising side effects.
- **Agent package** (`ogpu.agent`) — high-level wrappers for the agent scheduler role: `register_to`, `unregister_from`, `attempt`. Each signs with the agent's key and passes the target provider address explicitly. Uses `AGENT_PRIVATE_KEY` env var fallback via new `Role.AGENT`. Master and Provider high-level wrappers are NOT added in v0.2.1 — the existing `Master(addr)` / `Provider(addr)` synthetic classes already cover those roles cleanly.
- **Protocol layer** (`ogpu.protocol`) — low-level, 1:1 wrappers for every user-callable contract function across Nexus, Controller, Terminal, and Vault
- **Instance classes** — `Source`, `Task`, `Response`, `Provider`, `Master` as live stateless proxies bound to contract addresses, with full read + write methods and `snapshot()` batch capture
- **Vault module** (`ogpu.protocol.vault`) — deposit, withdraw, lock, unbond, cancel_unbonding, claim + all view functions. Previously 0% coverage from Python
- **Terminal expansion** — announce_master/provider, remove_provider/container, set_default_agent_disabled, 8 read functions
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
- **Provider-app responsibilities removed from the SDK** — `Nexus.submitResponse`, `Terminal.setBaseData`, and `Terminal.setLiveData` are no longer wrapped in `ogpu.protocol`, `ogpu.client`, `ogpu.agent`, or the `Provider` instance class. These three calls produce on-chain claims about compute output (`submitResponse`) or self-reported provider state (`setBaseData` / `setLiveData`) that only the running provider runtime can honestly make. Exposing them as plain SDK calls would let any provider key fabricate responses or capacity claims from arbitrary scripts. They live only inside the docker source runtime now. Read-side equivalents (`get_base_data_of`, `get_live_data_of`, `Response.get_data` / `fetch_data`, `Response.get_params`) remain — only the writes were removed.
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
