# Custom RPC endpoints

By default the SDK connects to OpenGPU's public RPC nodes:

| Chain | Default URL |
|---|---|
| Mainnet | `https://mainnet-rpc.ogpuscan.io` |
| Testnet | `https://testnetrpc.ogpuscan.io` |

If you run your own node, use a private provider, or want to point at
a local fork (Anvil, Foundry, Hardhat), override per chain.

## Setting a custom RPC

```python
from ogpu import ChainConfig, ChainId

ChainConfig.set_rpc("https://my-private-node.example:8545")
```

`set_rpc` validates connectivity before committing (via
`Web3.is_connected()`) and raises `InvalidRpcUrlError` if the endpoint
is unreachable. It also invalidates any cached Web3 instance so the
next SDK call reconnects with the new URL.

Target a specific chain explicitly:

```python
ChainConfig.set_rpc("http://localhost:8545", chain=ChainId.OGPU_TESTNET)
```

## Reading the current URL

```python
url = ChainConfig.get_rpc()                         # current chain
url_testnet = ChainConfig.get_rpc(ChainId.OGPU_TESTNET)
```

## Resetting to the default

```python
ChainConfig.reset_rpc()                             # current chain
ChainConfig.reset_rpc(ChainId.OGPU_TESTNET)         # specific chain
```

## Local fork workflow

Quick setup for integration testing against a local fork:

```python
from ogpu import ChainConfig, ChainId
from ogpu.client import publish_task, TaskInfo, TaskInput
import time

# Start anvil in another terminal:
#   anvil --fork-url https://testnetrpc.ogpuscan.io

ChainConfig.set_chain(ChainId.OGPU_TESTNET)
ChainConfig.set_rpc("http://127.0.0.1:8545")

# Now every SDK call hits the fork — no real state changes
task = publish_task(TaskInfo(
    source="0x...",
    config=TaskInput(function_name="predict", data={"x": 1}),
    expiryTime=int(time.time()) + 3600,
    payment=10**16,
))
```

You can reset to live testnet at any time:

```python
ChainConfig.reset_rpc()
```

## Errors

```python
from ogpu.types import InvalidRpcUrlError, ChainNotSupportedError

try:
    ChainConfig.set_rpc("https://bad-url.example")
except InvalidRpcUrlError as e:
    print(f"unreachable: {e.url}")

try:
    ChainConfig.set_rpc("http://localhost:8545", chain=some_unsupported)
except ChainNotSupportedError as e:
    print(f"unknown chain: {e.chain_id}")
```

## Next

- [Nonce recovery](errors.md#nonce-errors) — for when transactions get stuck
- [API reference: ogpu.chain](../reference/chain.md)
