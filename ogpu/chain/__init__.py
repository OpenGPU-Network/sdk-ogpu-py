"""Chain infrastructure — shared by every SDK module that touches the chain.

Loads .env files at import time (working dir, home, SDK dir) so
``CLIENT_PRIVATE_KEY``, ``PROVIDER_PRIVATE_KEY``, etc. are available before
any ``resolve_signer`` call. Re-exports the public chain surface.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    """Load .env files in priority order: cwd → home → SDK dir."""
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_environment()


from .config import CHAIN_RPC_URLS, ChainConfig, ChainId  # noqa: E402
from .nonce import (  # noqa: E402
    NonceManager,
    clear_all_nonce_caches,
    fix_nonce,
    get_nonce_info,
    reset_nonce_cache,
)
from .web3 import WEB3, Web3Manager, get_web3_for_chain  # noqa: E402

__all__ = [
    "ChainConfig",
    "ChainId",
    "CHAIN_RPC_URLS",
    "Web3Manager",
    "WEB3",
    "get_web3_for_chain",
    "NonceManager",
    "fix_nonce",
    "reset_nonce_cache",
    "clear_all_nonce_caches",
    "get_nonce_info",
]
