import time
import warnings
from typing import Optional

from eth_account import Account

from ..client.contracts import TerminalContract
from ..client.nonce_manager import NonceManager
from ..client.web3_manager import WEB3

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")


def set_agent(
    agent_address: str,
    value: bool,
    private_key: str,
    nonce: Optional[int] = None,
    auto_fix_nonce: bool = True,
    max_retries: int = 3,
) -> str:
    """
    Set an agent status in the Terminal contract.

    Args:
        agent_address: The address of the agent to set
        value: Boolean value to set for the agent (True to enable, False to disable)
        private_key: Private key for signing the transaction
        nonce: Optional manual nonce override. If None, will be fetched automatically.
        auto_fix_nonce: If True, automatically retry on nonce errors (default: True)
        max_retries: Maximum number of retry attempts on recoverable errors (default: 3)

    Returns:
        str: Transaction hash of the setAgent transaction

    Raises:
        ValueError: If the agent address format is invalid
        Exception: If the transaction fails after all retries

    Example:
        >>> from ogpu.agent import set_agent
        >>> # Normal usage with auto-retry
        >>> tx_hash = set_agent(agent_address, True, private_key)
        >>>
        >>> # Manual nonce override
        >>> tx_hash = set_agent(agent_address, True, private_key, nonce=42)
    """
    # Validate agent address format
    web3 = WEB3()
    if not web3.is_address(agent_address):
        raise ValueError(f"Invalid agent address format: {agent_address}")

    acc = Account.from_key(private_key)

    for attempt in range(max_retries):
        try:
            # Get the Terminal contract instance
            terminal_contract = TerminalContract()

            # Get nonce (manual override or managed)
            if nonce is not None:
                tx_nonce = nonce
            else:
                tx_nonce = NonceManager.get_nonce(acc.address, web3)

            # Build the transaction
            tx = terminal_contract.functions.setAgent(
                agent_address, value
            ).build_transaction({"from": acc.address, "nonce": tx_nonce})

            # Sign and send the transaction
            signed = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            # Success! Increment nonce if we're managing it
            if nonce is None:
                NonceManager.increment_nonce(acc.address, web3)

            if receipt["status"] != 1:
                raise Exception(f"Transaction failed: {tx_hash.hex()}")

            return tx_hash.hex()

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
                    from ..client.nonce_utils import fix_nonce

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
                raise Exception(
                    f"Failed to set agent {agent_address} to {value}: {str(e)}"
                )

    # Max retries exceeded
    raise Exception(f"Failed to set agent after {max_retries} attempts")
