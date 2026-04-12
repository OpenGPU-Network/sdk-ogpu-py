"""Fetch off-chain content from a standard IPFS gateway."""

from __future__ import annotations

import json
from typing import Any

import requests

from ..types.errors import IPFSFetchError, IPFSGatewayError


def fetch_ipfs_json(url: str) -> dict[str, Any]:
    """GET the given IPFS gateway URL and parse the body as JSON.

    Raises ``IPFSFetchError`` on network failure or invalid JSON,
    ``IPFSGatewayError`` on non-200 status.
    """
    try:
        response = requests.get(url, timeout=30)
    except requests.RequestException as exc:
        raise IPFSFetchError(url=url, reason=str(exc)) from exc

    if response.status_code != 200:
        raise IPFSGatewayError(gateway=url, status_code=response.status_code)

    try:
        data: dict[str, Any] = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise IPFSFetchError(url=url, reason=f"Invalid JSON: {exc}") from exc
    return data
