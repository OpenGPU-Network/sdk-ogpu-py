"""Acceptance tests for the 0.2.3 PRD — bounded & typed task-publish path.

One test (class) per PRD acceptance criterion:

- A1/A2 — IPFS retry on transient failures, no retry on 4xx/malformed
- A3 — IPFS knobs reach the pin through publish_task; one pin per call
- A4 — bounded receipt wait raises TxReceiptTimeoutError
- A5 — total_timeout bounds the whole call, never broadcasts past it
- A6 — every induced failure is a distinct OGPUError subclass
- A8 — 0.2.2 import paths still work
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
import requests
from web3.exceptions import TimeExhausted

import ogpu.client as client
from ogpu.client import TaskInfo, TaskInput
from ogpu.ipfs import publish_to_ipfs
from ogpu.types.errors import (
    IPFSFetchError,
    IPFSGatewayError,
    NonceError,
    OGPUError,
    PublishTimeoutError,
    TxReceiptTimeoutError,
    TxRpcError,
)

_HEX_KEY = "0x" + "11" * 32
_SOURCE = "0x" + "ab" * 20


def _ok_response(link: str = "https://gw/ipfs/Qm1"):
    resp = MagicMock(status_code=201)
    resp.json.return_value = {"link": link}
    return resp


def _http_response(status: int):
    resp = MagicMock(status_code=status)
    resp.json.return_value = {}
    return resp


def _task_info(expiry_offset: float = 3600) -> TaskInfo:
    return TaskInfo(
        source=_SOURCE,
        config=TaskInput(function_name="chat", data={"x": 1}),
        expiryTime=int(time.time() + expiry_offset),
        payment=10**15,
    )


class TestA1TransientRetry:
    def test_timeout_then_success_returns_link(self):
        post = MagicMock(side_effect=[requests.Timeout("stall"), _ok_response()])
        with patch("ogpu.ipfs.publish.requests.post", post):
            link = publish_to_ipfs({"a": 1}, retries=2, backoff=0)
        assert link == "https://gw/ipfs/Qm1"
        assert post.call_count == 2

    def test_5xx_then_success_returns_link(self):
        post = MagicMock(side_effect=[_http_response(503), _ok_response()])
        with patch("ogpu.ipfs.publish.requests.post", post):
            link = publish_to_ipfs({"a": 1}, retries=2, backoff=0)
        assert link == "https://gw/ipfs/Qm1"
        assert post.call_count == 2

    def test_connection_error_then_success(self):
        post = MagicMock(side_effect=[requests.ConnectionError("reset"), _ok_response()])
        with patch("ogpu.ipfs.publish.requests.post", post):
            assert publish_to_ipfs({"a": 1}, retries=2, backoff=0)
        assert post.call_count == 2


class TestA2BoundedAndNonRetryable:
    def test_never_responding_endpoint_raises_within_budget(self):
        post = MagicMock(side_effect=requests.Timeout("stall"))
        started = time.monotonic()
        with patch("ogpu.ipfs.publish.requests.post", post):
            with pytest.raises(IPFSFetchError):
                publish_to_ipfs({"a": 1}, timeout=0.2, retries=2, backoff=0.1)
        # timeout × retries + backoff, with generous scheduling slack
        assert time.monotonic() - started < 2.0
        assert post.call_count == 2

    def test_4xx_raises_immediately_without_retry(self):
        post = MagicMock(return_value=_http_response(400))
        with patch("ogpu.ipfs.publish.requests.post", post):
            with pytest.raises(IPFSGatewayError):
                publish_to_ipfs({"a": 1}, retries=3, backoff=0)
        post.assert_called_once()

    def test_malformed_body_raises_immediately_without_retry(self):
        resp = MagicMock(status_code=201)
        resp.json.return_value = {"nope": 1}  # no "link"
        post = MagicMock(return_value=resp)
        with patch("ogpu.ipfs.publish.requests.post", post):
            with pytest.raises(IPFSGatewayError):
                publish_to_ipfs({"a": 1}, retries=3, backoff=0)
        post.assert_called_once()

    def test_5xx_exhausted_raises_gateway_error(self):
        post = MagicMock(return_value=_http_response(502))
        with patch("ogpu.ipfs.publish.requests.post", post):
            with pytest.raises(IPFSGatewayError) as exc_info:
                publish_to_ipfs({"a": 1}, retries=2, backoff=0)
        assert exc_info.value.status_code == 502
        assert post.call_count == 2


class TestA3KnobsReachThePin:
    @pytest.fixture(autouse=True)
    def _signer_env(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", _HEX_KEY)

    def test_ipfs_knobs_passed_through_publish_task(self):
        receipt = MagicMock()
        with (
            patch("ogpu.client.publish_to_ipfs", return_value="ipfs://X") as pin,
            patch("ogpu.protocol.controller.publish_task", return_value=receipt),
            patch("ogpu.protocol.controller.extract_task_address", return_value=_SOURCE),
        ):
            client.publish_task(
                _task_info(), ipfs_timeout=7, ipfs_retries=4, ipfs_backoff=0.9
            )
        kwargs = pin.call_args.kwargs
        assert kwargs["timeout"] == 7
        assert kwargs["retries"] == 4
        assert kwargs["backoff"] == 0.9

    def test_nonce_retry_does_not_repin(self):
        """One pin per publish_task call even when the tx layer retries."""

        calls = {"send": 0}

        def flaky_send(raw):
            calls["send"] += 1
            if calls["send"] == 1:
                raise ValueError("nonce too low")
            return bytes.fromhex("a" * 64)

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"r")
        web3.eth.send_raw_transaction.side_effect = flaky_send
        web3.eth.wait_for_transaction_receipt.return_value = {
            "transactionHash": bytes.fromhex("a" * 64),
            "blockNumber": 1,
            "gasUsed": 21000,
            "status": 1,
            "logs": [],
        }
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(return_value={"from": "0x1", "nonce": 5})
        contract.functions.publishTask = MagicMock(return_value=fn)

        pin = MagicMock(return_value="ipfs://X")
        with (
            patch("ogpu.client.publish_to_ipfs", pin),
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.protocol.controller.load_contract", return_value=contract),
            patch("ogpu.protocol.controller.extract_task_address", return_value=_SOURCE),
        ):
            client.publish_task(_task_info())

        assert calls["send"] == 2  # the tx layer retried...
        pin.assert_called_once()  # ...but the pin happened exactly once


class TestA4ReceiptTimeout:
    def _executor_env(self):
        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"r")
        web3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
        web3.eth.wait_for_transaction_receipt.side_effect = TimeExhausted("no receipt")
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(return_value={"from": "0x1", "nonce": 5})
        contract.functions.doThing = MagicMock(return_value=fn)
        return web3, contract

    def test_raises_typed_error_with_tx_hash(self, sample_account):
        from ogpu.protocol._base import TxExecutor

        web3, contract = self._executor_env()
        with patch("ogpu.protocol._base._get_web3", return_value=web3):
            executor = TxExecutor(
                contract, "doThing", signer=sample_account, receipt_timeout=5
            )
            with pytest.raises(TxReceiptTimeoutError) as exc_info:
                executor.execute()
        # explicit timeout reaches web3 — never the implicit 120s default
        assert web3.eth.wait_for_transaction_receipt.call_args.kwargs["timeout"] == 5
        assert exc_info.value.tx_hash == "a" * 64
        assert exc_info.value.timeout == 5
        # broadcast happened: it must NOT retry/re-send
        web3.eth.send_raw_transaction.assert_called_once()


class TestA5TotalBudget:
    @pytest.fixture(autouse=True)
    def _signer_env(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", _HEX_KEY)

    def test_hung_ipfs_leg_respects_budget(self):
        """IPFS attempts are capped at the remaining budget, not ipfs_timeout."""

        def slow_post(url, files=None, timeout=None):
            # the SDK must shrink our per-attempt timeout to the budget
            assert timeout is not None and timeout <= 1.0
            raise requests.Timeout(f"stall (timeout={timeout})")

        started = time.monotonic()
        with patch("ogpu.ipfs.publish.requests.post", side_effect=slow_post):
            with pytest.raises(IPFSFetchError):
                client.publish_task(_task_info(), total_timeout=1.0, ipfs_retries=5)
        assert time.monotonic() - started < 2.5

    def test_budget_exhausted_before_tx_never_broadcasts(self):
        """Pin eats the whole budget → PublishTimeoutError, zero broadcasts."""

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5

        def slow_pin(*a, **kw):
            time.sleep(0.3)
            return "ipfs://X"

        with (
            patch("ogpu.client.publish_to_ipfs", side_effect=slow_pin),
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.protocol.controller.load_contract", return_value=MagicMock()),
        ):
            with pytest.raises(PublishTimeoutError) as exc_info:
                client.publish_task(_task_info(), total_timeout=0.2)
        assert exc_info.value.stage == "pre-transaction"
        web3.eth.send_raw_transaction.assert_not_called()

    def test_receipt_wait_capped_by_remaining_budget(self, sample_account):
        from ogpu.protocol._base import TxExecutor

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"r")
        web3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
        web3.eth.wait_for_transaction_receipt.side_effect = TimeExhausted("no receipt")
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(return_value={"from": "0x1", "nonce": 5})
        contract.functions.doThing = MagicMock(return_value=fn)

        with patch("ogpu.protocol._base._get_web3", return_value=web3):
            executor = TxExecutor(
                contract,
                "doThing",
                signer=sample_account,
                receipt_timeout=120,
                deadline=time.monotonic() + 3.0,
                budget=3.0,
            )
            with pytest.raises(TxReceiptTimeoutError):
                executor.execute()
        used = web3.eth.wait_for_transaction_receipt.call_args.kwargs["timeout"]
        assert used <= 3.0  # capped by remaining budget, not the 120s default


class TestA6DistinctTypedErrors:
    """Each induced failure → a distinct OGPUError subclass; nothing raw."""

    @pytest.fixture(autouse=True)
    def _signer_env(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", _HEX_KEY)

    def test_ipfs_down_raises_ipfs_error(self):
        with patch(
            "ogpu.ipfs.publish.requests.post", side_effect=requests.ConnectionError("down")
        ):
            with pytest.raises(IPFSFetchError) as exc_info:
                client.publish_task(_task_info(), ipfs_retries=1)
        assert isinstance(exc_info.value, OGPUError)

    def test_unknown_rpc_failure_raises_tx_rpc_error(self, sample_account):
        from ogpu.protocol._base import TxExecutor

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(side_effect=ValueError("weird RPC response"))
        contract.functions.doThing = MagicMock(return_value=fn)

        with patch("ogpu.protocol._base._get_web3", return_value=web3):
            with pytest.raises(TxRpcError) as exc_info:
                TxExecutor(contract, "doThing", signer=sample_account).execute()
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_transient_block_not_found_is_retried(self, sample_account):
        """The lagging-replica error observed on mainnet gets one more try."""
        from ogpu.protocol._base import TxExecutor

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"r")
        web3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)
        web3.eth.wait_for_transaction_receipt.return_value = {
            "transactionHash": bytes.fromhex("a" * 64),
            "blockNumber": 1,
            "gasUsed": 21000,
            "status": 1,
            "logs": [],
        }
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(
            side_effect=[ValueError("block 0x13f67ef not found"), {"from": "0x1", "nonce": 5}]
        )
        contract.functions.doThing = MagicMock(return_value=fn)

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.protocol._base._TRANSIENT_RPC_BACKOFF_SECONDS", 0),
        ):
            receipt = TxExecutor(contract, "doThing", signer=sample_account).execute()
        assert receipt.status == 1
        assert fn.build_transaction.call_count == 2

    def test_nonce_exhausted_raises_nonce_error(self, sample_account):
        from ogpu.protocol._base import TxExecutor

        web3 = MagicMock()
        web3.to_checksum_address = lambda a: a
        web3.eth.get_transaction_count.return_value = 5
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"r")
        web3.eth.send_raw_transaction.side_effect = ValueError("nonce too low")
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(return_value={"from": "0x1", "nonce": 5})
        contract.functions.doThing = MagicMock(return_value=fn)

        with patch("ogpu.protocol._base._get_web3", return_value=web3):
            with pytest.raises(NonceError):
                TxExecutor(
                    contract, "doThing", signer=sample_account, max_retries=2
                ).execute()


class TestA8StableImportPaths:
    def test_022_import_paths_still_work(self):
        from ogpu import ChainConfig, ChainId, fetch_ipfs_json, publish_to_ipfs, set_verbose
        from ogpu.client import TaskInfo, TaskInput, publish_task

        for obj in (
            ChainConfig,
            ChainId,
            publish_to_ipfs,
            fetch_ipfs_json,
            set_verbose,
            publish_task,
            TaskInfo,
            TaskInput,
        ):
            assert obj is not None

    def test_private_key_kwarg_still_accepted(self):
        """Relay passes private_key= explicitly — must stay accepted."""
        import inspect

        sig = inspect.signature(client.publish_task)
        assert "private_key" in sig.parameters
