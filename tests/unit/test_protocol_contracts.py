"""Tests for protocol.nexus, protocol.controller, protocol.terminal wrappers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from eth_account import Account

from ogpu.protocol import controller, nexus, terminal
from ogpu.types.errors import InvalidSignerError
from ogpu.types.metadata import SourceParams, TaskParams
from ogpu.types.receipt import Receipt

_HEX_KEY = "0x" + "11" * 32


def _mock_receipt(**over):
    data = {
        "tx_hash": "0x" + "a" * 64,
        "block_number": 10,
        "gas_used": 21000,
        "status": 1,
        "logs": [],
        "timestamp": 0,
    }
    data.update(over)
    return Receipt(**data)


def _patch_executor(receipt):
    """Stub out TxExecutor.execute to return a pre-built Receipt."""
    return patch(
        "ogpu.protocol._base.TxExecutor.execute",
        return_value=receipt,
    )


def _patch_load_contract(contract):
    return patch("ogpu.protocol._base.load_contract", return_value=contract)


class TestNexusPublishSource:
    def test_calls_tx_executor_with_tuple(self):
        params = SourceParams(
            client="0xC",
            imageMetadataUrl="ipfs://Qm",
            imageEnvironments=1,
            minPayment=0,
            minAvailableLockup=0,
            maxExpiryDuration=60,
            privacyEnabled=False,
            optionalParamsUrl="",
            deliveryMethod=0,
            lastUpdateTime=0,
        )
        contract = MagicMock()
        receipt = _mock_receipt()

        with (
            patch("ogpu.protocol.nexus.load_contract", return_value=contract),
            patch(
                "ogpu.protocol._base.TxExecutor.execute", return_value=receipt
            ) as execute,
        ):
            result = nexus.publish_source(params, signer=_HEX_KEY)

        assert result is receipt
        execute.assert_called_once()

    def test_missing_signer_no_env(self, monkeypatch):
        monkeypatch.delenv("CLIENT_PRIVATE_KEY", raising=False)
        params = SourceParams(
            client="0xC",
            imageMetadataUrl="",
            imageEnvironments=1,
            minPayment=0,
            minAvailableLockup=0,
            maxExpiryDuration=60,
            privacyEnabled=False,
            optionalParamsUrl="",
            deliveryMethod=0,
        )
        with pytest.raises(Exception):
            nexus.publish_source(params, signer=None)


class TestExtractSourceAddress:
    def test_extracts_from_log(self):
        fake_web3 = MagicMock()
        fake_web3.to_checksum_address = lambda a: a.upper()
        contract = MagicMock()
        contract.events.SourcePublished.return_value.process_receipt.return_value = [
            {"args": {"source": "0xsrc"}}
        ]

        with (
            patch("ogpu.protocol.nexus.load_contract", return_value=contract),
            patch("ogpu.protocol.nexus._get_web3", return_value=fake_web3),
        ):
            addr = nexus.extract_source_address(_mock_receipt(logs=[{}]))
            assert addr == "0XSRC"

    def test_raises_on_missing_log(self):
        contract = MagicMock()
        contract.events.SourcePublished.return_value.process_receipt.return_value = []

        with patch("ogpu.protocol.nexus.load_contract", return_value=contract):
            with pytest.raises(ValueError, match="SourcePublished event"):
                nexus.extract_source_address(_mock_receipt())


class TestControllerPublishTask:
    def test_calls_tx_executor_with_tuple(self):
        params = TaskParams(source="0xSRC", config="ipfs://Qm", expiryTime=100, payment=50)
        contract = MagicMock()
        receipt = _mock_receipt()

        with (
            patch("ogpu.protocol.controller.load_contract", return_value=contract),
            patch(
                "ogpu.protocol._base.TxExecutor.execute", return_value=receipt
            ) as execute,
        ):
            result = controller.publish_task(params, signer=_HEX_KEY)
        assert result is receipt
        execute.assert_called_once()


class TestControllerConfirmResponse:
    def test_calls_tx_executor(self):
        contract = MagicMock()
        receipt = _mock_receipt()
        fake_web3 = MagicMock()
        fake_web3.to_checksum_address = lambda a: a

        with (
            patch("ogpu.protocol.controller.load_contract", return_value=contract),
            patch(
                "ogpu.protocol._base.TxExecutor.execute", return_value=receipt
            ) as execute,
            patch("ogpu.protocol.controller._get_web3", return_value=fake_web3),
        ):
            result = controller.confirm_response("0xRESP", signer=_HEX_KEY)
        assert result is receipt
        execute.assert_called_once()


class TestExtractTaskAddress:
    def test_extracts_from_nexus_log(self):
        fake_web3 = MagicMock()
        fake_web3.to_checksum_address = lambda a: a
        contract = MagicMock()
        contract.events.TaskPublished.return_value.process_receipt.return_value = [
            {"args": {"task": "0xTASK"}}
        ]

        with (
            patch("ogpu.protocol.controller.load_contract", return_value=contract),
            patch("ogpu.protocol.controller._get_web3", return_value=fake_web3),
        ):
            addr = controller.extract_task_address(_mock_receipt(logs=[{}]))
            assert addr == "0xTASK"

    def test_raises_on_missing_log(self):
        contract = MagicMock()
        contract.events.TaskPublished.return_value.process_receipt.return_value = []
        with patch("ogpu.protocol.controller.load_contract", return_value=contract):
            with pytest.raises(ValueError, match="TaskPublished event"):
                controller.extract_task_address(_mock_receipt())


class TestTerminalSetAgent:
    def test_calls_tx_executor(self):
        contract = MagicMock()
        receipt = _mock_receipt()
        fake_web3 = MagicMock()
        fake_web3.is_address = lambda a: isinstance(a, str) and len(a) == 42
        fake_web3.to_checksum_address = lambda a: a

        with (
            patch("ogpu.protocol.terminal.load_contract", return_value=contract),
            patch(
                "ogpu.protocol._base.TxExecutor.execute", return_value=receipt
            ) as execute,
            patch("ogpu.protocol.terminal._get_web3", return_value=fake_web3),
        ):
            result = terminal.set_agent(
                "0x" + "a" * 40, True, signer=_HEX_KEY
            )
        assert result is receipt
        execute.assert_called_once()

    def test_invalid_agent_address_raises(self):
        contract = MagicMock()
        fake_web3 = MagicMock()
        fake_web3.is_address = lambda a: False

        with (
            patch("ogpu.protocol.terminal.load_contract", return_value=contract),
            patch("ogpu.protocol.terminal._get_web3", return_value=fake_web3),
        ):
            with pytest.raises(InvalidSignerError):
                terminal.set_agent("bad", True, signer=_HEX_KEY)


class TestTerminalRevokeAgent:
    def test_delegates_to_set_agent_with_false(self):
        receipt = _mock_receipt()
        with patch(
            "ogpu.protocol.terminal.set_agent", return_value=receipt
        ) as set_agent_mock:
            result = terminal.revoke_agent("0x" + "a" * 40, signer=_HEX_KEY)
            assert result is receipt
            set_agent_mock.assert_called_once_with(
                "0x" + "a" * 40, False, signer=_HEX_KEY
            )
