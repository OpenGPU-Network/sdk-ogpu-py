from contextlib import asynccontextmanager
from typing import AsyncIterator

import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI

from .config import CALLBACK_URL, SERVICE_HOST, SERVICE_PORT
from .handler import get_handlers, get_init_handler
from .logger import logger


def send_callback(task_address: str, result: dict):
    """
    Placeholder function to send a callback with the result.
    This function should be implemented to handle the callback logic.
    """

    if not CALLBACK_URL:
        logger.info(
            f"No callback address configured, skipping callback for task: {task_address}"
        )
        return

    # Implement the callback logic here
    callback_url = f"{CALLBACK_URL}/{task_address}"
    # Example: Use requests or httpx to send the result to the callback URL
    response = requests.post(callback_url, json=result)
    if response.status_code != 200:
        logger.error(f"Failed to send callback: {response.status_code} {response.text}")
    logger.info(f"Callback sent to {callback_url} with result: {result}")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager for handling startup and shutdown events.
    Executes the registered init handler on startup.
    """
    # Execute initialization function on startup
    init_handler = get_init_handler()
    if init_handler:
        try:
            logger.info(f"Executing init function: `{init_handler.__name__}`")
            init_handler()
            logger.info(
                f"Init function `{init_handler.__name__}` completed successfully"
            )
        except Exception as e:
            logger.error(f"Init function `{init_handler.__name__}` failed: {e}")
            raise e

    logger.info("Connected to OpenGPU Service 🔵")
    logger.info(f"API docs: http://{SERVICE_HOST}:{SERVICE_PORT}/docs")

    yield


def start():
    """
    Serves registered handler functions as HTTP endpoints using FastAPI.
    Creates a /run/{function}/{task_address} endpoint for each handler.
    """
    logger.info("Starting OpenGPU Service server...")

    app = FastAPI(title="OpenGPU Service", version="0.1.0", lifespan=lifespan)

    def create_endpoint(handler, input_model, function_name):
        """
        Dynamically generates an endpoint function for each handler.
        """

        async def endpoint(
            task_address: str, data: input_model, background_tasks: BackgroundTasks  # type: ignore
        ):
            """
            Runs the handler in the background when an HTTP request is received.
            """

            def runner():
                try:
                    result = handler(data)
                    if result:

                        logger.task_success(  # type: ignore
                            f"[{task_address}] Function: `{function_name}`, Result → "
                            + ", ".join(
                                [f"{k}={v}" for k, v in result.model_dump().items()]
                            )
                        )

                        send_callback(task_address, result.model_dump())

                except Exception as e:
                    logger.task_fail(  # type: ignore
                        f"[{task_address}] Error in `{function_name}`: {e}"
                    )

            background_tasks.add_task(runner)
            return {"task_address": task_address, "status": "accepted"}

        return endpoint

    # Create endpoints for all registered handlers
    for handler, input_model, _output_model in get_handlers():
        function_name = handler.__name__
        path = f"/run/{function_name}/{{task_address}}"

        endpoint = create_endpoint(handler, input_model, function_name)
        app.post(path, status_code=202)(endpoint)
        logger.info(f"Registered endpoint → /run/{function_name}/{{task_address}}")

    # Start FastAPI server
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT, log_level="warning")
