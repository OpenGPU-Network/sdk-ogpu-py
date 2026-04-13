"""Nonce management and recovery utilities.

The SDK uses ``NonceManager`` internally inside ``TxExecutor`` to avoid
nonce collisions during concurrent transactions. Every write operation
in the SDK reads from the cache, builds a transaction, sends it, and
increments the cached nonce — so two calls on the same address from the
same process naturally serialize.

When transactions get stuck (wrong gas price, network hiccup, process
crash mid-sign), the public helpers (``fix_nonce``, ``reset_nonce_cache``,
``clear_all_nonce_caches``, ``get_nonce_info``) let you recover without
restarting. See the [error handling guide](../guides/errors.md) for the
full playbook.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from eth_account import Account
from web3 import Web3

from .web3 import WEB3


class NonceManager:
    """Thread-safe nonce cache keyed by address.

    All methods are classmethods — there's only one cache per process.
    Internally uses a global lock for address-list mutations and a
    per-address lock for nonce reads/writes, so concurrent transactions
    from different addresses don't block each other.

    The cache starts empty. On first ``get_nonce(addr)`` the cache is
    seeded from ``eth.get_transaction_count(addr, "pending")``. Every
    successful ``send_raw_transaction`` increments the cached nonce.
    If the on-chain nonce jumps ahead of the cache (e.g. a tx we sent
    got included in a block), the next ``get_nonce`` picks up the
    higher value automatically.

    Usually you don't interact with this class directly — ``TxExecutor``
    wraps it for every write. You'd use it manually only if you're
    building transactions by hand.
    """

    _nonces: dict[str, int] = {}
    _locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, address: str) -> threading.Lock:
        """Return (and create on first use) the per-address lock."""
        with cls._global_lock:
            if address not in cls._locks:
                cls._locks[address] = threading.Lock()
            return cls._locks[address]

    @classmethod
    def get_nonce(cls, address: str, web3: Web3, force_refresh: bool = False) -> int:
        """Return the next nonce to use for ``address``.

        If the cache has no entry or ``force_refresh=True``, reads the
        on-chain pending count as a starting point. Otherwise returns
        ``max(cached, pending_from_chain)`` to recover from cases where
        the cache fell behind.

        Args:
            address: The EOA to get a nonce for.
            web3: Connected ``Web3`` instance (usually from
                ``WEB3()``).
            force_refresh: If True, ignore the cache and re-read from chain.

        Returns:
            The nonce to use for the next transaction from this address.
        """
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
        """Bump the cached nonce after a successful ``send_raw_transaction``.

        Called by ``TxExecutor`` after each successful broadcast so the
        next call gets a fresh nonce without re-reading the chain.

        Args:
            address: The EOA whose nonce to bump.
            web3: Connected ``Web3`` instance (used only for address
                checksumming).
        """
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                cls._nonces[address] += 1

    @classmethod
    def reset_nonce(cls, address: str, web3: Web3) -> None:
        """Drop the cached nonce for one address.

        The next ``get_nonce`` call for that address re-reads from chain.
        Use when you know the cache is stale — e.g. after manually
        canceling a stuck transaction.

        Args:
            address: The EOA whose cache entry to drop.
            web3: Connected ``Web3`` instance (used only for checksumming).
        """
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                del cls._nonces[address]

    @classmethod
    def clear_all(cls) -> None:
        """Drop every cached nonce and lock across all addresses.

        Useful in test teardown or when you want to guarantee fresh
        state after a major RPC outage.
        """
        with cls._global_lock:
            cls._nonces.clear()
            cls._locks.clear()

    @classmethod
    def get_cached_nonce(cls, address: str, web3: Web3) -> int | None:
        """Return the cached nonce without hitting the chain.

        Useful for diagnostics and for ``get_nonce_info``.

        Args:
            address: The EOA to query.
            web3: Connected ``Web3`` instance (used only for checksumming).

        Returns:
            The cached nonce, or None if nothing is cached for this address.
        """
        address = web3.to_checksum_address(address)
        return cls._nonces.get(address)


# ---------------------------------------------------------------------------
# Recovery utilities (user-facing)
# ---------------------------------------------------------------------------


def _require_private_key(private_key: str | None) -> str:
    """Resolve to ``CLIENT_PRIVATE_KEY`` env var when not explicit.

    Internal helper used by the recovery functions that need to sign
    cancellation transactions. Raises ``ValueError`` if the env var
    isn't set and nothing was passed.
    """
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
    """Detect stuck pending transactions and force-cancel them.

    Sometimes a transaction gets stuck in the mempool — wrong gas price,
    a crashed signer process, an RPC hiccup that lost the broadcast.
    ``fix_nonce`` is the hammer: it compares the on-chain
    ``mined_nonce`` with the ``pending_nonce``, and for every nonce in
    between, broadcasts a 0-value self-transfer at 1.2× the current gas
    price. These replacement transactions pre-empt the stuck ones and
    the mempool clears.

    After the cancellations propagate (there's a 3-second sleep), the
    SDK-side nonce cache is reset and the function returns the next
    available nonce.

    **Requires gas** — the cancellation transactions pay real gas, and
    every cancellation attempt is a separate tx.

    Args:
        address: The EOA to recover. Defaults to the address derived
            from ``private_key``.
        private_key: Hex private key used to sign cancellation
            transactions. If omitted, reads ``CLIENT_PRIVATE_KEY`` from
            the environment.

    Returns:
        The next available nonce after cancellation propagates.

    Raises:
        ValueError: If neither ``private_key`` nor ``CLIENT_PRIVATE_KEY``
            is available.

    Example:
        ```python
        from ogpu import fix_nonce
        next_nonce = fix_nonce()
        # 🔧 Fixing nonce for 0x...
        #    📊 Mined nonce: 42
        #    📊 Pending nonce: 45
        #    ⚠️  3 pending transaction(s) detected!
        #    ✅ Fixed! Next available nonce: 42
        ```
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


def _cancel_transaction_with_nonce(
    address: str, nonce: int, private_key: str, web3: Any
) -> str:
    """Broadcast a replacement 0-value self-transfer at a given nonce.

    Internal helper used by ``fix_nonce``. Builds a minimal transaction
    (21000 gas, 1.2× current gas price, to self) so the mempool sees
    a valid replacement for the stuck tx at that nonce.

    Args:
        address: Sender address.
        nonce: The stuck nonce to replace.
        private_key: Hex key for signing.
        web3: Connected ``Web3`` instance.

    Returns:
        The replacement transaction's hash as a hex string.
    """
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
    """Drop the SDK-side cached nonce for one address.

    Cheap, doesn't touch the chain. Use when you know the cache is
    stale but don't need to cancel stuck transactions — e.g. you just
    manually sent a transaction from an external wallet and want the
    SDK to re-read the on-chain nonce on the next call.

    Args:
        address: The EOA to clear. Defaults to the address derived
            from ``private_key``.
        private_key: Used to derive the address when ``address`` is
            omitted. Falls back to ``CLIENT_PRIVATE_KEY`` env var.

    Raises:
        ValueError: If no address can be determined.

    Example:
        ```python
        from ogpu import reset_nonce_cache
        reset_nonce_cache()
        # ✅ Nonce cache cleared for 0x...
        ```
    """
    private_key = _require_private_key(private_key)
    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    NonceManager.reset_nonce(address, web3)
    print(f"✅ Nonce cache cleared for {address}")


def clear_all_nonce_caches() -> None:
    """Drop every cached nonce for every address in the process.

    The nuclear option. Use in test teardown, or when you're doing
    something unusual and want to guarantee a clean slate.

    Example:
        ```python
        from ogpu import clear_all_nonce_caches
        clear_all_nonce_caches()
        ```
        ✅ All nonce caches cleared
    """
    NonceManager.clear_all()
    print("✅ All nonce caches cleared")


def get_nonce_info(
    address: str | None = None, private_key: str | None = None
) -> dict[str, Any]:
    """Return a dict summarizing on-chain and cached nonce state.

    Useful for diagnostics and dashboards. Reads both the ``latest``
    and ``pending`` transaction counts from chain, plus the SDK-side
    cached value, and returns them together.

    Args:
        address: The EOA to inspect. Defaults to the address derived
            from ``private_key``.
        private_key: Used to derive the address when ``address`` is
            omitted. Falls back to ``CLIENT_PRIVATE_KEY`` env var.

    Returns:
        Dict with keys:

        - ``address``: The checksummed address.
        - ``mined_nonce``: Nonce from ``latest`` block.
        - ``pending_nonce``: Nonce from ``pending`` block.
        - ``cached_nonce``: SDK cached nonce, or None if not cached.
        - ``has_pending``: True if ``pending_nonce > mined_nonce``.
        - ``pending_count``: Number of pending transactions.

    Example:
        ```python
        from ogpu import get_nonce_info
        get_nonce_info()
        # {'address': '0x...', 'mined_nonce': 42, 'pending_nonce': 42,
        #  'cached_nonce': 42, 'has_pending': False, 'pending_count': 0}
        ```
    """
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
