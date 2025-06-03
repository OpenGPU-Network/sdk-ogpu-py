from eth_account import Account
from web3 import Web3

from .config import CLIENT_PRIVATE_KEY
from .contracts import *
from .types import SourceParams


def create_source(
    web3: Web3,
    source_params: SourceParams,
    private_key: str | None = CLIENT_PRIVATE_KEY,
) -> str:
    acc = Account.from_key(private_key)

    tx = NexusContract.functions.publishSource(
        source_params.to_tuple()
    ).build_transaction(
        {
            "from": acc.address,
            "value": web3.to_wei(source_params.minPayment, "wei"),
            "nonce": web3.eth.get_transaction_count(acc.address),
            "gas": 8000000,
            "gasPrice": web3.to_wei("10", "gwei"),
        }
    )

    signed = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    logs = NexusContract.events.SourcePublished().process_receipt(receipt)
    return logs[0]["args"]["source"]
