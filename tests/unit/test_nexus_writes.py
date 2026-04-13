"""Nexus Phase 3+5 write functions — mock tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ogpu.protocol import nexus
from ogpu.types.metadata import SourceParams
from ogpu.types.receipt import Receipt

_KEY = "0x" + "11" * 32
_ADDR = "0x" + "aa" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _receipt():
    return Receipt(tx_hash="0x1", block_number=1, gas_used=1, status=1)


def _pe():
    return patch("ogpu.protocol._base.TxExecutor.execute", return_value=_receipt())


def _pc():
    return patch("ogpu.protocol.nexus.load_contract", return_value=MagicMock())


def _pw():
    return patch("ogpu.protocol.nexus._get_web3", return_value=_FAKE_WEB3)


class TestNexusClientWrites:
    def test_update_source(self):
        params = SourceParams(
            client="0xC", imageMetadataUrl="", imageEnvironments=1,
            minPayment=0, minAvailableLockup=0, maxExpiryDuration=60,
            privacyEnabled=False, optionalParamsUrl="", deliveryMethod=0,
        )
        with _pc(), _pe(), _pw():
            r = nexus.update_source(_ADDR, params, signer=_KEY)
        assert r.status == 1

    def test_inactivate_source(self):
        with _pc(), _pe(), _pw():
            r = nexus.inactivate_source(_ADDR, signer=_KEY)
        assert r.status == 1


class TestNexusProviderWrites:
    def test_register(self):
        with _pc(), _pe(), _pw():
            r = nexus.register("0xSRC", "0xPROV", 1, signer=_KEY)
        assert r.status == 1

    def test_unregister(self):
        with _pc(), _pe(), _pw():
            r = nexus.unregister("0xSRC", "0xPROV", signer=_KEY)
        assert r.status == 1

    def test_attempt(self):
        with _pc(), _pe(), _pw():
            r = nexus.attempt("0xTASK", "0xPROV", 100, signer=_KEY)
        assert r.status == 1
