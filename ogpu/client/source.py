import warnings

from eth_account import Account

# Suppress MismatchedABI warnings
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")

from .config import CLIENT_PRIVATE_KEY
from .contracts import NexusContract
from .types import SourceInfo
from .web3_manager import WEB3


def publish_source(
    source_info: SourceInfo,
    private_key: str | None = CLIENT_PRIVATE_KEY,
) -> str:
    """
    Publish a source to the Nexus contract.

    Args:
        source_info: SourceInfo object containing source configuration
        private_key: Private key for signing the transaction

    Returns:
        Address of the created source contract
    """
    if not private_key:
        raise ValueError(
            "Private key is required. Set CLIENT_PRIVATE_KEY environment variable or pass private_key parameter."
        )

    acc = Account.from_key(private_key)
    client_address = acc.address

    # Convert SourceInfo to SourceParams
    source_params = source_info.to_source_params(client_address)

    tx = NexusContract.functions.publishSource(
        source_params.to_tuple()
    ).build_transaction(
        {
            "from": acc.address,
            "nonce": WEB3.eth.get_transaction_count(acc.address),
        }
    )

    signed = WEB3.eth.account.sign_transaction(tx, private_key)
    tx_hash = WEB3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = WEB3.eth.wait_for_transaction_receipt(tx_hash)

    logs = NexusContract.events.SourcePublished().process_receipt(receipt)
    return WEB3.to_checksum_address(logs[0]["args"]["source"])
