import json
import os
from typing import Optional

from web3.contract import Contract

from .chain_config import ChainConfig, ChainId
from .utils import load_contract


class ContractManager:
    """Manages contract instances for the current chain"""

    _nexus_contract = None
    _controller_contract = None
    _terminal_contract = None
    _current_chain = None

    @classmethod
    def _ensure_contracts_loaded(cls):
        """Ensure contracts are loaded for the current chain"""
        current_chain = ChainConfig.get_current_chain()

        if cls._current_chain != current_chain or cls._nexus_contract is None:
            cls._load_contracts_for_chain(current_chain)

    @classmethod
    def _load_contracts_for_chain(cls, chain_id: ChainId):
        """Load contracts for a specific chain"""
        try:
            nexus_address = ChainConfig.get_contract_address("NEXUS")
            controller_address = ChainConfig.get_contract_address("CONTROLLER")
            terminal_address = ChainConfig.get_contract_address("TERMINAL")

            # Load ABIs for current chain
            nexus_abi = ChainConfig.load_abi("NexusAbi")
            controller_abi = ChainConfig.load_abi("ControllerAbi")
            terminal_abi = ChainConfig.load_abi("TerminalAbi")

            cls._nexus_contract = load_contract(nexus_address, nexus_abi)
            cls._controller_contract = load_contract(controller_address, controller_abi)
            cls._terminal_contract = load_contract(terminal_address, terminal_abi)
            cls._current_chain = chain_id

            # Verify contracts were loaded successfully
            if cls._nexus_contract is None:
                raise RuntimeError(f"Failed to load Nexus contract at {nexus_address}")
            if cls._controller_contract is None:
                raise RuntimeError(
                    f"Failed to load Controller contract at {controller_address}"
                )

        except Exception as e:
            raise RuntimeError(f"Failed to load contracts for chain {chain_id}: {e}")

    @classmethod
    def get_nexus_contract(cls) -> Contract:
        """Get the Nexus contract for the current chain"""
        cls._ensure_contracts_loaded()
        if cls._nexus_contract is None:
            raise RuntimeError("Nexus contract is not loaded.")
        return cls._nexus_contract

    @classmethod
    def get_controller_contract(cls) -> Contract:
        """Get the Controller contract for the current chain"""
        cls._ensure_contracts_loaded()
        if cls._controller_contract is None:
            raise RuntimeError("Controller contract is not loaded.")
        return cls._controller_contract

    @classmethod
    def get_terminal_contract(cls) -> Contract:
        """Get the Terminal contract for the current chain"""
        cls._ensure_contracts_loaded()
        if cls._terminal_contract is None:
            raise RuntimeError("Terminal contract is not loaded.")
        return cls._terminal_contract

    # Backward compatibility properties


def NexusContract() -> Contract:
    """Get the Nexus contract for the current chain"""
    return ContractManager.get_nexus_contract()


def ControllerContract() -> Contract:
    """Get the Controller contract for the current chain"""
    return ContractManager.get_controller_contract()


def TerminalContract() -> Contract:
    """Get the Terminal contract for the current chain"""
    return ContractManager.get_terminal_contract()


def load_task_contract(task_address: str) -> Contract:
    """Load a task contract instance for a given address"""
    task_abi = ChainConfig.load_abi("TaskAbi")
    return load_contract(task_address, task_abi)


def load_response_contract(response_address: str) -> Contract:
    """Load a response contract instance for a given address"""
    response_abi = ChainConfig.load_abi("ResponseAbi")
    return load_contract(response_address, response_abi)


# Export the contracts for easy access
__all__ = [
    "NexusContract",
    "ControllerContract",
    "TerminalContract",
    "load_task_contract",
    "load_response_contract",
    "ContractManager",
]
