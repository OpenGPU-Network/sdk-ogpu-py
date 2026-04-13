"""Synchronous Web3 instance manager.

``Web3Manager`` caches one ``Web3`` instance per chain so the SDK doesn't
re-create HTTP providers on every contract call. Instances are invalidated
automatically when ``ChainConfig.set_rpc`` changes the endpoint.

You rarely touch ``Web3Manager`` directly — every SDK contract operation
goes through ``TxExecutor`` / ``load_contract`` which call
``Web3Manager.get_web3_instance()`` internally. It's exposed here so you
can reach for the raw ``Web3`` object if you need to do something the
SDK doesn't cover.
"""

from __future__ import annotations

from web3 import Web3

from .config import CHAIN_RPC_URLS, ChainConfig, ChainId


class Web3Manager:
    """Cached ``Web3`` instance pool, keyed by ``ChainId``.

    All methods are classmethods — there's only ever one instance pool
    per process.

    The first ``get_web3_instance(chain)`` call for a given chain creates
    a fresh ``Web3`` with ``Web3.HTTPProvider(rpc_url)`` and probes
    ``is_connected()``. Subsequent calls return the cached instance.

    ``update_rpc_url`` drops the cached instance so the next call
    reconnects — this is how ``ChainConfig.set_rpc`` propagates a new
    RPC URL without a process restart.
    """

    _web3_instances: dict[ChainId, Web3] = {}

    @classmethod
    def get_web3_instance(cls, chain_id: ChainId | None = None) -> Web3:
        """Return the cached ``Web3`` for a chain, creating it on first use.

        Args:
            chain_id: Which chain to get the instance for. Defaults to
                the currently active chain.

        Returns:
            A connected ``Web3`` instance.

        Raises:
            ConnectionError: If the underlying ``HTTPProvider`` fails to
                connect on first creation.
            ValueError: If no RPC URL is configured for the given chain.

        Example:
            ```python
            from ogpu.chain.web3 import Web3Manager
            w3 = Web3Manager.get_web3_instance()
            w3.eth.block_number
            # 12345678
            ```
        """
        if chain_id is None:
            chain_id = ChainConfig.get_current_chain()

        if chain_id in cls._web3_instances:
            return cls._web3_instances[chain_id]

        rpc_url = cls._get_rpc_url_for_chain(chain_id)
        web3_instance = Web3(Web3.HTTPProvider(rpc_url))

        if not web3_instance.is_connected():
            raise ConnectionError(f"Failed to connect to {chain_id.name} node at {rpc_url}")

        cls._web3_instances[chain_id] = web3_instance
        return web3_instance

    @classmethod
    def _get_rpc_url_for_chain(cls, chain_id: ChainId) -> str:
        """Return the configured RPC URL for a chain (from ``CHAIN_RPC_URLS``)."""
        if chain_id not in CHAIN_RPC_URLS:
            raise ValueError(f"RPC URL not configured for chain {chain_id}")
        rpc_url = CHAIN_RPC_URLS[chain_id]
        if not rpc_url:
            raise ValueError(f"RPC URL for chain {chain_id} is not set")
        return rpc_url

    @classmethod
    def update_rpc_url(cls, chain_id: ChainId, rpc_url: str) -> None:
        """Set a new RPC URL for a chain and invalidate the cached instance.

        Called by ``ChainConfig.set_rpc`` and ``ChainConfig.reset_rpc``.
        After this runs, the next ``get_web3_instance(chain_id)`` creates
        a fresh connection against the new URL.

        Args:
            chain_id: The chain to reconfigure.
            rpc_url: The new RPC URL. Not validated here —
                ``ChainConfig.set_rpc`` does the ``is_connected`` probe.
        """
        CHAIN_RPC_URLS[chain_id] = rpc_url
        if chain_id in cls._web3_instances:
            del cls._web3_instances[chain_id]


def WEB3() -> Web3:
    """Return the ``Web3`` instance for the currently active chain.

    Convenience shortcut. Equivalent to
    ``Web3Manager.get_web3_instance()``.

    Returns:
        Connected ``Web3`` instance.

    Example:
        ```python
        from ogpu.chain.web3 import WEB3
        WEB3().eth.block_number
        # 12345678
        ```
    """
    return Web3Manager.get_web3_instance()


def get_web3_for_chain(chain_id: ChainId) -> Web3:
    """Return the ``Web3`` instance for a specific chain.

    Useful when you need to read state on a non-active chain without
    changing the global ``ChainConfig`` state.

    Args:
        chain_id: The chain to get the instance for.

    Returns:
        Connected ``Web3`` instance for that chain.
    """
    return Web3Manager.get_web3_instance(chain_id)
