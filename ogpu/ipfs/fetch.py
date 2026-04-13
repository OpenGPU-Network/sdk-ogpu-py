"""Fetch off-chain content from a standard IPFS gateway."""

from __future__ import annotations

import json
from typing import Any

import requests

from ..types.errors import IPFSFetchError, IPFSGatewayError


def fetch_ipfs_json(url: str) -> dict[str, Any]:
    """GET an IPFS gateway URL and parse the body as JSON.

    Used by ``Source.get_metadata``, ``Task.get_metadata``, and
    ``Response.fetch_data`` internally, but exposed here so you can
    fetch any IPFS JSON content directly — e.g. inspecting a task
    config URL from chain state, or decoding a response payload you
    discovered through some other path.

    Only handles JSON responses. If the content is binary (model
    weights, images, video), fetch it with your own HTTP client —
    ``Response.get_data()`` returns the raw URL string that you can
    feed to ``requests.get(url).content`` or similar.

    Works against any HTTP gateway URL, not just OGPU's — use it with
    ``https://cipfs.ogpuscan.io/...``, ``https://ipfs.io/...``, or your
    own node.

    Args:
        url: The gateway URL to fetch. Must respond with JSON.

    Returns:
        The parsed JSON body as a dict.

    Raises:
        IPFSFetchError: Network error, connection timeout, or invalid
            JSON in the response body.
        IPFSGatewayError: The gateway returned a non-200 status code.

    Example:
        ```python
        from ogpu import fetch_ipfs_json

        metadata = fetch_ipfs_json(
            "https://cipfs.ogpuscan.io/ipfs/QmAbC...",
        )
        print(metadata["name"])
        # 'sentiment-analyzer'

        # Same pattern from inside a Response instance — but
        # Response.fetch_data() is the more typical entry point:
        response = Response.load("0x...")
        payload = response.fetch_data()
        ```
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
