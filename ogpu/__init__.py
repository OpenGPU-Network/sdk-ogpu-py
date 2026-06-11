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

import importlib
from typing import Any

from . import agent, chain, client, events, ipfs, protocol, types
from ._logging import _apply_env_verbose, set_verbose
from .chain import (
    ChainConfig,
    ChainId,
    clear_all_nonce_caches,
    fix_nonce,
    get_nonce_info,
    reset_nonce_cache,
)
from .ipfs import fetch_ipfs_json, publish_to_ipfs

# ``ogpu.chain`` (imported above) has already run load_dotenv, so a
# ``.env``-provided OGPU_VERBOSE is visible here.
_apply_env_verbose()


def __getattr__(name: str) -> Any:
    # ``ogpu.service`` needs the optional ``ogpu[service]`` extras
    # (fastapi, uvicorn, ...), so it must not be imported eagerly here.
    if name == "service":
        return importlib.import_module(".service", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # "service" is intentionally NOT listed: star-import resolves every
    # __all__ name, which would force the lazy service import (and its
    # optional deps) on users who installed without the [service] extra.
    "agent",
    "chain",
    "client",
    "events",
    "ipfs",
    "protocol",
    "types",
    "ChainConfig",
    "ChainId",
    "fix_nonce",
    "reset_nonce_cache",
    "clear_all_nonce_caches",
    "get_nonce_info",
    "publish_to_ipfs",
    "fetch_ipfs_json",
    "set_verbose",
]
