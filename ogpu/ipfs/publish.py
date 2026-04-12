"""Upload off-chain content to the OGPU IPFS pinning service.

The publish endpoint is OGPU-specific (``capi.ogpuscan.io``). It returns a
gateway URL that any standard IPFS gateway can resolve.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from ..types.errors import IPFSFetchError, IPFSGatewayError

_IPFS_PUBLISH_URL = "https://capi.ogpuscan.io/file/create"


def publish_to_ipfs(
    data: str | dict[str, Any],
    filename: str = "data.json",
    content_type: str = "application/json",
) -> str:
    """Publish ``data`` (string or JSON-serializable dict) to IPFS.

    Returns the resulting gateway URL. Raises ``IPFSFetchError`` on network
    failure, ``IPFSGatewayError`` on non-success status or malformed response.
    """
    content = json.dumps(data) if isinstance(data, dict) else data
    files = {"file": (filename, content, content_type)}

    try:
        response = requests.post(_IPFS_PUBLISH_URL, files=files, timeout=30)
    except requests.RequestException as exc:
        raise IPFSFetchError(url=_IPFS_PUBLISH_URL, reason=str(exc)) from exc

    if response.status_code not in (200, 201):
        raise IPFSGatewayError(gateway=_IPFS_PUBLISH_URL, status_code=response.status_code)

    try:
        link = response.json()["link"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise IPFSGatewayError(gateway=_IPFS_PUBLISH_URL, status_code=response.status_code) from exc
    return str(link)
