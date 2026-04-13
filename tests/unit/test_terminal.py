"""Terminal module — mock unit tests for Phase 5 writes and reads."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ogpu.protocol import terminal
from ogpu.types.receipt import Receipt

_KEY = "0x" + "11" * 32
_ADDR = "0x" + "aa" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a
_FAKE_WEB3.is_address = lambda a: isinstance(a, str) and len(a) == 42


def _receipt():
    return Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)


def _pe():
    return patch("ogpu.protocol._base.TxExecutor.execute", return_value=_receipt())


def _pc():
    return patch("ogpu.protocol.terminal.load_contract", return_value=MagicMock())


def _pw():
    return patch("ogpu.protocol.terminal._get_web3", return_value=_FAKE_WEB3)


class TestTerminalWrites:
    def test_announce_master(self):
        with _pc(), _pe(), _pw():
            r = terminal.announce_master(_ADDR, signer=_KEY)
        assert r.tx_hash == "0xhash"

    def test_announce_provider(self):
        with _pc(), _pe(), _pw():
            r = terminal.announce_provider(_ADDR, 1000, signer=_KEY)
        assert r.status == 1

    def test_remove_provider(self):
        with _pc(), _pe(), _pw():
            r = terminal.remove_provider(_ADDR, signer=_KEY)
        assert r.status == 1

    def test_remove_container(self):
        src = "0x" + "bb" * 20
        with _pc(), _pe(), _pw():
            r = terminal.remove_container(_ADDR, src, signer=_KEY)
        assert r.status == 1

    def test_set_default_agent_disabled(self):
        with _pc(), _pe():
            r = terminal.set_default_agent_disabled(True, signer=_KEY)
        assert r.status == 1


class TestTerminalReads:
    def _mock(self, fn, ret):
        c = MagicMock()
        getattr(c.functions, fn).return_value.call.return_value = ret
        return patch("ogpu.protocol.terminal.load_contract", return_value=c)

    def test_get_master_of(self):
        with self._mock("masterOf", "0xMASTER"):
            assert terminal.get_master_of(_ADDR) == "0xMASTER"

    def test_get_provider_of(self):
        with self._mock("providerOf", "0xPROV"):
            assert terminal.get_provider_of(_ADDR) == "0xPROV"

    def test_get_base_data_of(self):
        with self._mock("baseDataOf", "ipfs://base"):
            assert terminal.get_base_data_of(_ADDR) == "ipfs://base"

    def test_get_live_data_of(self):
        with self._mock("liveDataOf", "ipfs://live"):
            assert terminal.get_live_data_of(_ADDR) == "ipfs://live"

    def test_is_master(self):
        with self._mock("isMaster", True):
            assert terminal.is_master(_ADDR) is True

    def test_is_provider(self):
        with self._mock("isProvider", False):
            assert terminal.is_provider(_ADDR) is False

    def test_is_agent_of(self):
        with self._mock("isAgentOf", True):
            assert terminal.is_agent_of(_ADDR, "0xAGENT") is True

    def test_is_default_agent_disabled(self):
        with self._mock("defaultAgentDisabled", False):
            assert terminal.is_default_agent_disabled(_ADDR) is False
