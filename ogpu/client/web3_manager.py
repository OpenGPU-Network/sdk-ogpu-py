from typing import Dict, Optional

from web3 import Web3

from .chain_config import ChainConfig, ChainId


class Web3Manager:
    """Manages Web3 instances for different chains"""

    _web3_instances: Dict[ChainId, Web3] = {}

    @classmethod
    def get_web3_instance(cls, chain_id: Optional[ChainId] = None) -> Web3:
        """Get Web3 instance for specified chain or current chain"""
        if chain_id is None:
            chain_id = ChainConfig.get_current_chain()

        # Return cached instance if exists
        if chain_id in cls._web3_instances:
            return cls._web3_instances[chain_id]

        # Get RPC URL for the chain
        rpc_url = cls._get_rpc_url_for_chain(chain_id)

        # Create and cache Web3 instance
        web3_instance = Web3(Web3.HTTPProvider(rpc_url))

        if not web3_instance.is_connected():
            raise ConnectionError(
                f"Failed to connect to {chain_id.name} node at {rpc_url}"
            )

        cls._web3_instances[chain_id] = web3_instance
        return web3_instance

    @classmethod
    def _get_rpc_url_for_chain(cls, chain_id: ChainId) -> str:
        """Get RPC URL for a specific chain"""
        from .config import CHAIN_RPC_URLS

        if chain_id not in CHAIN_RPC_URLS:
            raise ValueError(f"RPC URL not configured for chain {chain_id}")

        rpc_url = CHAIN_RPC_URLS[chain_id]
        if not rpc_url:
            raise ValueError(f"RPC URL for chain {chain_id} is not set")

        return rpc_url

    @classmethod
    def update_rpc_url(cls, chain_id: ChainId, rpc_url: str) -> None:
        """Update RPC URL for a specific chain"""
        from .config import CHAIN_RPC_URLS

        CHAIN_RPC_URLS[chain_id] = rpc_url
        # Clear cached instance to force reconnection
        if chain_id in cls._web3_instances:
            del cls._web3_instances[chain_id]


# Backward compatibility - Web3 instance for current chain
def WEB3():
    return Web3Manager.get_web3_instance()


# For direct access
def get_web3_for_chain(chain_id: ChainId) -> Web3:
    """Get Web3 instance for a specific chain"""
    return Web3Manager.get_web3_instance(chain_id)
