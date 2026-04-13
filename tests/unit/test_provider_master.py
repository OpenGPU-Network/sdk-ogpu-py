"""Provider and Master synthetic classes — full delegation tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.protocol.master import Master
from ogpu.protocol.provider import Provider
from ogpu.types.errors import MasterNotFoundError, ProviderNotFoundError
from ogpu.types.receipt import Receipt

_ADDR = "0x" + "aa" * 20
_KEY = "0x" + "11" * 32
_FAKE_WEB3 = MagicMock()
_FAKE_WEB3.to_checksum_address = lambda a: a


def _pw3():
    return patch("ogpu.protocol._base._get_web3", return_value=_FAKE_WEB3)


def _r():
    return Receipt(tx_hash="0x1", block_number=1, gas_used=1, status=1)


def _prov():
    with _pw3():
        return Provider(_ADDR)


def _mast():
    with _pw3():
        return Master(_ADDR)


# =========================================================================
# Provider
# =========================================================================


class TestProviderLoad:
    def test_load_success(self):
        with _pw3(), patch("ogpu.protocol.terminal.is_provider", return_value=True):
            assert Provider.load(_ADDR).address == _ADDR

    def test_load_not_found(self):
        with _pw3(), patch("ogpu.protocol.terminal.is_provider", return_value=False):
            with pytest.raises(ProviderNotFoundError):
                Provider.load(_ADDR)


class TestProviderTerminalReads:
    def test_get_master(self):
        with patch("ogpu.protocol.terminal.get_master_of", return_value="0xM"):
            assert _prov().get_master() == "0xM"

    def test_get_base_data(self):
        with patch("ogpu.protocol.terminal.get_base_data_of", return_value="ipfs://b"):
            assert _prov().get_base_data() == "ipfs://b"

    def test_get_live_data(self):
        with patch("ogpu.protocol.terminal.get_live_data_of", return_value="ipfs://l"):
            assert _prov().get_live_data() == "ipfs://l"

    def test_is_provider(self):
        with patch("ogpu.protocol.terminal.is_provider", return_value=True):
            assert _prov().is_provider() is True

    def test_get_default_agent_disabled(self):
        with patch("ogpu.protocol.terminal.is_default_agent_disabled", return_value=False):
            assert _prov().get_default_agent_disabled() is False


class TestProviderVaultReads:
    def test_get_balance(self):
        with patch("ogpu.protocol.vault.get_balance_of", return_value=1000):
            assert _prov().get_balance() == 1000

    def test_get_lockup(self):
        with patch("ogpu.protocol.vault.get_lockup_of", return_value=500):
            assert _prov().get_lockup() == 500

    def test_get_unbonding(self):
        with patch("ogpu.protocol.vault.get_unbonding_of", return_value=100):
            assert _prov().get_unbonding() == 100

    def test_get_unbonding_timestamp(self):
        with patch("ogpu.protocol.vault.get_unbonding_timestamp", return_value=9999):
            assert _prov().get_unbonding_timestamp() == 9999

    def test_get_total_earnings(self):
        with patch("ogpu.protocol.vault.get_total_earnings_of", return_value=5000):
            assert _prov().get_total_earnings() == 5000

    def test_get_frozen_payment(self):
        with patch("ogpu.protocol.vault.get_frozen_payment", return_value=200):
            assert _prov().get_frozen_payment() == 200

    def test_get_sanction(self):
        with patch("ogpu.protocol.vault.get_sanction_of", return_value=0):
            assert _prov().get_sanction() == 0

    def test_is_eligible(self):
        with patch("ogpu.protocol.vault.is_eligible", return_value=True):
            assert _prov().is_eligible() is True

    def test_is_whitelisted(self):
        with patch("ogpu.protocol.vault.is_whitelisted", return_value=False):
            assert _prov().is_whitelisted() is False


class TestProviderTerminalWrites:
    def test_announce_master(self):
        with patch("ogpu.protocol.terminal.announce_master", return_value=_r()) as m:
            _prov().announce_master("0xM", signer=_KEY)
        m.assert_called_once_with("0xM", signer=_KEY)

    def test_set_default_agent_disabled(self):
        with patch("ogpu.protocol.terminal.set_default_agent_disabled", return_value=_r()) as m:
            _prov().set_default_agent_disabled(True, signer=_KEY)
        m.assert_called_once_with(True, signer=_KEY)


class TestProviderNexusWrites:
    def test_register_to(self):
        with patch("ogpu.protocol.nexus.register", return_value=_r()) as m:
            _prov().register_to("0xSRC", env=1, signer=_KEY)
        m.assert_called_once_with("0xSRC", _ADDR, 1, signer=_KEY)

    def test_unregister_from(self):
        with patch("ogpu.protocol.nexus.unregister", return_value=_r()) as m:
            _prov().unregister_from("0xSRC", signer=_KEY)
        m.assert_called_once_with("0xSRC", _ADDR, signer=_KEY)

    def test_attempt(self):
        with patch("ogpu.protocol.nexus.attempt", return_value=_r()) as m:
            _prov().attempt("0xTASK", 100, signer=_KEY)
        m.assert_called_once_with("0xTASK", _ADDR, 100, signer=_KEY)


class TestProviderVaultWrites:
    def test_stake(self):
        with patch("ogpu.protocol.vault.lock", return_value=_r()) as m:
            _prov().stake(500, signer=_KEY)
        m.assert_called_once_with(500, signer=_KEY)

    def test_unstake(self):
        with patch("ogpu.protocol.vault.unbond", return_value=_r()) as m:
            _prov().unstake(200, signer=_KEY)
        m.assert_called_once_with(200, signer=_KEY)

    def test_cancel_unbonding(self):
        with patch("ogpu.protocol.vault.cancel_unbonding", return_value=_r()) as m:
            _prov().cancel_unbonding(signer=_KEY)
        m.assert_called_once_with(signer=_KEY)

    def test_claim_earnings(self):
        with patch("ogpu.protocol.vault.claim", return_value=_r()) as m:
            _prov().claim_earnings(signer=_KEY)
        m.assert_called_once_with(signer=_KEY)

    def test_deposit_to_vault(self):
        with patch("ogpu.protocol.vault.deposit", return_value=_r()) as m:
            _prov().deposit_to_vault(1000, signer=_KEY)
        m.assert_called_once_with(_ADDR, 1000, signer=_KEY)

    def test_withdraw_from_vault(self):
        with patch("ogpu.protocol.vault.withdraw", return_value=_r()) as m:
            _prov().withdraw_from_vault(300, signer=_KEY)
        m.assert_called_once_with(300, signer=_KEY)


class TestProviderSnapshot:
    def test_snapshot(self):
        patches = {
            "ogpu.protocol.terminal.get_master_of": "0xM",
            "ogpu.protocol.terminal.get_base_data_of": "base",
            "ogpu.protocol.terminal.get_live_data_of": "live",
            "ogpu.protocol.terminal.is_provider": True,
            "ogpu.protocol.terminal.is_default_agent_disabled": False,
            "ogpu.protocol.vault.get_balance_of": 1000,
            "ogpu.protocol.vault.get_lockup_of": 500,
            "ogpu.protocol.vault.get_unbonding_of": 0,
            "ogpu.protocol.vault.get_unbonding_timestamp": 0,
            "ogpu.protocol.vault.get_total_earnings_of": 2000,
            "ogpu.protocol.vault.get_frozen_payment": 100,
            "ogpu.protocol.vault.get_sanction_of": 0,
            "ogpu.protocol.vault.is_eligible": True,
            "ogpu.protocol.vault.is_whitelisted": True,
        }
        ctx = [patch(k, return_value=v) for k, v in patches.items()]
        p = _prov()
        for c in ctx:
            c.start()
        try:
            snap = p.snapshot()
        finally:
            for c in ctx:
                c.stop()
        assert snap.address == _ADDR
        assert snap.master == "0xM"
        assert snap.balance == 1000
        assert snap.is_eligible is True


class TestProviderDunder:
    def test_eq(self):
        assert _prov() == _prov()

    def test_neq(self):
        with _pw3():
            assert _prov() != Provider("0x" + "bb" * 20)

    def test_str(self):
        assert str(_prov()) == _ADDR

    def test_repr(self):
        assert "<Provider" in repr(_prov())

    def test_hash(self):
        assert hash(_prov()) == hash(_prov())


# =========================================================================
# Master
# =========================================================================


class TestMasterLoad:
    def test_load_success(self):
        with _pw3(), patch("ogpu.protocol.terminal.is_master", return_value=True):
            assert Master.load(_ADDR).address == _ADDR

    def test_load_not_found(self):
        with _pw3(), patch("ogpu.protocol.terminal.is_master", return_value=False):
            with pytest.raises(MasterNotFoundError):
                Master.load(_ADDR)


class TestMasterReads:
    def test_get_provider(self):
        with patch("ogpu.protocol.terminal.get_provider_of", return_value="0xP"):
            assert _mast().get_provider() == "0xP"

    def test_is_master(self):
        with patch("ogpu.protocol.terminal.is_master", return_value=True):
            assert _mast().is_master() is True

    def test_get_balance(self):
        with patch("ogpu.protocol.vault.get_balance_of", return_value=2000):
            assert _mast().get_balance() == 2000

    def test_get_lockup(self):
        with patch("ogpu.protocol.vault.get_lockup_of", return_value=800):
            assert _mast().get_lockup() == 800

    def test_get_unbonding(self):
        with patch("ogpu.protocol.vault.get_unbonding_of", return_value=50):
            assert _mast().get_unbonding() == 50

    def test_get_total_earnings(self):
        with patch("ogpu.protocol.vault.get_total_earnings_of", return_value=3000):
            assert _mast().get_total_earnings() == 3000

    def test_get_frozen_payment(self):
        with patch("ogpu.protocol.vault.get_frozen_payment", return_value=150):
            assert _mast().get_frozen_payment() == 150

    def test_is_eligible(self):
        with patch("ogpu.protocol.vault.is_eligible", return_value=True):
            assert _mast().is_eligible() is True

    def test_is_whitelisted(self):
        with patch("ogpu.protocol.vault.is_whitelisted", return_value=True):
            assert _mast().is_whitelisted() is True


class TestMasterWrites:
    def test_announce_provider(self):
        with patch("ogpu.protocol.terminal.announce_provider", return_value=_r()) as m:
            _mast().announce_provider("0xP", 100, signer=_KEY)
        m.assert_called_once_with("0xP", 100, signer=_KEY)

    def test_remove_provider(self):
        with patch("ogpu.protocol.terminal.remove_provider", return_value=_r()) as m:
            _mast().remove_provider("0xP", signer=_KEY)
        m.assert_called_once_with("0xP", signer=_KEY)

    def test_remove_container(self):
        with patch("ogpu.protocol.terminal.remove_container", return_value=_r()) as m:
            _mast().remove_container("0xP", "0xS", signer=_KEY)
        m.assert_called_once_with("0xP", "0xS", signer=_KEY)

    def test_set_agent(self):
        with patch("ogpu.protocol.terminal.set_agent", return_value=_r()) as m:
            _mast().set_agent("0xA", True, signer=_KEY)
        m.assert_called_once_with("0xA", True, signer=_KEY)

    def test_stake(self):
        with patch("ogpu.protocol.vault.lock", return_value=_r()) as m:
            _mast().stake(500, signer=_KEY)
        m.assert_called_once_with(500, signer=_KEY)

    def test_unstake(self):
        with patch("ogpu.protocol.vault.unbond", return_value=_r()) as m:
            _mast().unstake(200, signer=_KEY)
        m.assert_called_once_with(200, signer=_KEY)

    def test_cancel_unbonding(self):
        with patch("ogpu.protocol.vault.cancel_unbonding", return_value=_r()) as m:
            _mast().cancel_unbonding(signer=_KEY)
        m.assert_called_once_with(signer=_KEY)

    def test_claim_earnings(self):
        with patch("ogpu.protocol.vault.claim", return_value=_r()) as m:
            _mast().claim_earnings(signer=_KEY)
        m.assert_called_once_with(signer=_KEY)

    def test_deposit_to_vault(self):
        with patch("ogpu.protocol.vault.deposit", return_value=_r()) as m:
            _mast().deposit_to_vault(1000, signer=_KEY)
        m.assert_called_once_with(_ADDR, 1000, signer=_KEY)

    def test_withdraw_from_vault(self):
        with patch("ogpu.protocol.vault.withdraw", return_value=_r()) as m:
            _mast().withdraw_from_vault(300, signer=_KEY)
        m.assert_called_once_with(300, signer=_KEY)


class TestMasterSnapshot:
    def test_snapshot(self):
        patches = {
            "ogpu.protocol.terminal.get_provider_of": "0xP",
            "ogpu.protocol.terminal.is_master": True,
            "ogpu.protocol.vault.get_balance_of": 2000,
            "ogpu.protocol.vault.get_lockup_of": 800,
            "ogpu.protocol.vault.get_unbonding_of": 50,
            "ogpu.protocol.vault.get_total_earnings_of": 3000,
            "ogpu.protocol.vault.get_frozen_payment": 150,
            "ogpu.protocol.vault.is_eligible": True,
            "ogpu.protocol.vault.is_whitelisted": True,
        }
        ctx = [patch(k, return_value=v) for k, v in patches.items()]
        m = _mast()
        for c in ctx:
            c.start()
        try:
            snap = m.snapshot()
        finally:
            for c in ctx:
                c.stop()
        assert snap.address == _ADDR
        assert snap.provider == "0xP"
        assert snap.balance == 2000
        assert snap.is_master is True


class TestMasterDunder:
    def test_eq(self):
        assert _mast() == _mast()

    def test_str(self):
        assert str(_mast()) == _ADDR

    def test_repr(self):
        assert "<Master" in repr(_mast())
