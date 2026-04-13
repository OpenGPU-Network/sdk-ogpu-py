"""ogpu.agent high-level wrappers — mock tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from eth_account import Account

from ogpu import agent
from ogpu.types.enums import Role
from ogpu.types.errors import MissingSignerError
from ogpu.types.receipt import Receipt

_KEY = "0x" + "11" * 32
_AGENT_ADDR = Account.from_key(_KEY).address
_PROVIDER = "0x" + "aa" * 20
_SOURCE = "0x" + "bb" * 20
_TASK = "0x" + "cc" * 20


def _receipt() -> Receipt:
    return Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)


class TestAgentRegisterTo:
    def test_explicit_key_passes_account_to_protocol(self):
        with patch("ogpu.protocol.nexus.register", return_value=_receipt()) as m:
            result = agent.register_to(_SOURCE, _PROVIDER, 1, private_key=_KEY)
        assert result.tx_hash == "0xhash"
        # Protocol received a LocalAccount, not a raw string
        call_args = m.call_args
        assert call_args.args[:3] == (_SOURCE, _PROVIDER, 1)
        signer = call_args.kwargs["signer"]
        assert signer.address == _AGENT_ADDR

    def test_env_fallback_reads_agent_private_key(self, monkeypatch):
        monkeypatch.setenv("AGENT_PRIVATE_KEY", _KEY)
        with patch("ogpu.protocol.nexus.register", return_value=_receipt()) as m:
            agent.register_to(_SOURCE, _PROVIDER, 1)
        signer = m.call_args.kwargs["signer"]
        assert signer.address == _AGENT_ADDR

    def test_missing_env_raises(self, monkeypatch):
        monkeypatch.delenv("AGENT_PRIVATE_KEY", raising=False)
        with pytest.raises(MissingSignerError) as exc:
            agent.register_to(_SOURCE, _PROVIDER, 1)
        assert exc.value.role == Role.AGENT


class TestAgentUnregisterFrom:
    def test_delegates(self):
        with patch("ogpu.protocol.nexus.unregister", return_value=_receipt()) as m:
            agent.unregister_from(_SOURCE, _PROVIDER, private_key=_KEY)
        assert m.call_args.args[:2] == (_SOURCE, _PROVIDER)
        assert m.call_args.kwargs["signer"].address == _AGENT_ADDR


class TestAgentAttempt:
    def test_delegates(self):
        with patch("ogpu.protocol.nexus.attempt", return_value=_receipt()) as m:
            agent.attempt(_TASK, _PROVIDER, suggested_payment=100, private_key=_KEY)
        assert m.call_args.args == (_TASK, _PROVIDER, 100)


class TestIgnoredKwargs:
    def test_old_style_kwargs_ignored(self):
        """Wrappers should accept extra kwargs silently (parallel with ogpu.client)."""
        with patch("ogpu.protocol.nexus.register", return_value=_receipt()):
            agent.register_to(
                _SOURCE, _PROVIDER, 1,
                private_key=_KEY,
                nonce=42, auto_fix_nonce=False, max_retries=9,
            )
