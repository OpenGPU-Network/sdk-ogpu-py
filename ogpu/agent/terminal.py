import warnings

from eth_account import Account

from ..client.contracts import TerminalContract
from ..client.web3_manager import WEB3

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")


def set_agent(agent_address: str, value: bool, private_key: str) -> str:
    """
    Set an agent status in the Terminal contract.

    Args:
        agent_address: The address of the agent to set
        value: Boolean value to set for the agent (True to enable, False to disable)
        private_key: Private key for signing the transaction.

    Returns:
        str: Transaction hash of the setAgent transaction

    Raises:
        ValueError: If the agent address format is invalid
        Exception: If the transaction fails
    """

    # Validate agent address format
    web3 = WEB3()
    if not web3.is_address(agent_address):
        raise ValueError(f"Invalid agent address format: {agent_address}")

    acc = Account.from_key(private_key)

    try:
        # Get the Terminal contract instance
        terminal_contract = TerminalContract()

        # Build the transaction
        tx = terminal_contract.functions.setAgent(
            agent_address, value
        ).build_transaction(
            {
                "from": acc.address,
                "nonce": web3.eth.get_transaction_count(acc.address),
            }
        )

        # Sign and send the transaction
        signed = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")

        return tx_hash.hex()

    except Exception as e:
        raise Exception(f"Failed to set agent {agent_address} to {value}: {str(e)}")
