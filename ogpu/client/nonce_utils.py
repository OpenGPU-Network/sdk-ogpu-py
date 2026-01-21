"""
Nonce utility functions for fixing stuck transactions.

This module provides user-facing utilities for recovering from nonce-related
transaction failures.
"""

import time
from typing import Optional

from eth_account import Account

from .config import get_private_key
from .nonce_manager import NonceManager
from .web3_manager import WEB3


def fix_nonce(address: Optional[str] = None, private_key: Optional[str] = None) -> int:
    """
    Fix stuck nonce issues by canceling pending transactions.

    This function will:
    1. Detect pending transactions (transactions stuck in mempool)
    2. Cancel them by sending 0 ETH self-transfers with higher gas price
    3. Clear SDK's internal nonce cache
    4. Return the next available nonce

    Args:
        address: Ethereum address to fix (optional if private_key provided)
        private_key: Private key for signing cancellation transactions
                    If None, will use CLIENT_PRIVATE_KEY environment variable

    Returns:
        Next available nonce after fixing

    Raises:
        ValueError: If neither address nor private_key is provided

    Example:
        >>> from ogpu.client import fix_nonce
        >>> # Fix nonce for current account
        >>> next_nonce = fix_nonce()
        >>> print(f"Ready to send transaction with nonce: {next_nonce}")
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    address = web3.to_checksum_address(address)

    print(f"🔧 Fixing nonce for {address}...")

    # Get current nonce state
    mined_nonce = web3.eth.get_transaction_count(address, "latest")
    pending_nonce = web3.eth.get_transaction_count(address, "pending")

    print(f"   📊 Mined nonce: {mined_nonce}")
    print(f"   📊 Pending nonce: {pending_nonce}")

    if pending_nonce > mined_nonce:
        stuck_count = pending_nonce - mined_nonce
        print(f"   ⚠️  {stuck_count} pending transaction(s) detected!")
        print(f"   🗑️  Attempting to cancel stuck transactions...")

        # Cancel each stuck transaction
        success_count = 0
        for nonce in range(mined_nonce, pending_nonce):
            try:
                tx_hash = _cancel_transaction_with_nonce(
                    address, nonce, private_key, web3
                )
                print(f"      ✅ Cancelled nonce {nonce} (tx: {tx_hash[:10]}...)")
                success_count += 1
                time.sleep(0.5)  # Small delay between cancellations
            except Exception as e:
                print(f"      ⚠️  Could not cancel nonce {nonce}: {e}")

        if success_count > 0:
            print(f"   ✅ Successfully cancelled {success_count} transaction(s)")
            print(f"   ⏳ Waiting 3 seconds for cancellations to propagate...")
            time.sleep(3)
        else:
            print(f"   ⚠️  Could not cancel any transactions automatically")
            print(f"   💡 They may resolve naturally or you may need to wait")
    else:
        print(f"   ✅ No pending transactions found")

    # Clear SDK internal cache
    NonceManager.reset_nonce(address, web3)
    print(f"   🧹 SDK nonce cache cleared")

    # Get fresh nonce
    final_nonce = web3.eth.get_transaction_count(address, "pending")
    print(f"   ✅ Fixed! Next available nonce: {final_nonce}")

    return final_nonce


def _cancel_transaction_with_nonce(
    address: str, nonce: int, private_key: str, web3
) -> str:
    """
    Cancel a pending transaction by replacing it with a 0 ETH self-transfer.

    Args:
        address: Ethereum address
        nonce: Nonce to cancel
        private_key: Private key for signing
        web3: Web3 instance

    Returns:
        Transaction hash of the cancellation transaction

    Raises:
        Exception: If transaction fails to send
    """
    acc = Account.from_key(private_key)

    # Get current gas price and increase by 20% to ensure replacement
    current_gas_price = web3.eth.gas_price
    replacement_gas_price = int(current_gas_price * 1.2)

    # Build cancellation transaction (0 ETH to self)
    cancel_tx = {
        "from": acc.address,
        "to": acc.address,  # Send to self
        "value": 0,  # 0 ETH
        "nonce": nonce,
        "gas": 21000,  # Minimum gas for transfer
        "gasPrice": replacement_gas_price,
        "chainId": web3.eth.chain_id,
    }

    # Sign and send
    signed = web3.eth.account.sign_transaction(cancel_tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

    return tx_hash.hex()


def reset_nonce_cache(
    address: Optional[str] = None, private_key: Optional[str] = None
) -> None:
    """
    Reset the SDK's internal nonce cache without canceling transactions.

    This is useful when you want to force the SDK to fetch a fresh nonce
    from the blockchain without canceling any pending transactions.

    Args:
        address: Ethereum address to reset (optional if private_key provided)
        private_key: Private key to derive address from
                    If None, will use CLIENT_PRIVATE_KEY environment variable

    Example:
        >>> from ogpu.client import reset_nonce_cache
        >>> reset_nonce_cache()
        >>> print("Nonce cache cleared")
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)
    if address is None:
        address = acc.address

    web3 = WEB3()
    NonceManager.reset_nonce(address, web3)
    print(f"✅ Nonce cache cleared for {address}")


def clear_all_nonce_caches() -> None:
    """
    Clear all nonce caches for all addresses.

    This is useful for testing or when you want to completely reset
    the SDK's nonce state.

    Example:
        >>> from ogpu.client import clear_all_nonce_caches
        >>> clear_all_nonce_caches()
        >>> print("All nonce caches cleared")
    """
    NonceManager.clear_all()
    print("✅ All nonce caches cleared")


def get_nonce_info(
    address: Optional[str] = None, private_key: Optional[str] = None
) -> dict:
    """
    Get detailed nonce information for an address.

    Args:
        address: Ethereum address (optional if private_key provided)
        private_key: Private key to derive address from
                    If None, will use CLIENT_PRIVATE_KEY environment variable

    Returns:
        Dictionary containing:
        - address: The address
        - mined_nonce: Number of mined transactions
        - pending_nonce: Number of mined + pending transactions
        - cached_nonce: SDK's cached nonce (None if not cached)
        - has_pending: Whether there are pending transactions

    Example:
        >>> from ogpu.client import get_nonce_info
        >>> info = get_nonce_info()
        >>> print(f"Pending transactions: {info['pending_nonce'] - info['mined_nonce']}")
    """
    if private_key is None:
        private_key = get_private_key()

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
