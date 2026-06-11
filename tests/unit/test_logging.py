"""``ogpu.set_verbose`` and the SDK logger hierarchy."""

import logging

import pytest

import ogpu
from ogpu._logging import _apply_env_verbose


@pytest.fixture(autouse=True)
def _reset_verbose():
    yield
    ogpu.set_verbose(False)


class TestSetVerbose:
    def test_attaches_single_handler(self):
        root = logging.getLogger("ogpu")
        before = list(root.handlers)

        ogpu.set_verbose()
        ogpu.set_verbose()  # idempotent — no duplicate handlers

        added = [h for h in root.handlers if h not in before]
        assert len(added) == 1
        assert root.level == logging.DEBUG

    def test_disable_removes_handler(self):
        root = logging.getLogger("ogpu")
        before = list(root.handlers)

        ogpu.set_verbose()
        ogpu.set_verbose(False)

        assert list(root.handlers) == before
        assert root.level == logging.NOTSET

    def test_custom_level(self):
        ogpu.set_verbose(level=logging.INFO)
        assert logging.getLogger("ogpu").level == logging.INFO

    def test_timestamp_format_has_milliseconds(self):
        ogpu.set_verbose()
        from ogpu._logging import _verbose_handler

        record = logging.LogRecord("ogpu.tx", logging.INFO, "", 0, "mined", (), None)
        line = _verbose_handler.format(record)
        # HH:MM:SS.mmm prefix
        import re

        assert re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} ", line), line


class TestEnvVerbose:
    @pytest.mark.parametrize("value", ["1", "true", "YES"])
    def test_enables_from_env(self, monkeypatch, value):
        monkeypatch.setenv("OGPU_VERBOSE", value)
        _apply_env_verbose()
        assert logging.getLogger("ogpu").level == logging.DEBUG

    @pytest.mark.parametrize("value", ["", "0", "false", "no"])
    def test_ignores_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("OGPU_VERBOSE", value)
        _apply_env_verbose()
        assert logging.getLogger("ogpu").level == logging.NOTSET


class TestInstrumentation:
    def test_ipfs_publish_logs_duration(self, caplog):
        from unittest.mock import MagicMock, patch

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"link": "https://gw/ipfs/Qm123"}

        with caplog.at_level(logging.DEBUG, logger="ogpu.ipfs"):
            with patch("ogpu.ipfs.publish.requests.post", return_value=mock_resp):
                ogpu.publish_to_ipfs({"a": 1}, filename="x.json")

        messages = [r.message for r in caplog.records]
        assert any("publishing x.json" in m for m in messages)
        assert any("IPFS pin ok in" in m and "Qm123" in m for m in messages)
