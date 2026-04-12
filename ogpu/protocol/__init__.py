"""Low-level protocol layer — 1:1 mirrors of the OGPU contract ABIs.

Instance classes (``Source``, ``Task``, ``Response``) provide live,
stateless proxies to on-chain contracts. Module-level namespaces
(``nexus``, ``controller``, ``terminal``) expose singleton contract writes.
"""

from __future__ import annotations

from . import controller, nexus, terminal, vault
from ._base import (
    REVERT_PATTERN_MAP,
    ZERO_ADDRESS,
    TxExecutor,
    decode_revert,
    load_contract,
)
from ._signer import Signer, resolve_signer
from .response import Response
from .source import Source
from .task import Task

__all__ = [
    # Instance classes
    "Source",
    "Task",
    "Response",
    # Modules
    "nexus",
    "controller",
    "terminal",
    "vault",
    # Shared infrastructure
    "TxExecutor",
    "ZERO_ADDRESS",
    "REVERT_PATTERN_MAP",
    "decode_revert",
    "load_contract",
    "Signer",
    "resolve_signer",
]
