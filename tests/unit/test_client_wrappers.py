"""Phase 1 transitional client wrappers.

Verifies that the old-style signatures (``private_key=``, returning str) still
work by delegating to the new protocol layer under the hood.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from eth_account import Account

from ogpu import client
from ogpu.types.metadata import ImageEnvironments, SourceInfo, TaskInfo, TaskInput
from ogpu.types.receipt import Receipt

_HEX_KEY = "0x" + "11" * 32
_FAKE_SRC = "0x" + "aa" * 20
_FAKE_TASK = "0x" + "bb" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _fake_receipt(tx_hash: str = "0x" + "a" * 64) -> Receipt:
    return Receipt(tx_hash=tx_hash, block_number=1, gas_used=1, status=1)


def _web3_patch():
    return patch("ogpu.protocol._base._get_web3", return_value=_FAKE_WEB3)


class TestPublishSourceWrapper:
    def _make_info(self):
        return SourceInfo(
            name="x", description="y", logoUrl="z",
            imageEnvs=ImageEnvironments(cpu="c"),
            minPayment=0, minAvailableLockup=0, maxExpiryDuration=60,
        )

    def test_returns_source_instance(self, monkeypatch):
        monkeypatch.setattr("ogpu._ipfs.publish_to_ipfs", lambda *a, **kw: "ipfs://X")
        with (
            _web3_patch(),
            patch("ogpu.protocol.nexus.publish_source", return_value=_fake_receipt()),
            patch("ogpu.protocol.nexus.extract_source_address", return_value=_FAKE_SRC),
        ):
            result = client.publish_source(self._make_info(), private_key=_HEX_KEY)
        assert str(result) == _FAKE_SRC

    def test_reads_client_private_key_env(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", _HEX_KEY)
        monkeypatch.setattr("ogpu._ipfs.publish_to_ipfs", lambda *a, **kw: "ipfs://X")
        with (
            _web3_patch(),
            patch("ogpu.protocol.nexus.publish_source", return_value=_fake_receipt()),
            patch("ogpu.protocol.nexus.extract_source_address", return_value=_FAKE_SRC),
        ):
            result = client.publish_source(self._make_info())
        assert str(result) == _FAKE_SRC

    def test_ignores_old_kwargs(self, monkeypatch):
        monkeypatch.setattr("ogpu._ipfs.publish_to_ipfs", lambda *a, **kw: "ipfs://X")
        with (
            _web3_patch(),
            patch("ogpu.protocol.nexus.publish_source", return_value=_fake_receipt()),
            patch("ogpu.protocol.nexus.extract_source_address", return_value=_FAKE_SRC),
        ):
            result = client.publish_source(
                self._make_info(), private_key=_HEX_KEY,
                nonce=42, auto_fix_nonce=False, max_retries=9,
            )
        assert str(result) == _FAKE_SRC


class TestPublishTaskWrapper:
    def test_returns_task_instance(self, monkeypatch):
        monkeypatch.setattr("ogpu._ipfs.publish_to_ipfs", lambda *a, **kw: "ipfs://X")
        info = TaskInfo(
            source="0xSRC",
            config=TaskInput(function_name="fn", data={}),
            expiryTime=100,
            payment=10,
        )
        with (
            _web3_patch(),
            patch("ogpu.protocol.controller.publish_task", return_value=_fake_receipt()),
            patch("ogpu.protocol.controller.extract_task_address", return_value=_FAKE_TASK),
        ):
            result = client.publish_task(info, private_key=_HEX_KEY)
        assert str(result) == _FAKE_TASK


class TestConfirmResponseWrapper:
    def test_returns_tx_hash_string(self):
        receipt = _fake_receipt(tx_hash="0xdeadbeef")
        with patch(
            "ogpu.protocol.controller.confirm_response", return_value=receipt
        ):
            tx_hash = client.confirm_response("0xRESP", private_key=_HEX_KEY)
        assert tx_hash == "0xdeadbeef"

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("CLIENT_PRIVATE_KEY", raising=False)
        with pytest.raises(Exception):
            client.confirm_response("0xRESP")


class TestSetAgentWrapper:
    def test_returns_tx_hash_string(self):
        receipt = _fake_receipt(tx_hash="0xabcdef")
        with patch(
            "ogpu.protocol.terminal.set_agent", return_value=receipt
        ) as set_agent_mock:
            tx_hash = client.set_agent(
                "0x" + "a" * 40, True, private_key=_HEX_KEY
            )
        assert tx_hash == "0xabcdef"
        set_agent_mock.assert_called_once()
