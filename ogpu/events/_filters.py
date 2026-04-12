"""Shared filter creation helpers for event watchers."""

from __future__ import annotations

from typing import Any

from web3 import AsyncWeb3
from web3.contract import AsyncContract

from ..client.chain_config import ChainConfig


async def get_nexus_contract(w3: AsyncWeb3) -> AsyncContract:
    """Load the Nexus contract for async event filtering."""
    address = ChainConfig.get_contract_address("NEXUS")
    abi = ChainConfig.load_abi("NexusAbi")
    return w3.eth.contract(address=w3.to_checksum_address(address), abi=abi)


def _tx_hash_hex(raw: Any) -> str:
    if hasattr(raw, "hex"):
        return str(raw.hex())
    if isinstance(raw, (bytes, bytearray)):
        return raw.hex()
    return str(raw)
