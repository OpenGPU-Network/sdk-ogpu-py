"""OGPU Python SDK — top-level package.

The SDK is split into:

- ``ogpu.chain``    — ChainConfig, ChainId, Web3Manager, nonce utilities, ABI loader
- ``ogpu.types``    — shared enums, dataclasses, and exceptions
- ``ogpu.ipfs``     — publish and fetch off-chain content
- ``ogpu.protocol`` — low-level, 1:1 with contract ABIs
- ``ogpu.client``   — client-role workflows (publish_source, publish_task, ...)
- ``ogpu.agent``    — agent-role scheduler workflows (register/attempt on behalf of a master)
- ``ogpu.events``   — async event subscriptions (the one async island)
- ``ogpu.service``  — framework for source developers (frozen, out of scope)
"""

from __future__ import annotations

from . import agent, chain, client, events, ipfs, protocol, service, types
from .chain import (
    ChainConfig,
    ChainId,
    clear_all_nonce_caches,
    fix_nonce,
    get_nonce_info,
    reset_nonce_cache,
)
from .ipfs import fetch_ipfs_json, publish_to_ipfs

__all__ = [
    "agent",
    "chain",
    "client",
    "events",
    "ipfs",
    "protocol",
    "service",
    "types",
    "ChainConfig",
    "ChainId",
    "fix_nonce",
    "reset_nonce_cache",
    "clear_all_nonce_caches",
    "get_nonce_info",
    "publish_to_ipfs",
    "fetch_ipfs_json",
]
