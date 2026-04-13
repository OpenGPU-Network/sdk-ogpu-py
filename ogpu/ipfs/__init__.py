"""IPFS helpers — publish and fetch off-chain content.

Users typically don't need to call these directly: ``SourceInfo`` / ``TaskInfo``
get their metadata uploaded automatically by ``client.publish_source`` /
``client.publish_task``, and ``Source.get_metadata`` / ``Task.get_metadata``
fetch it back. Providers producing real response output and clients reading
confirmed response payloads *do* need direct access — that's what this
package is for.

Example::

    from ogpu import publish_to_ipfs, fetch_ipfs_json

    # Provider side: upload compute output
    url = publish_to_ipfs({"result": 42, "logs": [...]}, filename="response.json")

    # Client side: fetch confirmed response payload
    task = Task.load("0x...")
    response = task.get_confirmed_response()
    payload = response.fetch_data()   # dict
"""

from __future__ import annotations

from .fetch import fetch_ipfs_json
from .publish import publish_to_ipfs

__all__ = [
    "publish_to_ipfs",
    "fetch_ipfs_json",
]
