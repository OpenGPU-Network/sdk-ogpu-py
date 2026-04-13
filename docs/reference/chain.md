# `ogpu.chain`

Shared chain infrastructure — the layer every other module imports
from. Owns the chain selection state, the RPC URL configuration, the
Web3 instance cache, the nonce management singleton, and the ABI
loader.

The package is a **leaf** in the SDK dependency graph: `ogpu.types`,
`ogpu.protocol`, `ogpu.client`, and friends all depend on `ogpu.chain`,
but nothing in `ogpu.chain` imports from higher layers. This is why
switching chains in `ChainConfig` transparently affects every other
module without coordination.

Public surface is re-exported at the top level for ergonomics:

```python
from ogpu import ChainConfig, ChainId
from ogpu import fix_nonce, reset_nonce_cache, clear_all_nonce_caches, get_nonce_info
```

You only need to import from `ogpu.chain.*` directly when you want
the low-level classes (`Web3Manager`, `NonceManager`) or the per-chain
RPC URL dict (`CHAIN_RPC_URLS`).

---



## ChainId

::: ogpu.chain.config.ChainId
    options:
      show_root_heading: true
      heading_level: 3
      members: []

## ChainConfig

::: ogpu.chain.config.ChainConfig.set_chain
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.get_current_chain
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.get_contract_address
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.get_all_supported_chains
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.set_rpc
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.get_rpc
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.reset_rpc
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.config.ChainConfig.load_abi
    options:
      show_root_heading: true
      heading_level: 3

## Nonce management

::: ogpu.chain.nonce.fix_nonce
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.nonce.get_nonce_info
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.nonce.reset_nonce_cache
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.chain.nonce.clear_all_nonce_caches
    options:
      show_root_heading: true
      heading_level: 3

## Web3 access

::: ogpu.chain.web3.Web3Manager
    options:
      show_root_heading: true
      heading_level: 3
