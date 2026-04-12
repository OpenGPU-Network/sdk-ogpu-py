"""OGPU Python SDK — top-level package.

The SDK is split into:

- ``ogpu.protocol`` — low-level, 1:1 with contract ABIs (v0.2.1 scaffolding)
- ``ogpu.client`` — client-role workflows (transitional in v0.2.1)
- ``ogpu.service`` — framework for source developers (frozen, out of scope)
- ``ogpu.types`` — shared enums, dataclasses, and exceptions
"""

from __future__ import annotations

from . import client, protocol, service, types
from .client.chain_config import ChainConfig, ChainId

__all__ = [
    "client",
    "protocol",
    "service",
    "types",
    "ChainConfig",
    "ChainId",
]
