"""Chain selection and RPC configuration.

``ChainConfig`` is a process-wide global that holds the currently active
chain, the RPC URL for each chain, and the ABI/contract-address mappings.
Default chain is ``OGPU_MAINNET`` (flipped from TESTNET in v0.2.1 per
decision F1 / N3).

Users who want a different RPC endpoint (private node, local fork) call
``ChainConfig.set_rpc(url)`` — this delegates to ``Web3Manager.update_rpc_url``
and invalidates the cached Web3 instance so the next call reconnects.
"""

from __future__ import annotations

import json
import os
from enum import Enum

from web3 import Web3

from ..types.errors import ChainNotSupportedError, InvalidRpcUrlError


class ChainId(Enum):
    """Supported blockchain networks."""

    OGPU_MAINNET = 1071
    OGPU_TESTNET = 200820172034


class ChainConfig:
    """Global chain configuration. Thread-safe for read-mostly workloads."""

    CHAIN_CONTRACTS: dict[ChainId, dict[str, str]] = {
        ChainId.OGPU_TESTNET: {
            "NEXUS": "0xF87bb2f3edB991a998992f14d35fE142e6Bb50b1",
            "CONTROLLER": "0x9fb6022074Fd7Bdb429de0776eb693cA0CB55E09",
            "TERMINAL": "0x1ea332Fc14a5AFD3AF3852B45C263Ab5b1Dd6f52",
            "VAULT": "0x15905a2FbD3EF5d3532b931b5656BB9EB493Bb15",
        },
        ChainId.OGPU_MAINNET: {
            "NEXUS": "0x2b0cC6058313801D5feb184a539e3a0C5A87a6a1",
            "CONTROLLER": "0x8661F4B9c30e07A04d795A192478dfD905625a1D",
            "TERMINAL": "0xaEBC7b712D38Fc4d841f0732c21B8774339869D3",
            "VAULT": "0xa5c582254AA313528898311362bc698b041580cC",
        },
    }

    CHAIN_DIRECTORIES: dict[ChainId, str] = {
        ChainId.OGPU_TESTNET: "testnet",
        ChainId.OGPU_MAINNET: "mainnet",
    }

    _DEFAULT_RPC_URLS: dict[ChainId, str] = {
        ChainId.OGPU_MAINNET: "https://mainnet-rpc.ogpuscan.io",
        ChainId.OGPU_TESTNET: "https://testnetrpc.ogpuscan.io",
    }

    _current_chain: ChainId | None = ChainId.OGPU_MAINNET
    _loaded_abis: dict[ChainId, dict[str, object]] = {}

    # ------------------------------------------------------------------ #
    # Chain selection
    # ------------------------------------------------------------------ #

    @classmethod
    def set_chain(cls, chain_id: ChainId) -> None:
        """Switch the globally-active chain."""
        if chain_id not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=chain_id)
        cls._current_chain = chain_id

    @classmethod
    def get_current_chain(cls) -> ChainId:
        if cls._current_chain is None:
            raise ChainNotSupportedError(chain_id=None)
        return cls._current_chain

    @classmethod
    def get_contract_address(cls, contract_name: str) -> str:
        current = cls.get_current_chain()
        if current not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=current)
        contracts = cls.CHAIN_CONTRACTS[current]
        if contract_name not in contracts:
            raise ValueError(f"Contract {contract_name} not configured for chain {current}")
        return contracts[contract_name]

    @classmethod
    def get_all_supported_chains(cls) -> list[ChainId]:
        return list(cls.CHAIN_CONTRACTS.keys())

    # ------------------------------------------------------------------ #
    # ABI loading
    # ------------------------------------------------------------------ #

    @classmethod
    def get_chain_abi_directory(cls) -> str:
        current = cls.get_current_chain()
        if current not in cls.CHAIN_DIRECTORIES:
            raise ChainNotSupportedError(chain_id=current)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "abis", cls.CHAIN_DIRECTORIES[current])

    @classmethod
    def load_abi(cls, abi_name: str) -> object:
        current = cls.get_current_chain()
        if current in cls._loaded_abis and abi_name in cls._loaded_abis[current]:
            return cls._loaded_abis[current][abi_name]

        abi_path = os.path.join(cls.get_chain_abi_directory(), f"{abi_name}.json")
        if not os.path.exists(abi_path):
            raise FileNotFoundError(f"ABI file not found: {abi_path}")

        with open(abi_path) as fh:
            abi_data: object = json.load(fh)

        cls._loaded_abis.setdefault(current, {})[abi_name] = abi_data
        return abi_data

    # ------------------------------------------------------------------ #
    # RPC configuration (new in v0.2.1 — decision F2)
    # ------------------------------------------------------------------ #

    @classmethod
    def set_rpc(cls, url: str, chain: ChainId | None = None) -> None:
        """Override the RPC URL for a given chain (default: current chain).

        Validates connectivity via ``Web3.is_connected`` before committing.
        Raises ``InvalidRpcUrlError`` if the URL is unreachable or invalid.
        Invalidates any cached Web3 instance so the next call reconnects.
        """
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=target)

        probe = Web3(Web3.HTTPProvider(url))
        try:
            reachable = probe.is_connected()
        except Exception as exc:  # noqa: BLE001 — treated as unreachable
            raise InvalidRpcUrlError(url=url) from exc
        if not reachable:
            raise InvalidRpcUrlError(url=url)

        from .web3_manager import Web3Manager

        Web3Manager.update_rpc_url(target, url)

    @classmethod
    def get_rpc(cls, chain: ChainId | None = None) -> str:
        """Return the current RPC URL for a chain (current chain if omitted)."""
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=target)
        from .config import CHAIN_RPC_URLS

        return CHAIN_RPC_URLS[target]

    @classmethod
    def reset_rpc(cls, chain: ChainId | None = None) -> None:
        """Restore the built-in default RPC URL for a chain."""
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls._DEFAULT_RPC_URLS:
            raise ChainNotSupportedError(chain_id=target)
        from .web3_manager import Web3Manager

        Web3Manager.update_rpc_url(target, cls._DEFAULT_RPC_URLS[target])
