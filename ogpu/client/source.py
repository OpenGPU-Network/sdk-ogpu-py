import warnings

from eth_account import Account

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")

from .config import get_private_key
from .contracts import NexusContract
from .types import SourceInfo
from .web3_manager import WEB3


def publish_source(
    source_info: SourceInfo,
    private_key: str | None = None,
) -> str:
    """
    Publish a source to the Nexus contract.

    Args:
        source_info: SourceInfo object containing source configuration
        private_key: Private key for signing the transaction. If None, will use CLIENT_PRIVATE_KEY environment variable.

    Returns:
        Address of the created source contract
    """
    if private_key is None:
        private_key = get_private_key()

    acc = Account.from_key(private_key)
    client_address = acc.address

    # Convert SourceInfo to SourceParams
    source_params = source_info.to_source_params(client_address)

    # Get contract instances
    nexus_contract = NexusContract()
    web3 = WEB3()

    tx = nexus_contract.functions.publishSource(
        source_params.to_tuple()
    ).build_transaction(
        {
            "from": acc.address,
            "nonce": web3.eth.get_transaction_count(acc.address),
        }
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    logs = nexus_contract.events.SourcePublished().process_receipt(receipt)
    return web3.to_checksum_address(logs[0]["args"]["source"])
