# Example of a single task handler using ogpu.service
from pydantic import BaseModel

import ogpu.service


@ogpu.service.init()
def setup():
    ogpu.service.logger.info("Loading models and resources...")
    # Load your models, download files, etc.
    ogpu.service.logger.info("Setup complete!")


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


@ogpu.service.expose()
def multiply(data: MultiplyInput) -> MultiplyOutput:
    """
    Example handler function that multiplies two numbers.
    """
    ogpu.service.logger.info(f"Starting multiplication: {data.a} * {data.b}")
    result = data.a * data.b
    ogpu.service.logger.info(f"Result computed: {result}")
    return MultiplyOutput(result=result)


# Starts the server and makes the handler accessible over HTTP
ogpu.service.start()
