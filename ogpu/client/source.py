import time
import warnings
from typing import Optional

from eth_account import Account

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")

from .config import get_private_key
from .contracts import NexusContract
from .nonce_manager import NonceManager
from .types import SourceInfo
from .web3_manager import WEB3


def publish_source(
    source_info: SourceInfo,
    private_key: Optional[str] = None,
    nonce: Optional[int] = None,
    auto_fix_nonce: bool = True,
    max_retries: int = 3,
) -> str:
    """
    Publish a source to the Nexus contract.

    Args:
        source_info: SourceInfo object containing source configuration
        private_key: Private key for signing the transaction. If None, will use CLIENT_PRIVATE_KEY environment variable.
        nonce: Optional manual nonce override. If None, will be fetched automatically.
        auto_fix_nonce: If True, automatically retry on nonce errors (default: True)
        max_retries: Maximum number of retry attempts on recoverable errors (default: 3)

    Returns:
        Address of the created source contract

    Raises:
        Exception: If transaction fails after all retries

    Example:
        >>> from ogpu.client import publish_source, SourceInfo
        >>> # Normal usage with auto-retry
        >>> source_address = publish_source(source_info)
        >>>
        >>> # Manual nonce override (for advanced use)
        >>> source_address = publish_source(source_info, nonce=42)
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)

    for attempt in range(max_retries):
        try:
            client_address = acc.address

            # Convert SourceInfo to SourceParams
            source_params = source_info.to_source_params(client_address)

            # Get contract instances
            nexus_contract = NexusContract()
            web3 = WEB3()

            # Get nonce (manual override or managed)
            if nonce is not None:
                tx_nonce = nonce
            else:
                tx_nonce = NonceManager.get_nonce(acc.address, web3)

            tx = nexus_contract.functions.publishSource(
                source_params.to_tuple()
            ).build_transaction({"from": acc.address, "nonce": tx_nonce})

            signed = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            # Success! Increment nonce if we're managing it
            if nonce is None:
                NonceManager.increment_nonce(acc.address, web3)

            logs = nexus_contract.events.SourcePublished().process_receipt(receipt)
            return web3.to_checksum_address(logs[0]["args"]["source"])

        except Exception as e:
            error_msg = str(e).lower()

            # Check if this is a nonce-related error
            is_nonce_error = any(
                x in error_msg
                for x in ["nonce too low", "known transaction", "already known"]
            )

            # Check if this is a replacement underpriced error
            is_underpriced = "replacement transaction underpriced" in error_msg

            if is_nonce_error:
                print(
                    f"⚠️  Nonce error detected on attempt {attempt + 1}/{max_retries}"
                )

                if auto_fix_nonce and attempt < max_retries - 1:
                    print(f"🔧 Auto-fixing nonce...")
                    from .nonce_utils import fix_nonce

                    fix_nonce(acc.address, private_key)
                    print(f"🔄 Retrying transaction...")
                    continue
                else:
                    raise Exception(
                        f"Nonce error after {attempt + 1} attempts: {e}\n"
                        f"💡 Try calling fix_nonce() to manually resolve this issue."
                    )

            elif is_underpriced:
                print(
                    f"⚠️  Transaction underpriced on attempt {attempt + 1}/{max_retries}"
                )

                if auto_fix_nonce and attempt < max_retries - 1:
                    print(
                        f"⛽ Waiting 5 seconds for gas prices to update and retrying..."
                    )
                    time.sleep(5)
                    NonceManager.reset_nonce(acc.address, web3)
                    continue
                else:
                    raise Exception(
                        f"Transaction underpriced after {attempt + 1} attempts: {e}\n"
                        f"💡 Wait a few seconds and try again, or increase gas price."
                    )

            else:
                # Not a recoverable error, re-raise immediately
                raise

    # Max retries exceeded
    raise Exception(f"Failed to publish source after {max_retries} attempts")
