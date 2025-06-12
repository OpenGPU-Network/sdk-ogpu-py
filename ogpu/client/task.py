import warnings

from eth_account import Account

from .config import get_private_key
from .contracts import ControllerContract, NexusContract
from .types import TaskInfo
from .web3_manager import WEB3

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")


def publish_task(
    task_info: TaskInfo,
    private_key: str | None = None,
) -> str:
    """
    Publish a task to the Controller contract.

    Args:
        task_info: TaskInfo object containing task configuration
        private_key: Private key for signing the transaction. If None, will use CLIENT_PRIVATE_KEY environment variable.

    Returns:
        Address of the created task contract
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)
    # Convert TaskInfo to TaskParams
    task_params = task_info.to_task_params()

    # Get Web3 instance
    web3 = WEB3()

    # Get contract instances
    controller_contract = ControllerContract()
    nexus_contract = NexusContract()

    tx = controller_contract.functions.publishTask(
        task_params.to_tuple()
    ).build_transaction(
        {"from": acc.address, "nonce": web3.eth.get_transaction_count(acc.address)}
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    logs = nexus_contract.events.TaskPublished().process_receipt(receipt)
    return web3.to_checksum_address(logs[0]["args"]["task"])
