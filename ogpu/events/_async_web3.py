"""Async Web3 singleton — separate from the sync Web3Manager."""

from __future__ import annotations

from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

_instances: dict[str, AsyncWeb3] = {}


async def get_async_web3() -> AsyncWeb3:
    """Return a cached AsyncWeb3 instance for the current chain's RPC URL."""
    from ..client.chain_config import ChainConfig

    url = ChainConfig.get_rpc()

    if url in _instances:
        return _instances[url]

    provider = AsyncHTTPProvider(url)
    w3 = AsyncWeb3(provider)

    connected = await w3.is_connected()
    if not connected:
        raise ConnectionError(f"Async Web3 cannot connect to {url}")

    _instances[url] = w3
    return w3
