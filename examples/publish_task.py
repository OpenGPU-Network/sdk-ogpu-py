import time

from pydantic import BaseModel
from web3 import Web3

from ogpu.client import ChainConfig, ChainId, TaskInfo, TaskInput, publish_task

ChainConfig.set_chain(ChainId.OGPU_TESTNET)


class MyTaskModel(BaseModel):
    """
    Input model for multiplication operation.
    """

    input: str
    additional_param: int = 0  # Optional parameter with default value


# Create task configuration
task_config = TaskInput(
    function_name="some_function",
    data=MyTaskModel(
        input="a photo of an astronaut riding a horse on mars",
        additional_param=42,  # Example additional parameter
    ),
)

# Create task info
task_info = TaskInfo(
    source="0x4288fCDF9815718358cb481A82A4dB123e6D0b45",
    config=task_config,
    expiryTime=int(time.time()) + 3600,  # 1 hour from now
    payment=Web3.to_wei(0.01, "ether"),
)

# Publish the task
task_address = publish_task(task_info=task_info)

print(f"Task published at: {task_address}")
