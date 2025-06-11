# set chain to mainnet
from ogpu.client import ChainConfig, ChainId, get_task_responses

ChainConfig.set_chain(ChainId.OGPU_TESTNET)


responses = get_task_responses(
    task_address="0x9A52457785367B7cFDf7594847C506B6c80032dE"
)

print("Responses:")
for response in responses:
    print(f"Address: {response.address}")
    print(f"Task: {response.task}")
    print(f"Provider: {response.provider}")
    print(f"Data: {response.data}")
    print(f"Payment: {response.payment}")
    print(f"Status: {response.status}")
    print(f"Timestamp: {response.timestamp}")
    print(f"Confirmed: {response.confirmed}")
    print("-" * 40)
