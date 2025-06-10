import json
import os

from .utils import load_contract

# Get the directory of this module
current_dir = os.path.dirname(os.path.abspath(__file__))
abis_dir = os.path.join(current_dir, "abis")

with open(os.path.join(abis_dir, "NexusAbi.json")) as f:
    NEXUS_ABI = json.load(f)
with open(os.path.join(abis_dir, "ControllerAbi.json")) as f:
    CONTROLLER_ABI = json.load(f)
with open(os.path.join(abis_dir, "TaskAbi.json")) as f:
    TASK_ABI = json.load(f)
with open(os.path.join(abis_dir, "SourceAbi.json")) as f:
    SOURCE_ABI = json.load(f)
with open(os.path.join(abis_dir, "ResponseAbi.json")) as f:
    RESPONSE_ABI = json.load(f)
with open(os.path.join(abis_dir, "VaultAbi.json")) as f:
    VAULT_ABI = json.load(f)
with open(os.path.join(abis_dir, "TerminalAbi.json")) as f:
    TERMINAL_ABI = json.load(f)

NEXUS_CONTRACT_ADDRESS = "0x2fE44Dd99AaC6A17143999DcCA5b074C6ce36812"
CONTROLLER_CONTRACT_ADDRESS = "0x57436474D2624d7F5326F593a899ceaeE9708812"

NexusContract = load_contract(NEXUS_CONTRACT_ADDRESS, NEXUS_ABI)
ControllerContract = load_contract(CONTROLLER_CONTRACT_ADDRESS, CONTROLLER_ABI)


def load_task_contract(task_address: str):
    """Load a task contract instance for a given address"""
    return load_contract(task_address, TASK_ABI)


def load_response_contract(response_address: str):
    """Load a response contract instance for a given address"""
    return load_contract(response_address, RESPONSE_ABI)


# Export the contracts for easy access
__all__ = [
    "NexusContract",
    "ControllerContract",
    "load_task_contract",
    "load_response_contract",
]
