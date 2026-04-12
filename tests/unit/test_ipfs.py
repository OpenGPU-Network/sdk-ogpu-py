from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu._ipfs import publish_to_ipfs
from ogpu.types.errors import IPFSFetchError, IPFSGatewayError


def _mock_response(status=201, json_data=None, raise_on_post=None):
    if raise_on_post is not None:
        def raiser(*a, **kw):
            raise raise_on_post
        return raiser
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {"link": "ipfs://Qm123"}
    return MagicMock(return_value=resp)


class TestPublishToIpfs:
    def test_dict_payload_serialized(self):
        with patch("ogpu._ipfs.requests.post", _mock_response()) as post:
            link = publish_to_ipfs({"a": 1, "b": 2}, filename="x.json")
        assert link == "ipfs://Qm123"
        kwargs = post.call_args.kwargs
        _filename, content, _ct = kwargs["files"]["file"]
        assert "a" in content and "1" in content

    def test_string_payload_passthrough(self):
        with patch("ogpu._ipfs.requests.post", _mock_response()) as post:
            publish_to_ipfs("raw body", filename="body.txt")
        _, content, _ = post.call_args.kwargs["files"]["file"]
        assert content == "raw body"

    def test_200_status_accepted(self):
        with patch("ogpu._ipfs.requests.post", _mock_response(status=200)):
            link = publish_to_ipfs({"k": "v"})
        assert link == "ipfs://Qm123"

    def test_network_error_raises_ipfs_fetch_error(self):
        import requests

        with patch(
            "ogpu._ipfs.requests.post",
            side_effect=requests.ConnectionError("dns fail"),
        ):
            with pytest.raises(IPFSFetchError) as exc:
                publish_to_ipfs({"k": "v"})
        assert "dns fail" in exc.value.reason

    def test_non_success_status_raises_gateway_error(self):
        with patch("ogpu._ipfs.requests.post", _mock_response(status=503)):
            with pytest.raises(IPFSGatewayError) as exc:
                publish_to_ipfs({"k": "v"})
        assert exc.value.status_code == 503

    def test_malformed_json_raises_gateway_error(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {}  # missing 'link' key
        with patch("ogpu._ipfs.requests.post", return_value=resp):
            with pytest.raises(IPFSGatewayError):
                publish_to_ipfs({"k": "v"})
