"""Vault operations: deposit, lock, check balances."""

from web3 import Web3

from ogpu.client import ChainConfig, ChainId
from ogpu.protocol import vault

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

SIGNER = "YOUR_PRIVATE_KEY_HERE"
MY_ADDRESS = "0xYOUR_ADDRESS_HERE"

receipt = vault.deposit(MY_ADDRESS, Web3.to_wei(1, "ether"), signer=SIGNER)
print(f"Deposited in tx: {receipt.tx_hash}")

balance = vault.get_balance_of(MY_ADDRESS)
print(f"Vault balance: {balance} wei")

receipt = vault.lock(Web3.to_wei(0.5, "ether"), signer=SIGNER)
print(f"Locked in tx: {receipt.tx_hash}")

lockup = vault.get_lockup_of(MY_ADDRESS)
print(f"Lockup: {lockup} wei")

eligible = vault.is_eligible(MY_ADDRESS)
print(f"Eligible: {eligible}")
