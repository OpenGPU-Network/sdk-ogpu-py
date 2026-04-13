# Installation

## Requirements

- **Python 3.10+**
- Access to an OpenGPU RPC endpoint (the SDK ships with defaults for mainnet and testnet)
- A funded wallet on the chain you target (testnet tokens for testing)

## Install

=== "pip"

    ```bash
    pip install ogpu
    ```

=== "pip + examples"

    ```bash
    pip install "ogpu[examples]"
    ```

    Adds Jupyter so the scenario notebooks under
    [`examples/scenarios/`](https://github.com/OpenGPU-Network/sdk-ogpu-py/tree/main/examples/scenarios)
    can be opened and re-run locally.

=== "From source"

    ```bash
    git clone https://github.com/OpenGPU-Network/sdk-ogpu-py.git
    cd sdk-ogpu-py
    pip install -e ".[dev]"
    ```

## Verify

```python
import ogpu
print(ogpu.ChainConfig.get_current_chain().name)  # OGPU_MAINNET
print(ogpu.ChainConfig.get_rpc())                 # https://mainnet-rpc.ogpuscan.io
```

If the import succeeds and the RPC URL prints, you're ready.

## Environment variables

The SDK reads private keys from env vars, looked up by role. None are
required at import time — you only need the one matching the role you
act as.

| Variable | Used by | Description |
|---|---|---|
| `CLIENT_PRIVATE_KEY` | `ogpu.client` | Publish sources, publish tasks, confirm responses |
| `PROVIDER_PRIVATE_KEY` | provider-side writes | announce_master, register, attempt, submit_response |
| `MASTER_PRIVATE_KEY` | master-side writes | announce_provider, remove_provider, set_agent |
| `AGENT_PRIVATE_KEY` | `ogpu.agent` | Scheduler role delegated by a master |

The SDK searches for a `.env` file in this order on import:

1. Current working directory (`./.env`)
2. User home (`~/.env`)
3. SDK install directory (fallback)

Any values already set in the environment take precedence.

!!! tip "Vault operations need explicit signers"
    Vault writes (`deposit`, `withdraw`, `lock`, `unbond`, `claim`,
    `cancel_unbonding`) require `signer=` as a keyword argument. There is
    no env-var fallback — this is intentional, to prevent accidental
    deposit/withdraw from the wrong account.

## Pick a chain

Default chain is **mainnet**. Switch to testnet explicitly:

```python
from ogpu import ChainConfig, ChainId

ChainConfig.set_chain(ChainId.OGPU_TESTNET)
```

For a custom RPC endpoint (private node, local fork), see
[custom RPC](../guides/custom-rpc.md).

## Next

- [Quickstart](quickstart.md) — publish and confirm a task in a handful of lines
- [Concepts](concepts.md) — how the packages and layers fit together
