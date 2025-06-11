import warnings

from eth_account import Account

from .config import CLIENT_PRIVATE_KEY
from .contracts import ControllerContract, NexusContract
from .types import TaskInfo
from .web3_manager import WEB3

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")


def publish_task(
    task_info: TaskInfo,
    private_key: str | None = CLIENT_PRIVATE_KEY,
) -> str:
    """
    Publish a task to the Controller contract.

    Args:
        task_info: TaskInfo object containing task configuration
        private_key: Private key for signing the transaction

    Returns:
        Address of the created task contract
    """
    if not private_key:
        raise ValueError(
            "Private key is required. Set CLIENT_PRIVATE_KEY environment variable or pass private_key parameter."
        )

    acc = Account.from_key(private_key)

    # Convert TaskInfo to TaskParams
    task_params = task_info.to_task_params()

    tx = ControllerContract.functions.publishTask(
        task_params.to_tuple()
    ).build_transaction(
        {"from": acc.address, "nonce": WEB3.eth.get_transaction_count(acc.address)}
    )

    signed = WEB3.eth.account.sign_transaction(tx, private_key)
    tx_hash = WEB3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash)

    logs = NexusContract.events.TaskPublished().process_receipt(receipt)
    return WEB3.to_checksum_address(logs[0]["args"]["task"])
