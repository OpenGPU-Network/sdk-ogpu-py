# Example of a task with timeout parameter using ogpu.service
from pydantic import BaseModel
import time
import ogpu.service


class MultiplyInput(BaseModel):
    """
    Input model for multiplication operation.
    """

    a: int
    b: int


class MultiplyOutput(BaseModel):
    """
    Output model for multiplication operation.
    """

    result: int


@ogpu.service.expose(timeout=2)
def multiply(data: MultiplyInput) -> MultiplyOutput:
    """
    Example handler function that multiplies two numbers.
    """
    ogpu.service.logger.info(f"Starting multiplication: {data.a} * {data.b}")
    result = data.a * data.b
    time.sleep(3)  # Simulate a delay to demonstrate timeout handling
    ogpu.service.logger.info(f"Result computed: {result}")
    return MultiplyOutput(result=result)


# Starts the server and makes the handler accessible over HTTP
ogpu.service.start()
