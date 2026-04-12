from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ogpu.chain.nonce import NonceManager


def _make_web3(pending_nonce: int = 5):
    web3 = MagicMock()
    web3.to_checksum_address = lambda a: a
    web3.eth.get_transaction_count = MagicMock(return_value=pending_nonce)
    return web3


class TestNonceManager:
    def test_first_call_reads_pending_nonce(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=7)
        assert NonceManager.get_nonce("0xA", web3) == 7
        web3.eth.get_transaction_count.assert_called_once_with("0xA", "pending")

    def test_cached_nonce_returned_when_ahead(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        NonceManager.increment_nonce("0xA", web3)
        NonceManager.increment_nonce("0xA", web3)
        # Cache is now 7; blockchain still reports 5 — cache wins
        assert NonceManager.get_nonce("0xA", web3) == 7

    def test_blockchain_ahead_of_cache_wins(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        web3.eth.get_transaction_count.return_value = 10
        assert NonceManager.get_nonce("0xA", web3) == 10

    def test_force_refresh_ignores_cache(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        NonceManager.increment_nonce("0xA", web3)  # cache -> 6
        web3.eth.get_transaction_count.return_value = 3
        assert NonceManager.get_nonce("0xA", web3, force_refresh=True) == 3

    def test_increment_updates_cache(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        NonceManager.increment_nonce("0xA", web3)
        assert NonceManager.get_cached_nonce("0xA", web3) == 6

    def test_reset_clears_single_address(self):
        NonceManager.clear_all()
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        NonceManager.reset_nonce("0xA", web3)
        assert NonceManager.get_cached_nonce("0xA", web3) is None

    def test_clear_all(self):
        web3 = _make_web3(pending_nonce=5)
        NonceManager.get_nonce("0xA", web3)
        NonceManager.get_nonce("0xB", web3)
        NonceManager.clear_all()
        assert NonceManager.get_cached_nonce("0xA", web3) is None
        assert NonceManager.get_cached_nonce("0xB", web3) is None

    def test_increment_noop_when_not_cached(self):
        NonceManager.clear_all()
        web3 = _make_web3()
        NonceManager.increment_nonce("0xNeverRead", web3)
        assert NonceManager.get_cached_nonce("0xNeverRead", web3) is None

    def test_reset_noop_when_not_cached(self):
        NonceManager.clear_all()
        web3 = _make_web3()
        NonceManager.reset_nonce("0xNeverRead", web3)
