import json
import os
from enum import Enum
from typing import Dict, Optional


class ChainId(Enum):
    OGPU_MAINNET = 1071
    OGPU_TESTNET = 200820172034


class ChainConfig:
    """Manages chain-specific configuration and contract addresses"""

    # Contract addresses for each chain
    CHAIN_CONTRACTS: Dict[ChainId, Dict[str, str]] = {
        ChainId.OGPU_TESTNET: {
            "NEXUS": "0xF87bb2f3edB991a998992f14d35fE142e6Bb50b1",
            "CONTROLLER": "0x9fb6022074Fd7Bdb429de0776eb693cA0CB55E09",
            "TERMINAL": "0x1ea332Fc14a5AFD3AF3852B45C263Ab5b1Dd6f52",
        },
        ChainId.OGPU_MAINNET: {
            "NEXUS": "0x2b0cC6058313801D5feb184a539e3a0C5A87a6a1",
            "CONTROLLER": "0x8661F4B9c30e07A04d795A192478dfD905625a1D",
            "TERMINAL": "0xaEBC7b712D38Fc4d841f0732c21B8774339869D3",
        },
    }

    # Chain directory mapping
    CHAIN_DIRECTORIES: Dict[ChainId, str] = {
        ChainId.OGPU_TESTNET: "testnet",
        ChainId.OGPU_MAINNET: "mainnet",
    }

    _current_chain: Optional[ChainId] = ChainId.OGPU_TESTNET
    _loaded_abis: Dict[ChainId, Dict[str, dict]] = {}

    @classmethod
    def set_chain(cls, chain_id: ChainId) -> None:
        """Set the current active chain"""
        if chain_id not in cls.CHAIN_CONTRACTS:
            raise ValueError(f"Chain {chain_id} is not supported")
        cls._current_chain = chain_id

    @classmethod
    def get_current_chain(cls) -> ChainId:
        """Get the current active chain"""
        if cls._current_chain is None:
            raise ValueError("No chain has been set. Call set_chain() first.")
        return cls._current_chain

    @classmethod
    def get_contract_address(cls, contract_name: str) -> str:
        """Get contract address for the current chain"""
        current_chain = cls.get_current_chain()

        if current_chain not in cls.CHAIN_CONTRACTS:
            raise ValueError(f"Chain {current_chain} is not configured")

        chain_contracts = cls.CHAIN_CONTRACTS[current_chain]
        if contract_name not in chain_contracts:
            raise ValueError(
                f"Contract {contract_name} not found for chain {current_chain}"
            )

        return chain_contracts[contract_name]

    @classmethod
    def get_all_supported_chains(cls) -> list[ChainId]:
        """Get list of all supported chains"""
        return list(cls.CHAIN_CONTRACTS.keys())

    @classmethod
    def get_chain_abi_directory(cls) -> str:
        """Get the ABI directory path for the current chain"""
        current_chain = cls.get_current_chain()
        if current_chain not in cls.CHAIN_DIRECTORIES:
            raise ValueError(f"Chain directory not configured for {current_chain}")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "abis", cls.CHAIN_DIRECTORIES[current_chain])

    @classmethod
    def load_abi(cls, abi_name: str) -> dict:
        """Load ABI for the current chain"""
        current_chain = cls.get_current_chain()

        # Check if ABI is already loaded for this chain
        if (
            current_chain in cls._loaded_abis
            and abi_name in cls._loaded_abis[current_chain]
        ):
            return cls._loaded_abis[current_chain][abi_name]

        # Load ABI from file
        abi_dir = cls.get_chain_abi_directory()
        abi_file_path = os.path.join(abi_dir, f"{abi_name}.json")

        if not os.path.exists(abi_file_path):
            raise FileNotFoundError(f"ABI file not found: {abi_file_path}")

        with open(abi_file_path, "r") as f:
            abi_data = json.load(f)

        # Cache the loaded ABI
        if current_chain not in cls._loaded_abis:
            cls._loaded_abis[current_chain] = {}
        cls._loaded_abis[current_chain][abi_name] = abi_data

        return abi_data
