# set chain to mainnet
from ogpu.client import ChainConfig, ChainId, get_confirmed_response

ChainConfig.set_chain(ChainId.OGPU_TESTNET)


response = get_confirmed_response(
    task_address="0xC983F060a9e3EB54aF67AAdC65CC10E8aD90C5f3"
)

print(f"Address: {response.address}")
print(f"Data: {response.data}")
