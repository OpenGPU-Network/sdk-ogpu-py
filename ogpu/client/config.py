import json
import os
from typing import Dict

from dotenv import load_dotenv

from .chain_config import ChainId

load_dotenv()

# Chain-specific RPC URLs
CHAIN_RPC_URLS: Dict[ChainId, str] = {
    ChainId.OGPU_MAINNET: "https://mainnet-rpc.ogpuscan.io",
    ChainId.OGPU_TESTNET: "https://testnetrpc.ogpuscan.io",
}

CLIENT_PRIVATE_KEY = os.getenv("CLIENT_PRIVATE_KEY")
