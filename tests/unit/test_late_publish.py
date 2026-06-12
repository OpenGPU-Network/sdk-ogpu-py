"""Late-publish regression suite — degraded IPFS/RPC must never orphan a task.

The incident being guarded against (reported by the Relay team on
0.2.0.x): the IPFS pin stalled, the caller's watchdog gave up, the SDK
thread kept blocking, and when IPFS finally answered the transaction
fired anyway — landing an on-chain task minutes late, with 0 attempters,
expiring unused while still costing gas.

These tests simulate the degraded network deterministically with a real
local HTTP server whose response delay is configurable, then assert the
two SDK defenses:

1. ``publish_to_ipfs`` raises after ``timeout`` instead of blocking.
2. ``publish_task`` refuses to send the transaction once ``expiryTime``
   has passed — even if the pin eventually succeeded.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import pytest

import ogpu.client as client
from ogpu.client import TaskInfo, TaskInput
from ogpu.ipfs import publish_to_ipfs
from ogpu.types.errors import IPFSFetchError, TaskExpiredError

SOURCE = "0x" + "ab" * 20


# ---------------------------------------------------------------------------
# Slow IPFS endpoint — a real HTTP server with configurable response delay
# ---------------------------------------------------------------------------


class _SlowHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 — http.server API
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        time.sleep(self.server.delay)  # type: ignore[attr-defined]
        body = json.dumps({"link": "https://gw/ipfs/QmSlow"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence request logging
        pass


@pytest.fixture
def slow_ipfs():
    """Yield a function that starts a local IPFS stand-in with a given delay.

    Returns the URL to patch into ``ogpu.ipfs.publish._IPFS_PUBLISH_URL``.
    """
    servers: list[ThreadingHTTPServer] = []

    def start(delay: float) -> str:
        # daemon_threads: teardown must not block on a handler that is
        # still mid-sleep after the client side already timed out.
        server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowHandler)
        server.daemon_threads = True
        server.delay = delay  # type: ignore[attr-defined]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}/file/create"

    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


def _task_info(expiry_offset: float) -> TaskInfo:
    return TaskInfo(
        source=SOURCE,
        config=TaskInput(function_name="chat", data={"x": 1}),
        expiryTime=int(time.time() + expiry_offset),
        payment=10**15,
    )


# ---------------------------------------------------------------------------
# Defense 1: bounded IPFS calls
# ---------------------------------------------------------------------------


class TestIPFSTimeout:
    def test_stalled_endpoint_raises_within_timeout(self, slow_ipfs):
        """A stalled pin must raise promptly — not block until the server feels like answering."""
        url = slow_ipfs(delay=2.0)
        started = time.monotonic()
        with patch("ogpu.ipfs.publish._IPFS_PUBLISH_URL", url):
            with pytest.raises(IPFSFetchError):
                publish_to_ipfs({"a": 1}, timeout=0.3)
        elapsed = time.monotonic() - started
        assert elapsed < 1.5, f"timeout not enforced: took {elapsed:.1f}s"

    def test_slow_but_responsive_endpoint_succeeds(self, slow_ipfs):
        url = slow_ipfs(delay=0.3)
        with patch("ogpu.ipfs.publish._IPFS_PUBLISH_URL", url):
            link = publish_to_ipfs({"a": 1}, timeout=5)
        assert link == "https://gw/ipfs/QmSlow"


# ---------------------------------------------------------------------------
# Defense 2: never send a transaction for an already-expired task
# ---------------------------------------------------------------------------


class TestExpiryGuard:
    @pytest.fixture(autouse=True)
    def _signer_env(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", "0x" + "11" * 32)

    def test_already_expired_fails_fast_without_ipfs(self):
        """Expired before we even start → no pin, no transaction."""
        with (
            patch("ogpu.client.publish_to_ipfs") as pin,
            patch("ogpu.protocol.controller.publish_task") as send,
        ):
            with pytest.raises(TaskExpiredError):
                client.publish_task(_task_info(expiry_offset=-10))
        pin.assert_not_called()
        send.assert_not_called()

    def test_slow_pin_eating_past_expiry_blocks_transaction(self, slow_ipfs):
        """The pin succeeds, but too late — the transaction must NOT fire."""
        url = slow_ipfs(delay=1.5)
        with (
            patch("ogpu.ipfs.publish._IPFS_PUBLISH_URL", url),
            patch("ogpu.protocol.controller.publish_task") as send,
        ):
            with pytest.raises(TaskExpiredError):
                client.publish_task(_task_info(expiry_offset=1.0))
        send.assert_not_called()

    def test_relay_incident_replay(self, slow_ipfs):
        """Full incident: caller watchdog abandons, SDK thread must still not publish.

        Timeline (compressed from the original minutes to ~2s):
        - t=0    caller starts publish_task in a thread, watchdog = 0.5s
        - t=0.5  watchdog fires, caller abandons the wait
        - t=2    IPFS finally answers — but expiryTime (t=1) has passed
        - then   the SDK must raise, NOT send the transaction
        """
        url = slow_ipfs(delay=2.0)
        outcome: dict = {}

        def run():
            try:
                outcome["task"] = client.publish_task(_task_info(expiry_offset=1.0))
            except Exception as exc:  # noqa: BLE001 — recorded for assertion
                outcome["error"] = exc

        with (
            patch("ogpu.ipfs.publish._IPFS_PUBLISH_URL", url),
            patch("ogpu.protocol.controller.publish_task") as send,
        ):
            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            worker.join(timeout=0.5)
            assert worker.is_alive(), "watchdog window: SDK should still be pinning"
            # caller has now "given up" — the SDK thread keeps running
            worker.join(timeout=5.0)
            assert not worker.is_alive()

        assert isinstance(outcome.get("error"), TaskExpiredError)
        assert "task" not in outcome
        send.assert_not_called()  # the old behavior fired the tx here

    def test_healthy_flow_unaffected(self):
        """Sanity: with a fast pin and future expiry the publish goes through."""
        receipt = MagicMock()
        with (
            patch("ogpu.client.publish_to_ipfs", return_value="https://gw/ipfs/Qm1"),
            patch("ogpu.protocol.controller.publish_task", return_value=receipt) as send,
            patch(
                "ogpu.protocol.controller.extract_task_address",
                return_value="0x" + "cd" * 20,
            ),
        ):
            task = client.publish_task(_task_info(expiry_offset=3600))
        send.assert_called_once()
        assert task.address.lower() == "0x" + "cd" * 20  # Task checksums the address

    def test_guard_logs_warning(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="ogpu.client"):
            with pytest.raises(TaskExpiredError):
                client.publish_task(_task_info(expiry_offset=-1))
        assert any("would be orphaned" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Observability: a slow RPC stage must be attributable from the logs
# ---------------------------------------------------------------------------


class TestSlowRpcVisibility:
    def test_receipt_wait_duration_logged(self, sample_account, caplog):
        import logging

        from ogpu.protocol._base import TxExecutor

        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        fn = MagicMock()
        fn.build_transaction = MagicMock(return_value={"from": "0x1", "nonce": 0})
        contract.functions.doThing = MagicMock(return_value=fn)

        web3 = MagicMock()
        web3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"raw")
        web3.eth.send_raw_transaction.return_value = bytes.fromhex("a" * 64)

        def slow_receipt(tx_hash, timeout=None):
            time.sleep(0.3)  # simulated congested RPC
            return {
                "transactionHash": bytes.fromhex("a" * 64),
                "blockNumber": 7,
                "gasUsed": 21000,
                "status": 1,
                "logs": [],
            }

        web3.eth.wait_for_transaction_receipt.side_effect = slow_receipt

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.chain.nonce.NonceManager.reserve_nonce", return_value=5),
            caplog.at_level(logging.DEBUG, logger="ogpu.tx"),
        ):
            TxExecutor(contract, "doThing", signer=sample_account).execute()

        mined = [r.message for r in caplog.records if "mined in block" in r.message]
        assert len(mined) == 1
        # the 0.3s receipt stall must be attributed to the receipt wait
        # (upper bound generous: loaded CI machines oversleep)
        import re

        match = re.search(r"receipt wait (\d+\.\d)s", mined[0])
        assert match, mined[0]
        assert 0.25 <= float(match.group(1)) <= 1.5, mined[0]
