"""Upload off-chain content to the OGPU IPFS pinning service.

The SDK uses ``publish_to_ipfs`` internally whenever it needs to put
off-chain content on IPFS — source metadata before ``publishSource``,
task configs before ``publishTask``, and so on. Users call it directly
when they're producing real response payloads as a provider or uploading
custom data.

The publish endpoint is OGPU-specific (``capi.ogpuscan.io/file/create``)
and always returns a gateway URL that any standard IPFS gateway can
resolve.
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
    """Publish ``data`` to IPFS via the OGPU pinning service.

    Accepts either a dict (JSON-serialized before upload) or a raw
    string (uploaded as-is). Returns a gateway URL pointing at the
    pinned content — typically something like
    ``https://cipfs.ogpuscan.io/ipfs/Qm...``.

    The upload target is OGPU's own pinning endpoint; you cannot point
    this at a different IPFS gateway. If you need custom pinning, use
    your own HTTP client and pass the resulting URL to the SDK wherever
    it expects a ``data`` URL field.

    Args:
        data: The content to upload. A dict is JSON-serialized before
            sending. A string is uploaded unchanged — use this if you
            already have a JSON string or want to upload plain text.
        filename: Filename to send in the multipart form. Only affects
            how the pinning service labels the upload; the returned URL
            does not include this name.
        content_type: MIME type to send with the upload. Defaults to
            ``application/json``.

    Returns:
        Gateway URL (string) pointing at the pinned content.

    Raises:
        IPFSFetchError: Network error, connection refused, DNS failure,
            or malformed response body.
        IPFSGatewayError: The endpoint responded with a non-success
            status code, or the response JSON is missing the ``link``
            field.

    Example:
        ```python
        from ogpu import publish_to_ipfs

        # Upload a dict as JSON
        url = publish_to_ipfs(
            {"result": "cat", "confidence": 0.97},
            filename="response.json",
        )
        print(url)
        # 'https://cipfs.ogpuscan.io/ipfs/Qm...'

        # Upload a raw string
        url = publish_to_ipfs(
            "plain text content",
            filename="note.txt",
            content_type="text/plain",
        )
        ```
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
        raise IPFSGatewayError(
            gateway=_IPFS_PUBLISH_URL, status_code=response.status_code
        ) from exc
    return str(link)
