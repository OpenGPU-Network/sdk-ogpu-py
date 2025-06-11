import json
import os
from typing import Optional

from .chain_config import ChainConfig, ChainId
from .utils import load_contract


class ContractManager:
    """Manages contract instances for the current chain"""

    _nexus_contract = None
    _controller_contract = None
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
        nexus_address = ChainConfig.get_contract_address("NEXUS")
        controller_address = ChainConfig.get_contract_address("CONTROLLER")

        # Load ABIs for current chain
        nexus_abi = ChainConfig.load_abi("NexusAbi")
        controller_abi = ChainConfig.load_abi("ControllerAbi")

        cls._nexus_contract = load_contract(nexus_address, nexus_abi)
        cls._controller_contract = load_contract(controller_address, controller_abi)
        cls._current_chain = chain_id

    @classmethod
    def get_nexus_contract(cls):
        """Get the Nexus contract for the current chain"""
        cls._ensure_contracts_loaded()
        return cls._nexus_contract

    @classmethod
    def get_controller_contract(cls):
        """Get the Controller contract for the current chain"""
        cls._ensure_contracts_loaded()
        return cls._controller_contract

    # Backward compatibility properties


def NexusContract():
    return ContractManager.get_nexus_contract()


def ControllerContract():
    return ContractManager.get_controller_contract()


def load_task_contract(task_address: str):
    """Load a task contract instance for a given address"""
    task_abi = ChainConfig.load_abi("TaskAbi")
    return load_contract(task_address, task_abi)


def load_response_contract(response_address: str):
    """Load a response contract instance for a given address"""
    response_abi = ChainConfig.load_abi("ResponseAbi")
    return load_contract(response_address, response_abi)


# Export the contracts for easy access
__all__ = [
    "NexusContract",
    "ControllerContract",
    "load_task_contract",
    "load_response_contract",
    "ContractManager",
]
