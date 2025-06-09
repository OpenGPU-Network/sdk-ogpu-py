import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI

from .config import CALLBACK_ADDRESS, SERVICE_HOST, SERVICE_PORT
from .handler import get_handlers
from .logger import logger


def send_callback(task_address: str, result: dict):
    """
    Placeholder function to send a callback with the result.
    This function should be implemented to handle the callback logic.
    """
    # Implement the callback logic here
    callback_url = f"{CALLBACK_ADDRESS}/{task_address}"
    # Example: Use requests or httpx to send the result to the callback URL
    response = requests.post(callback_url, json=result)
    if response.status_code != 200:
        logger.error(f"Failed to send callback: {response.status_code} {response.text}")
    logger.info(f"Callback sent to {callback_url} with result: {result}")


def start():
    """
    Serves registered handler functions as HTTP endpoints using FastAPI.
    Creates a /run/{function}/{task_address} endpoint for each handler.
    """
    logger.info("Starting OpenGPU Service server...")
    app = FastAPI(title="OpenGPU Service", version="0.1.0")

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
                        ## callback operation
                        send_callback(task_address, result.model_dump())

                        logger.task_success(  # type: ignore
                            f"[{task_address}] Function: `{function_name}`, Result → "
                            + ", ".join(
                                [f"{k}={v}" for k, v in result.model_dump().items()]
                            )
                        )
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

    logger.info("Connected to OpenGPU Service 🔵")
    logger.info("Listening on http://0.0.0.0:5555")

    # Start FastAPI server
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT, log_level="warning")
