from ogpu.client import ChainConfig, ChainId
from ogpu.protocol import Response

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

response = Response("0x575162Fb2b19Fd6C3bC8af5Fd1D4F9b832311a34")

print(f"Status before: {response.get_status()}")
print(f"Already confirmed: {response.is_confirmed()}")

receipt = response.confirm()

print(f"Confirmed in tx: {receipt.tx_hash}")
print(f"Status after: {response.get_status()}")
