import json

from .utils import load_contract

with open("abis/NexusAbi.json") as f:
    NEXUS_ABI = json.load(f)
with open("abis/ControllerAbi.json") as f:
    CONTROLLER_ABI = json.load(f)

NEXUS_CONTRACT_ADDRESS = "0x731329542F2dABC433f84BF0498791999D03FfBE"
CONTROLLER_CONTRACT_ADDRESS = "0xeb45d738E8c59BFa30bf6109340ccbb41469eedA"


NexusContract = load_contract(NEXUS_CONTRACT_ADDRESS, NEXUS_ABI)
ControllerContract = load_contract(CONTROLLER_CONTRACT_ADDRESS, CONTROLLER_ABI)

# Export the contracts for easy access
__all__ = ["NexusContract", "ControllerContract"]
