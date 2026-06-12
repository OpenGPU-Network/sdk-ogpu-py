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
import logging
import time
from typing import Any

import requests

from ..types.errors import IPFSFetchError, IPFSGatewayError

logger = logging.getLogger("ogpu.ipfs")

_IPFS_PUBLISH_URL = "https://capi.ogpuscan.io/file/create"


def publish_to_ipfs(
    data: str | dict[str, Any],
    filename: str = "data.json",
    content_type: str = "application/json",
    timeout: float = 30,
    retries: int = 2,
    backoff: float = 0.5,
    _deadline: float | None = None,
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
        timeout: Per-attempt cap in seconds for the upload. A stalled
            endpoint raises ``IPFSFetchError`` after this long instead
            of blocking. Defaults to 30.
        retries: Total attempts on *transient* failures — connection
            errors, timeouts, and 5xx responses. 4xx responses and
            malformed bodies fail immediately without retry. Defaults
            to 2.
        backoff: Base sleep in seconds between attempts, doubled each
            retry. Defaults to 0.5.
        _deadline: Internal — absolute ``time.monotonic()`` deadline set
            by ``publish_task``'s ``total_timeout``. Attempts and
            backoffs never run past it.

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
    attempts = max(1, retries)

    def _remaining() -> float | None:
        if _deadline is None:
            return None
        return _deadline - time.monotonic()

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        effective_timeout = timeout
        remaining = _remaining()
        if remaining is not None:
            if remaining <= 0:
                break  # budget exhausted — raise below with the last error
            effective_timeout = min(timeout, remaining)

        logger.debug(
            "publishing %s (%d bytes) to IPFS (attempt %d/%d)...",
            filename,
            len(content),
            attempt,
            attempts,
        )
        started = time.monotonic()
        try:
            response = requests.post(_IPFS_PUBLISH_URL, files=files, timeout=effective_timeout)
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "IPFS publish attempt %d/%d failed after %.1fs: %s",
                attempt,
                attempts,
                time.monotonic() - started,
                exc,
            )
        else:
            if response.status_code in (200, 201):
                try:
                    link = response.json()["link"]
                except (json.JSONDecodeError, KeyError) as exc:
                    # malformed success body — not transient, no retry
                    raise IPFSGatewayError(
                        gateway=_IPFS_PUBLISH_URL, status_code=response.status_code
                    ) from exc
                logger.info("IPFS pin ok in %.1fs → %s", time.monotonic() - started, link)
                return str(link)

            logger.warning(
                "IPFS publish attempt %d/%d rejected after %.1fs: HTTP %d",
                attempt,
                attempts,
                time.monotonic() - started,
                response.status_code,
            )
            if response.status_code < 500:
                # 4xx — the request itself is bad, retrying won't help
                raise IPFSGatewayError(
                    gateway=_IPFS_PUBLISH_URL, status_code=response.status_code
                )
            last_error = IPFSGatewayError(
                gateway=_IPFS_PUBLISH_URL, status_code=response.status_code
            )

        if attempt < attempts:
            sleep_for = backoff * (2 ** (attempt - 1))
            remaining = _remaining()
            if remaining is not None:
                sleep_for = min(sleep_for, max(remaining, 0))
            if sleep_for > 0:
                time.sleep(sleep_for)

    if isinstance(last_error, IPFSGatewayError):
        raise last_error
    reason = str(last_error) if last_error else "publish budget exhausted before any attempt"
    raise IPFSFetchError(url=_IPFS_PUBLISH_URL, reason=reason) from last_error
