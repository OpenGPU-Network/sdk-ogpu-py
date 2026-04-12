"""Vault module — mock unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.protocol import vault
from ogpu.types.errors import MissingSignerError
from ogpu.types.receipt import Receipt

_KEY = "0x" + "11" * 32
_ADDR = "0x" + "aa" * 20
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _receipt():
    return Receipt(tx_hash="0xhash", block_number=1, gas_used=1, status=1)


def _patch_exec():
    return patch("ogpu.protocol._base.TxExecutor.execute", return_value=_receipt())


def _patch_contract():
    c = MagicMock()
    return c, patch("ogpu.protocol.vault.load_contract", return_value=c)


class TestVaultWrites:
    def test_deposit(self):
        c, pc = _patch_contract()
        with pc, _patch_exec(), patch("ogpu.protocol.vault._get_web3", return_value=_FAKE_WEB3):
            r = vault.deposit(_ADDR, 1000, signer=_KEY)
        assert r.tx_hash == "0xhash"

    def test_withdraw(self):
        _, pc = _patch_contract()
        with pc, _patch_exec():
            r = vault.withdraw(500, signer=_KEY)
        assert r.status == 1

    def test_lock(self):
        _, pc = _patch_contract()
        with pc, _patch_exec():
            r = vault.lock(100, signer=_KEY)
        assert r.status == 1

    def test_unbond(self):
        _, pc = _patch_contract()
        with pc, _patch_exec():
            r = vault.unbond(50, signer=_KEY)
        assert r.status == 1

    def test_cancel_unbonding(self):
        _, pc = _patch_contract()
        with pc, _patch_exec():
            r = vault.cancel_unbonding(signer=_KEY)
        assert r.status == 1

    def test_claim(self):
        _, pc = _patch_contract()
        with pc, _patch_exec():
            r = vault.claim(signer=_KEY)
        assert r.status == 1

    def test_no_signer_raises(self):
        with pytest.raises(TypeError):
            vault.deposit(_ADDR, 1000)  # type: ignore[call-arg]


class TestVaultReads:
    def _mock_vault(self, fn_name, ret):
        c = MagicMock()
        getattr(c.functions, fn_name).return_value.call.return_value = ret
        return patch("ogpu.protocol.vault.load_contract", return_value=c)

    def test_get_balance_of(self):
        with self._mock_vault("balanceOf", 1000):
            assert vault.get_balance_of(_ADDR) == 1000

    def test_get_lockup_of(self):
        with self._mock_vault("lockupOf", 500):
            assert vault.get_lockup_of(_ADDR) == 500

    def test_get_unbonding_of(self):
        with self._mock_vault("unbondingOf", 200):
            assert vault.get_unbonding_of(_ADDR) == 200

    def test_get_unbonding_timestamp(self):
        with self._mock_vault("unbondingTimestamp", 9999):
            assert vault.get_unbonding_timestamp(_ADDR) == 9999

    def test_get_total_earnings_of(self):
        with self._mock_vault("totalEarningsOf", 5000):
            assert vault.get_total_earnings_of(_ADDR) == 5000

    def test_get_frozen_payment(self):
        with self._mock_vault("frozenPayment", 100):
            assert vault.get_frozen_payment(_ADDR) == 100

    def test_get_sanction_of(self):
        with self._mock_vault("sanctionOf", 0):
            assert vault.get_sanction_of(_ADDR) == 0

    def test_is_eligible(self):
        with self._mock_vault("isEligible", True):
            assert vault.is_eligible(_ADDR) is True

    def test_is_whitelisted(self):
        with self._mock_vault("isWhitelisted", False):
            assert vault.is_whitelisted(_ADDR) is False

    def test_get_min_lockup_per_source(self):
        with self._mock_vault("MIN_LOCKUP_PER_SOURCE", 10**18):
            assert vault.get_min_lockup_per_source() == 10**18

    def test_get_unbonding_period(self):
        with self._mock_vault("UNBONDING_PERIOD", 86400):
            assert vault.get_unbonding_period() == 86400
