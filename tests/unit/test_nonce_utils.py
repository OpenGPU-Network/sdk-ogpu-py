from __future__ import annotations

from unittest.mock import MagicMock, patch

from eth_account import Account

from ogpu.client.nonce_manager import NonceManager
from ogpu.client.nonce_utils import (
    clear_all_nonce_caches,
    fix_nonce,
    get_nonce_info,
    reset_nonce_cache,
)

_HEX_KEY = "0x" + "11" * 32


def _mock_web3(mined: int = 5, pending: int = 5, gas_price: int = 10**9, chain_id: int = 1071):
    web3 = MagicMock()
    web3.to_checksum_address = lambda a: a
    web3.eth.gas_price = gas_price
    web3.eth.chain_id = chain_id
    web3.eth.get_transaction_count.side_effect = lambda addr, block="latest": (
        mined if block == "latest" else pending
    )

    tx_hash = MagicMock()
    tx_hash.hex.return_value = "deadbeef"
    web3.eth.send_raw_transaction.return_value = tx_hash
    signed = MagicMock()
    signed.raw_transaction = b"raw"
    web3.eth.account.sign_transaction.return_value = signed
    return web3


class TestFixNonce:
    def test_no_pending_does_nothing(self):
        NonceManager.clear_all()
        web3 = _mock_web3(mined=5, pending=5)
        with patch("ogpu.client.nonce_utils.WEB3", return_value=web3):
            result = fix_nonce(private_key=_HEX_KEY)
        assert result == 5

    def test_pending_transactions_are_replaced(self):
        NonceManager.clear_all()
        web3 = _mock_web3(mined=5, pending=8)
        with patch("ogpu.client.nonce_utils.WEB3", return_value=web3):
            with patch("ogpu.client.nonce_utils.time.sleep"):
                result = fix_nonce(private_key=_HEX_KEY)
        # Should have attempted 3 replacement sends
        assert web3.eth.send_raw_transaction.call_count == 3
        assert result == 8


class TestResetNonceCache:
    def test_clears_single_address(self):
        NonceManager.clear_all()
        web3 = _mock_web3()
        with patch("ogpu.client.nonce_utils.WEB3", return_value=web3):
            NonceManager.get_nonce(
                Account.from_key(_HEX_KEY).address, web3
            )
            reset_nonce_cache(private_key=_HEX_KEY)
        assert (
            NonceManager.get_cached_nonce(
                Account.from_key(_HEX_KEY).address, web3
            )
            is None
        )


class TestClearAllNonceCaches:
    def test_clears_everything(self):
        web3 = _mock_web3()
        NonceManager.get_nonce("0xA", web3)
        NonceManager.get_nonce("0xB", web3)
        clear_all_nonce_caches()
        assert NonceManager.get_cached_nonce("0xA", web3) is None
        assert NonceManager.get_cached_nonce("0xB", web3) is None


class TestGetNonceInfo:
    def test_returns_mined_pending_and_cached(self):
        NonceManager.clear_all()
        web3 = _mock_web3(mined=3, pending=5)
        with patch("ogpu.client.nonce_utils.WEB3", return_value=web3):
            info = get_nonce_info(private_key=_HEX_KEY)
        assert info["mined_nonce"] == 3
        assert info["pending_nonce"] == 5
        assert info["has_pending"] is True
        assert info["pending_count"] == 2
