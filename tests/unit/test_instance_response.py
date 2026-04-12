"""Response instance class — mock unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.protocol.response import Response
from ogpu.types.enums import ResponseStatus
from ogpu.types.errors import ResponseNotFoundError
from ogpu.types.receipt import Receipt

_ADDR = "0x" + "cc" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _pw3():
    return patch("ogpu.protocol._base._get_web3", return_value=_FAKE_WEB3)


def _mc(**views):
    c = MagicMock()
    for name, val in views.items():
        getattr(c.functions, name).return_value.call.return_value = val
    return c


class TestResponseConstructor:
    def test_lazy(self):
        with _pw3():
            r = Response(_ADDR)
        assert r.address == _ADDR

    def test_load_raises(self):
        c = MagicMock()
        c.functions.getStatus.return_value.call.side_effect = Exception("revert")
        with _pw3(), patch("ogpu.protocol.response.load_contract", return_value=c):
            with pytest.raises(ResponseNotFoundError):
                Response.load(_ADDR)


class TestResponseReads:
    def _r(self, contract):
        r = Response.__new__(Response)
        r.address = _ADDR
        r.chain = None
        return r, patch("ogpu.protocol.response.load_contract", return_value=contract)

    def test_get_params(self):
        c = _mc(getResponseParams=("0xT", "0xP", "data_blob", 100))
        r, p = self._r(c)
        with p:
            params = r.get_params()
        assert params.task == "0xT"
        assert params.provider == "0xP"
        assert params.data == "data_blob"
        assert params.payment == 100

    def test_get_task(self):
        c = _mc(getResponseParams=("0x" + "bb" * 20, "0xP", "d", 0))
        r, p = self._r(c)
        with p, _pw3():
            t = r.get_task()
        assert str(t) == "0x" + "bb" * 20

    def test_get_data(self):
        c = _mc(getResponseParams=("0xT", "0xP", "payload", 0))
        r, p = self._r(c)
        with p:
            assert r.get_data() == "payload"

    def test_fetch_data_follows_url_and_parses_json(self):
        c = _mc(getResponseParams=("0xT", "0xP", "https://ipfs.example/Qm123", 0))
        r, p = self._r(c)
        with p, patch(
            "ogpu.protocol.response.fetch_ipfs_json",
            return_value={"result": 42, "logs": ["step1", "step2"]},
        ) as fetch_mock:
            payload = r.fetch_data()
        assert payload == {"result": 42, "logs": ["step1", "step2"]}
        fetch_mock.assert_called_once_with("https://ipfs.example/Qm123")

    def test_get_status(self):
        c = _mc(getStatus=0)
        r, p = self._r(c)
        with p:
            assert r.get_status() == ResponseStatus.SUBMITTED

    def test_get_timestamp(self):
        c = _mc(responseTimestamp=12345)
        r, p = self._r(c)
        with p:
            assert r.get_timestamp() == 12345

    def test_is_confirmed(self):
        c = _mc(confirmedFinal=True)
        r, p = self._r(c)
        with p:
            assert r.is_confirmed() is True


class TestResponseConfirm:
    def test_confirm_delegates(self):
        receipt = Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)
        r = Response.__new__(Response)
        r.address = _ADDR
        r.chain = None
        with patch("ogpu.protocol.controller.confirm_response", return_value=receipt) as mock:
            result = r.confirm(signer="0x" + "11" * 32)
        assert result.tx_hash == "0xhash"
        mock.assert_called_once_with(_ADDR, signer="0x" + "11" * 32)


class TestResponseSnapshot:
    def test_snapshot(self):
        c = _mc(
            getResponseParams=("0xT", "0xP", "data", 50),
            getStatus=1, responseTimestamp=9999, confirmedFinal=True,
        )
        with _pw3(), patch("ogpu.protocol.response.load_contract", return_value=c):
            r = Response(_ADDR)
            snap = r.snapshot()
        assert snap.address == _ADDR
        assert snap.confirmed is True
        assert snap.data == "data"
        assert snap.status == ResponseStatus.CONFIRMED
