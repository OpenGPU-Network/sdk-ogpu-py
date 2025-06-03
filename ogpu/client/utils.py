from typing import Dict

from web3 import Web3

from .config import WEB3


def load_contract(address: str, abi: Dict):
    return WEB3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
