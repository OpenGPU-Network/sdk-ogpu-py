import time

from web3 import Web3

from ogpu.client import ChainConfig, ChainId, TaskInfo, TaskInput, publish_task

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

# Create task configuration
task_config = TaskInput(
    function_name="rewarder",
    data={
        "provider": "0xefAF383fB02cDf98b0Fae3E95001D888Ae7358f4",
        "reward": 0.004166666666666667,
    },
)

# Create task info
task_info = TaskInfo(
    source="0xbED73Af03698e4B91D397c7610B972bad018a752",
    config=task_config,
    expiryTime=int(time.time()) + 3600,  # 1 hour from now
    payment=Web3.to_wei(0.01, "ether"),
)

# Publish the task
task_address = publish_task(task_info=task_info)

print(f"Task published at: {task_address}")
