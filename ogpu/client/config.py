import json
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

from .chain_config import ChainId


def _load_environment():
    """Load environment variables from .env files in priority order:
    1. Current working directory (.env)
    2. User's home directory (.env)
    3. SDK directory (.env)
    """
    env_paths = [
        # Current working directory (user's project)
        Path.cwd() / ".env",
        # User's home directory
        Path.home() / ".env",
        # SDK directory (fallback)
        Path(__file__).parent.parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override already set values


_load_environment()

# Chain-specific RPC URLs
CHAIN_RPC_URLS: Dict[ChainId, str] = {
    ChainId.OGPU_MAINNET: "https://mainnet-rpc.ogpuscan.io",
    ChainId.OGPU_TESTNET: "https://testnetrpc.ogpuscan.io",
}

CLIENT_PRIVATE_KEY = os.getenv("CLIENT_PRIVATE_KEY")


def get_private_key() -> str:
    """Get the CLIENT_PRIVATE_KEY with helpful error message if not found."""
    private_key = os.getenv("CLIENT_PRIVATE_KEY")
    if not private_key:
        raise ValueError(
            "CLIENT_PRIVATE_KEY environment variable is not set. "
            "Please create a .env file in your project directory with:\n"
            "CLIENT_PRIVATE_KEY=your_private_key_here\n\n"
            "The SDK will look for .env files in the following order:\n"
            "1. Current working directory (.env)\n"
            "2. User's home directory (~/.env)\n"
            "3. SDK installation directory (.env)"
        )
    return private_key
