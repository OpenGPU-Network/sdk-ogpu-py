"""Client Phase 3 wrappers — cancel_task, update_source, inactivate_source."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ogpu import client
from ogpu.types.metadata import ImageEnvironments, SourceInfo
from ogpu.types.receipt import Receipt

_KEY = "0x" + "11" * 32
_ADDR = "0x" + "aa" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _receipt():
    return Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)


class TestCancelTask:
    def test_returns_receipt(self):
        with patch("ogpu.protocol.controller.cancel_task", return_value=_receipt()) as m:
            r = client.cancel_task(_ADDR, private_key=_KEY)
        assert r.tx_hash == "0xhash"
        m.assert_called_once()


class TestUpdateSource:
    def test_returns_receipt(self, monkeypatch):
        monkeypatch.setattr("ogpu.client.publish_to_ipfs", lambda *a, **kw: "ipfs://X")
        info = SourceInfo(
            name="x", description="y", logoUrl="z",
            imageEnvs=ImageEnvironments(cpu="c"),
            minPayment=0, minAvailableLockup=0, maxExpiryDuration=60,
        )
        with patch("ogpu.protocol.nexus.update_source", return_value=_receipt()) as m:
            r = client.update_source(_ADDR, info, private_key=_KEY)
        assert r.tx_hash == "0xhash"
        m.assert_called_once()


class TestInactivateSource:
    def test_returns_receipt(self):
        with patch("ogpu.protocol.nexus.inactivate_source", return_value=_receipt()) as m:
            r = client.inactivate_source(_ADDR, private_key=_KEY)
        assert r.tx_hash == "0xhash"
        m.assert_called_once()
