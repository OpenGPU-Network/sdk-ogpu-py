import json
from typing import Any, Dict, Union

import requests
from web3 import Web3
from web3.contract import Contract

from .web3_manager import Web3Manager


def load_contract(address: str, abi: Dict) -> Contract:
    web3 = Web3Manager.get_web3_instance()
    return web3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def publish_to_ipfs(
    data: Union[str, Dict[str, Any]],
    filename: str = "data.json",
    content_type: str = "application/json",
) -> str:
    """
    Publish data to IPFS and return the link.

    Args:
        data: String content or dictionary to be published
        filename: Name of the file (default: "data.json")
        content_type: MIME type of the content (default: "application/json")

    Returns:
        str: IPFS link to the published data

    Raises:
        Exception: If the request fails or response is invalid
    """
    ipfs_api = "https://capi.ogpuscan.io/file/create"

    # Convert data to string if it's a dictionary
    if isinstance(data, dict):
        content = json.dumps(data)
    else:
        content = data

    # Prepare multipart form data
    files = {"file": (filename, content, content_type)}

    # Make the request
    response = requests.post(ipfs_api, files=files)

    # Check response status
    if response.status_code not in [200, 201]:
        raise Exception(f"IPFS API error: {response.status_code} - {response.text}")

    # Parse response
    try:
        ipfs_response = response.json()
        return ipfs_response["link"]
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception(f"IPFS response parsing error: {e}")
