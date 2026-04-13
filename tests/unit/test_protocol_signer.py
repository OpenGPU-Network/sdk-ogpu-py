from __future__ import annotations

import pytest
from eth_account import Account
from eth_account.signers.local import LocalAccount

from ogpu.protocol._signer import resolve_signer
from ogpu.types.enums import Role
from ogpu.types.errors import InvalidSignerError, MissingSignerError

_HEX_KEY = "0x" + "11" * 32


class TestResolveSigner:
    def test_local_account_passthrough(self):
        acc = Account.from_key(_HEX_KEY)
        result = resolve_signer(acc, role=Role.CLIENT)
        assert result is acc
        assert isinstance(result, LocalAccount)

    def test_hex_string_parses_to_local_account(self):
        result = resolve_signer(_HEX_KEY, role=Role.CLIENT)
        assert isinstance(result, LocalAccount)
        assert result.address == Account.from_key(_HEX_KEY).address

    def test_env_var_fallback_client(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", _HEX_KEY)
        result = resolve_signer(None, role=Role.CLIENT)
        assert result.address == Account.from_key(_HEX_KEY).address

    def test_env_var_fallback_provider(self, monkeypatch):
        monkeypatch.setenv("PROVIDER_PRIVATE_KEY", _HEX_KEY)
        result = resolve_signer(None, role=Role.PROVIDER)
        assert isinstance(result, LocalAccount)

    def test_env_var_fallback_master(self, monkeypatch):
        monkeypatch.setenv("MASTER_PRIVATE_KEY", _HEX_KEY)
        result = resolve_signer(None, role=Role.MASTER)
        assert isinstance(result, LocalAccount)

    def test_missing_env_var_raises(self, monkeypatch):
        monkeypatch.delenv("CLIENT_PRIVATE_KEY", raising=False)
        with pytest.raises(MissingSignerError) as exc:
            resolve_signer(None, role=Role.CLIENT)
        assert exc.value.role == Role.CLIENT

    def test_vault_mode_rejects_none(self):
        with pytest.raises(MissingSignerError) as exc:
            resolve_signer(None, role=None)
        assert exc.value.role is None

    def test_invalid_hex_string(self):
        with pytest.raises(InvalidSignerError):
            resolve_signer("not-a-valid-key", role=Role.CLIENT)

    def test_unsupported_type(self):
        with pytest.raises(InvalidSignerError):
            resolve_signer(12345, role=Role.CLIENT)  # type: ignore[arg-type]

    def test_invalid_env_var_value(self, monkeypatch):
        monkeypatch.setenv("CLIENT_PRIVATE_KEY", "garbage")
        with pytest.raises(InvalidSignerError):
            resolve_signer(None, role=Role.CLIENT)
