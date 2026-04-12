"""Nonce management and recovery utilities.

``NonceManager`` is a thread-safe cache used internally by ``TxExecutor`` to
avoid redundant RPC calls and prevent nonce collisions during concurrent
transactions. The public helpers (``fix_nonce``, ``reset_nonce_cache``,
``clear_all_nonce_caches``, ``get_nonce_info``) are user-facing escape hatches
for recovering from stuck transactions.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from eth_account import Account
from web3 import Web3

from .web3 import WEB3


class NonceManager:
    """Thread-safe nonce manager that caches nonces per address."""

    _nonces: dict[str, int] = {}
    _locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, address: str) -> threading.Lock:
        with cls._global_lock:
            if address not in cls._locks:
                cls._locks[address] = threading.Lock()
            return cls._locks[address]

    @classmethod
    def get_nonce(cls, address: str, web3: Web3, force_refresh: bool = False) -> int:
        """Get the next nonce for an address."""
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            pending_nonce = web3.eth.get_transaction_count(address, "pending")
            if force_refresh or address not in cls._nonces:
                cls._nonces[address] = pending_nonce
            else:
                cls._nonces[address] = max(cls._nonces[address], pending_nonce)
            return cls._nonces[address]

    @classmethod
    def increment_nonce(cls, address: str, web3: Web3) -> None:
        """Increment the cached nonce after a successful send."""
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                cls._nonces[address] += 1

    @classmethod
    def reset_nonce(cls, address: str, web3: Web3) -> None:
        """Drop the cached nonce for an address — next get_nonce reads fresh."""
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                del cls._nonces[address]

    @classmethod
    def clear_all(cls) -> None:
        """Drop every cached nonce and lock."""
        with cls._global_lock:
            cls._nonces.clear()
            cls._locks.clear()

    @classmethod
    def get_cached_nonce(cls, address: str, web3: Web3) -> int | None:
        """Return the cached nonce or None if not cached."""
        address = web3.to_checksum_address(address)
        return cls._nonces.get(address)


# ---------------------------------------------------------------------------
# Recovery utilities (user-facing)
# ---------------------------------------------------------------------------


def _require_private_key(private_key: str | None) -> str:
    """Resolve to CLIENT_PRIVATE_KEY env var when not explicit. Raises if unset."""
    import os

    if private_key is not None:
        return private_key
    key = os.getenv("CLIENT_PRIVATE_KEY")
    if not key:
        raise ValueError(
            "CLIENT_PRIVATE_KEY environment variable is not set. "
            "Pass private_key= explicitly or set CLIENT_PRIVATE_KEY."
        )
    return key


def fix_nonce(address: str | None = None, private_key: str | None = None) -> int:
    """Detect and cancel stuck pending transactions, then clear the nonce cache.

    Returns the next available nonce after fixing.
    """
    private_key = _require_private_key(private_key)
    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    address = web3.to_checksum_address(address)

    print(f"🔧 Fixing nonce for {address}...")

    mined_nonce = web3.eth.get_transaction_count(address, "latest")
    pending_nonce = web3.eth.get_transaction_count(address, "pending")

    print(f"   📊 Mined nonce: {mined_nonce}")
    print(f"   📊 Pending nonce: {pending_nonce}")

    if pending_nonce > mined_nonce:
        stuck_count = pending_nonce - mined_nonce
        print(f"   ⚠️  {stuck_count} pending transaction(s) detected!")
        print("   🗑️  Attempting to cancel stuck transactions...")

        success_count = 0
        for nonce in range(mined_nonce, pending_nonce):
            try:
                tx_hash = _cancel_transaction_with_nonce(address, nonce, private_key, web3)
                print(f"      ✅ Cancelled nonce {nonce} (tx: {tx_hash[:10]}...)")
                success_count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"      ⚠️  Could not cancel nonce {nonce}: {e}")

        if success_count > 0:
            print(f"   ✅ Successfully cancelled {success_count} transaction(s)")
            print("   ⏳ Waiting 3 seconds for cancellations to propagate...")
            time.sleep(3)
        else:
            print("   ⚠️  Could not cancel any transactions automatically")
    else:
        print("   ✅ No pending transactions found")

    NonceManager.reset_nonce(address, web3)
    print("   🧹 SDK nonce cache cleared")

    final_nonce = web3.eth.get_transaction_count(address, "pending")
    print(f"   ✅ Fixed! Next available nonce: {final_nonce}")
    return int(final_nonce)


def _cancel_transaction_with_nonce(address: str, nonce: int, private_key: str, web3: Any) -> str:
    """Replace a pending transaction with a 0-ETH self-transfer at higher gas."""
    acc = Account.from_key(private_key)
    current_gas_price = web3.eth.gas_price
    replacement_gas_price = int(current_gas_price * 1.2)

    cancel_tx = {
        "from": acc.address,
        "to": acc.address,
        "value": 0,
        "nonce": nonce,
        "gas": 21000,
        "gasPrice": replacement_gas_price,
        "chainId": web3.eth.chain_id,
    }

    signed = web3.eth.account.sign_transaction(cancel_tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    return str(tx_hash.hex())


def reset_nonce_cache(address: str | None = None, private_key: str | None = None) -> None:
    """Drop the SDK-side cached nonce for one address without touching the chain."""
    private_key = _require_private_key(private_key)
    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    NonceManager.reset_nonce(address, web3)
    print(f"✅ Nonce cache cleared for {address}")


def clear_all_nonce_caches() -> None:
    """Drop every cached nonce for every address."""
    NonceManager.clear_all()
    print("✅ All nonce caches cleared")


def get_nonce_info(address: str | None = None, private_key: str | None = None) -> dict[str, Any]:
    """Return a dict summarizing mined / pending / cached nonce state."""
    private_key = _require_private_key(private_key)
    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    address = web3.to_checksum_address(address)

    mined_nonce = web3.eth.get_transaction_count(address, "latest")
    pending_nonce = web3.eth.get_transaction_count(address, "pending")
    cached_nonce = NonceManager.get_cached_nonce(address, web3)

    return {
        "address": address,
        "mined_nonce": mined_nonce,
        "pending_nonce": pending_nonce,
        "cached_nonce": cached_nonce,
        "has_pending": pending_nonce > mined_nonce,
        "pending_count": pending_nonce - mined_nonce,
    }
