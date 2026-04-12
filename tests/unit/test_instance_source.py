"""Source instance class — mock unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.protocol.source import Source
from ogpu.types.enums import Environment, SourceStatus
from ogpu.types.errors import SourceNotFoundError

_ADDR = "0x" + "aa" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _patch_web3():
    return patch("ogpu.protocol._base._get_web3", return_value=_FAKE_WEB3)


def _mock_contract(**view_returns):
    contract = MagicMock()
    for name, value in view_returns.items():
        getattr(contract.functions, name).return_value.call.return_value = value
    return contract


class TestSourceConstructor:
    def test_lazy_no_rpc(self):
        with _patch_web3():
            s = Source(_ADDR)
        assert s.address == _ADDR
        assert s.chain is None

    def test_load_success(self):
        contract = _mock_contract(getStatus=0)
        with _patch_web3(), patch("ogpu.protocol.source.load_contract", return_value=contract):
            s = Source.load(_ADDR)
        assert s.address == _ADDR

    def test_load_raises_not_found(self):
        contract = MagicMock()
        contract.functions.getStatus.return_value.call.side_effect = Exception("revert")
        with _patch_web3(), patch("ogpu.protocol.source.load_contract", return_value=contract):
            with pytest.raises(SourceNotFoundError):
                Source.load(_ADDR)


class TestSourceReads:
    def _make(self, **views):
        contract = _mock_contract(**views)
        return Source.__new__(Source), contract

    def _setup(self, source, contract):
        source.address = _ADDR
        source.chain = None
        return patch("ogpu.protocol.source.load_contract", return_value=contract)

    def test_get_client(self):
        s, c = self._make(getClient="0xCLIENT")
        with self._setup(s, c):
            assert s.get_client() == "0xCLIENT"

    def test_get_status(self):
        s, c = self._make(getStatus=0)
        with self._setup(s, c):
            assert s.get_status() == SourceStatus.ACTIVE

    def test_get_params(self):
        raw = ("0xC", "ipfs://meta", 1, 100, 0, 3600, False, "", 0, 9999)
        s, c = self._make(getSourceParams=raw)
        with self._setup(s, c):
            p = s.get_params()
            assert p.client == "0xC"
            assert p.imageMetadataUrl == "ipfs://meta"
            assert p.minPayment == 100

    def test_get_metadata(self):
        raw = ("0xC", "ipfs://meta", 1, 0, 0, 60, False, "", 0, 0)
        s, c = self._make(getSourceParams=raw)
        with self._setup(s, c), patch(
            "ogpu.protocol.source.fetch_ipfs_json", return_value={"name": "demo"}
        ):
            assert s.get_metadata()["name"] == "demo"

    def test_get_task_count(self):
        s, c = self._make(getTaskCount=5)
        with self._setup(s, c):
            assert s.get_task_count() == 5

    def test_get_registrant_count(self):
        s, c = self._make(getRegistrantCount=3)
        with self._setup(s, c):
            assert s.get_registrant_count() == 3

    def test_get_registrant_id(self):
        s, c = self._make(getRegistrantId=7)
        with self._setup(s, c):
            assert s.get_registrant_id("0xPROV") == 7

    def test_get_preferred_environment_of(self):
        s, c = self._make(preferredEnvironmentOf=2)
        with self._setup(s, c):
            assert s.get_preferred_environment_of("0xP") == Environment.NVIDIA

    def test_get_tasks_paginated(self):
        s, c = self._make(getTaskCount=2)
        c.functions.getTasks.return_value.call.return_value = ["0x" + "bb" * 20, "0x" + "cc" * 20]
        with self._setup(s, c), _patch_web3():
            tasks = s.get_tasks()
        assert len(tasks) == 2

    def test_get_registrants_paginated(self):
        s, c = self._make(getRegistrantCount=1)
        c.functions.getRegistrants.return_value.call.return_value = ["0x" + "dd" * 20]
        with self._setup(s, c):
            regs = s.get_registrants()
        assert len(regs) == 1


class TestSourceSnapshot:
    def test_snapshot_returns_frozen(self):
        raw_params = ("0xC", "ipfs://m", 1, 0, 0, 60, False, "", 0, 0)
        contract = _mock_contract(
            getClient="0xC", getStatus=0, getSourceParams=raw_params,
            getTaskCount=2, getRegistrantCount=1,
        )
        with _patch_web3(), patch("ogpu.protocol.source.load_contract", return_value=contract):
            s = Source(_ADDR)
            snap = s.snapshot()
        assert snap.address == _ADDR
        assert snap.client == "0xC"
        assert snap.task_count == 2
        with pytest.raises(Exception):
            snap.client = "x"  # type: ignore[misc]


class TestSourceDunder:
    def test_eq_same(self):
        with _patch_web3():
            a = Source(_ADDR)
            b = Source(_ADDR)
        assert a == b

    def test_eq_different(self):
        with _patch_web3():
            a = Source(_ADDR)
            b = Source("0x" + "bb" * 20)
        assert a != b

    def test_str(self):
        with _patch_web3():
            assert str(Source(_ADDR)) == _ADDR

    def test_repr(self):
        with _patch_web3():
            r = repr(Source(_ADDR))
        assert "<Source" in r and "@mainnet>" in r

    def test_hash_stable(self):
        with _patch_web3():
            assert hash(Source(_ADDR)) == hash(Source(_ADDR))
