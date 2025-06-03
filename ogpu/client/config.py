import json
import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

WEB3_RPC_URL = os.getenv("WEB3_RPC_URL")
if not WEB3_RPC_URL:
    raise ValueError("`WEB3_RPC_URL` environment variable is not set.")

CLIENT_PRIVATE_KEY = os.getenv("CLIENT_PRIVATE_KEY")

# Web3 instance
WEB3 = Web3(Web3.HTTPProvider(WEB3_RPC_URL))
if not WEB3.is_connected():
    raise ConnectionError("Failed to connect to the node at the provided RPC URL.")
