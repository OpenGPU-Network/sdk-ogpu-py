"""Task instance class — mock unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.protocol._base import ZERO_ADDRESS
from ogpu.protocol.task import Task
from ogpu.types.enums import DeliveryMethod, TaskStatus
from ogpu.types.errors import TaskNotFoundError
from ogpu.types.receipt import Receipt

_ADDR = "0x" + "bb" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _pw3():
    return patch("ogpu.protocol._base._get_web3", return_value=_FAKE_WEB3)


def _mc(**views):
    c = MagicMock()
    for name, val in views.items():
        getattr(c.functions, name).return_value.call.return_value = val
    return c


class TestTaskConstructor:
    def test_lazy(self):
        with _pw3():
            t = Task(_ADDR)
        assert t.address == _ADDR

    def test_load_raises(self):
        c = MagicMock()
        c.functions.getStatus.return_value.call.side_effect = Exception("boom")
        with _pw3(), patch("ogpu.protocol.task.load_contract", return_value=c):
            with pytest.raises(TaskNotFoundError):
                Task.load(_ADDR)


class TestTaskReads:
    def _t(self, contract):
        t = Task.__new__(Task)
        t.address = _ADDR
        t.chain = None
        return t, patch("ogpu.protocol.task.load_contract", return_value=contract)

    def test_get_source(self):
        c = _mc(getSource="0x" + "aa" * 20)
        t, p = self._t(c)
        with p, _pw3():
            src = t.get_source()
        assert str(src) == "0x" + "aa" * 20

    def test_get_status(self):
        c = _mc(getStatus=0)
        t, p = self._t(c)
        with p:
            assert t.get_status() == TaskStatus.NEW

    def test_get_params(self):
        c = _mc(taskParams=("0xS", "ipfs://c", 1000, 50))
        t, p = self._t(c)
        with p:
            tp = t.get_params()
            assert tp.source == "0xS" and tp.payment == 50

    def test_get_metadata(self):
        c = _mc(taskParams=("0xS", "ipfs://config", 0, 0))
        t, p = self._t(c)
        with p, patch("ogpu.protocol.task.fetch_ipfs_json", return_value={"fn": "predict"}):
            assert t.get_metadata()["fn"] == "predict"

    def test_get_payment(self):
        c = _mc(getPayment=42)
        t, p = self._t(c)
        with p:
            assert t.get_payment() == 42

    def test_get_expiry_time(self):
        c = _mc(getExpiryTime=9999)
        t, p = self._t(c)
        with p:
            assert t.get_expiry_time() == 9999

    def test_get_delivery_method(self):
        c = _mc(getDeliveryMethod=1)
        t, p = self._t(c)
        with p:
            assert t.get_delivery_method() == DeliveryMethod.FIRST_RESPONSE

    def test_get_attempt_count(self):
        c = _mc(getAttemptCount=3)
        t, p = self._t(c)
        with p:
            assert t.get_attempt_count() == 3

    def test_get_attempters(self):
        c = _mc(getAttemptCount=2)
        c.functions.getAttempters.return_value.call.return_value = ["0x" + "11" * 20, "0x" + "22" * 20]
        t, p = self._t(c)
        with p:
            assert len(t.get_attempters()) == 2

    def test_get_attempter_id(self):
        c = _mc(getAttempterId=5)
        t, p = self._t(c)
        with p:
            assert t.get_attempter_id("0xP") == 5

    def test_get_response_of_found(self):
        resp_addr = "0x" + "cc" * 20
        c = _mc(responseOf=resp_addr)
        t, p = self._t(c)
        with p, _pw3():
            r = t.get_response_of("0xP")
        assert r is not None and str(r) == resp_addr

    def test_get_response_of_zero(self):
        c = _mc(responseOf=ZERO_ADDRESS)
        t, p = self._t(c)
        with p:
            assert t.get_response_of("0xP") is None

    def test_get_winning_provider_found(self):
        c = _mc(winningProvider="0x" + "dd" * 20)
        t, p = self._t(c)
        with p:
            assert t.get_winning_provider() == "0x" + "dd" * 20

    def test_get_winning_provider_none(self):
        c = _mc(winningProvider=ZERO_ADDRESS)
        t, p = self._t(c)
        with p:
            assert t.get_winning_provider() is None

    def test_is_already_submitted(self):
        c = _mc(isAlreadySubmitted=True)
        t, p = self._t(c)
        with p:
            assert t.is_already_submitted(b"\x00" * 32) is True

    def test_get_responses(self):
        c = _mc(getAttemptCount=1)
        c.functions.getResponsesOf.return_value.call.return_value = ["0x" + "ee" * 20]
        t, p = self._t(c)
        with p, _pw3():
            resps = t.get_responses()
        assert len(resps) == 1

    def test_get_confirmed_response_found(self):
        resp = MagicMock()
        resp.is_confirmed.return_value = True
        t = Task.__new__(Task)
        t.address = _ADDR
        t.chain = None
        with patch.object(Task, "get_responses", return_value=[resp]):
            assert t.get_confirmed_response() is resp

    def test_get_confirmed_response_none(self):
        t = Task.__new__(Task)
        t.address = _ADDR
        t.chain = None
        with patch.object(Task, "get_responses", return_value=[]):
            assert t.get_confirmed_response() is None


class TestTaskCancel:
    def test_cancel_delegates(self):
        receipt = Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)
        t = Task.__new__(Task)
        t.address = _ADDR
        t.chain = None
        with patch("ogpu.protocol.controller.cancel_task", return_value=receipt) as mock:
            r = t.cancel(signer="0x" + "11" * 32)
        assert r.tx_hash == "0xhash"
        mock.assert_called_once_with(_ADDR, signer="0x" + "11" * 32)


class TestTaskSnapshot:
    def test_snapshot(self):
        c = _mc(
            getSource="0x" + "aa" * 20, getStatus=0,
            taskParams=("0xS", "ipfs://c", 1000, 50),
            getPayment=50, getExpiryTime=1000, getDeliveryMethod=0,
            getAttemptCount=0, winningProvider=ZERO_ADDRESS,
        )
        with _pw3(), patch("ogpu.protocol.task.load_contract", return_value=c):
            t = Task(_ADDR)
            snap = t.snapshot()
        assert snap.address == _ADDR
        assert snap.payment == 50
        assert snap.winning_provider is None
