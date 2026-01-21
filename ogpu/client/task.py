import time
import warnings
from typing import Optional

from eth_account import Account

from .config import get_private_key
from .contracts import ControllerContract, NexusContract
from .nonce_manager import NonceManager
from .types import TaskInfo
from .web3_manager import WEB3

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")


def publish_task(
    task_info: TaskInfo,
    private_key: Optional[str] = None,
    nonce: Optional[int] = None,
    auto_fix_nonce: bool = True,
    max_retries: int = 3,
) -> str:
    """
    Publish a task to the Controller contract.

    Args:
        task_info: TaskInfo object containing task configuration
        private_key: Private key for signing the transaction. If None, will use CLIENT_PRIVATE_KEY environment variable.
        nonce: Optional manual nonce override. If None, will be fetched automatically.
        auto_fix_nonce: If True, automatically retry on nonce errors (default: True)
        max_retries: Maximum number of retry attempts on recoverable errors (default: 3)

    Returns:
        Address of the created task contract

    Raises:
        Exception: If transaction fails after all retries

    Example:
        >>> from ogpu.client import publish_task, TaskInfo
        >>> # Normal usage with auto-retry
        >>> task_address = publish_task(task_info)
        >>>
        >>> # Manual nonce override (for advanced use)
        >>> task_address = publish_task(task_info, nonce=42)
        >>>
        >>> # Disable auto-fix
        >>> task_address = publish_task(task_info, auto_fix_nonce=False)
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)

    for attempt in range(max_retries):
        try:
            # Convert TaskInfo to TaskParams
            task_params = task_info.to_task_params()

            # Get Web3 instance
            web3 = WEB3()

            # Get contract instances
            controller_contract = ControllerContract()
            nexus_contract = NexusContract()

            # Get nonce (manual override or managed)
            if nonce is not None:
                tx_nonce = nonce
            else:
                tx_nonce = NonceManager.get_nonce(acc.address, web3)

            tx = controller_contract.functions.publishTask(
                task_params.to_tuple()
            ).build_transaction({"from": acc.address, "nonce": tx_nonce})

            signed = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            # Success! Increment nonce if we're managing it
            if nonce is None:
                NonceManager.increment_nonce(acc.address, web3)

            logs = nexus_contract.events.TaskPublished().process_receipt(receipt)
            return web3.to_checksum_address(logs[0]["args"]["task"])

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
                    # Import here to avoid circular dependency
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
                    # Reset nonce cache to get fresh values
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
    raise Exception(f"Failed to publish task after {max_retries} attempts")
