"""Low-level protocol layer — 1:1 mirrors of the OGPU contract ABIs.

Phase 1 ships the scaffolding: ``TxExecutor`` + shared helpers in ``_base``,
the signer resolver in ``_signer``, and minimal write wrappers on
``nexus``, ``controller``, and ``terminal``. Instance classes (``Source``,
``Task``, ``Response``, ``Provider``, ``Master``) land in Phase 2+.
"""

from __future__ import annotations

from . import controller, nexus, terminal
from ._base import (
    REVERT_PATTERN_MAP,
    ZERO_ADDRESS,
    TxExecutor,
    decode_revert,
    load_contract,
)
from ._signer import Signer, resolve_signer

__all__ = [
    # Modules
    "nexus",
    "controller",
    "terminal",
    # Shared infrastructure
    "TxExecutor",
    "ZERO_ADDRESS",
    "REVERT_PATTERN_MAP",
    "decode_revert",
    "load_contract",
    "Signer",
    "resolve_signer",
]
