"""
Nonce management for preventing stuck transactions.

This module provides thread-safe nonce caching and management to prevent
nonce collisions and stuck transactions in the OGPU SDK.
"""

import threading
from typing import Dict, Optional

from web3 import Web3


class NonceManager:
    """
    Thread-safe nonce manager that caches nonces per address.

    This manager helps prevent nonce-related issues by:
    1. Using 'pending' block identifier to include pending transactions
    2. Caching nonces locally to avoid redundant RPC calls
    3. Providing thread-safe operations for concurrent transactions
    4. Offering manual reset capabilities for stuck transaction recovery
    """

    _nonces: Dict[str, int] = {}
    _locks: Dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, address: str) -> threading.Lock:
        """Get or create a lock for a specific address."""
        with cls._global_lock:
            if address not in cls._locks:
                cls._locks[address] = threading.Lock()
            return cls._locks[address]

    @classmethod
    def get_nonce(
        cls, address: str, web3: Web3, force_refresh: bool = False
    ) -> int:
        """
        Get the next nonce for an address.

        Args:
            address: Ethereum address (will be checksummed)
            web3: Web3 instance for blockchain queries
            force_refresh: If True, ignore cache and fetch from blockchain

        Returns:
            Next available nonce for the address
        """
        # Ensure address is checksummed
        address = web3.to_checksum_address(address)

        lock = cls._get_lock(address)
        with lock:
            # Get pending nonce from blockchain (includes pending txs)
            pending_nonce = web3.eth.get_transaction_count(address, "pending")

            if force_refresh or address not in cls._nonces:
                # First time or forced refresh - use blockchain value
                cls._nonces[address] = pending_nonce
            else:
                # Use the maximum of cached and blockchain value
                # This handles cases where:
                # - Blockchain is ahead (tx mined while we weren't watching)
                # - Cache is ahead (we sent tx but blockchain hasn't seen it yet)
                cls._nonces[address] = max(cls._nonces[address], pending_nonce)

            return cls._nonces[address]

    @classmethod
    def increment_nonce(cls, address: str, web3: Web3) -> None:
        """
        Increment the cached nonce after successfully sending a transaction.

        Args:
            address: Ethereum address (will be checksummed)
            web3: Web3 instance for address checksumming
        """
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                cls._nonces[address] += 1

    @classmethod
    def reset_nonce(cls, address: str, web3: Web3) -> None:
        """
        Reset the cached nonce for an address.

        This forces the next get_nonce() call to fetch fresh from blockchain.
        Useful for recovering from stuck transaction scenarios.

        Args:
            address: Ethereum address (will be checksummed)
            web3: Web3 instance for address checksumming
        """
        address = web3.to_checksum_address(address)
        lock = cls._get_lock(address)
        with lock:
            if address in cls._nonces:
                del cls._nonces[address]

    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all cached nonces.

        This is useful for testing or when you want to reset the entire state.
        """
        with cls._global_lock:
            cls._nonces.clear()
            cls._locks.clear()

    @classmethod
    def get_cached_nonce(cls, address: str, web3: Web3) -> Optional[int]:
        """
        Get the cached nonce without fetching from blockchain.

        Args:
            address: Ethereum address (will be checksummed)
            web3: Web3 instance for address checksumming

        Returns:
            Cached nonce or None if not cached
        """
        address = web3.to_checksum_address(address)
        return cls._nonces.get(address)
