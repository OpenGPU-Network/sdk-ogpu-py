import inspect
import threading
from functools import wraps
from typing import get_type_hints

from pydantic import BaseModel

from .handler import add_handler, get_handlers
from .logger import logger


def expose(timeout: int | None = None):
    """
    Decorator to expose user functions as handlers for OpenGPU service.
    The function's input and output must be Pydantic BaseModel.
    An optional timeout can be set for background execution.

    Args:
        timeout (int, optional): Timeout duration in seconds. If set, the handler will return None if not completed within this time.
    """

    def decorator(func):
        function_name = func.__name__
        # Check for unique handler names
        existing_names = [f.__name__ for f, _, _ in get_handlers()]
        if function_name in existing_names:
            raise ValueError(
                f"A handler named `{function_name}` is already registered."
            )

        sig = inspect.signature(func)
        parameters = list(sig.parameters.values())
        if len(parameters) != 1:
            raise TypeError(
                f"Function `{function_name}` must take exactly ONE input argument (got {len(parameters)})"
            )

        hints = get_type_hints(func)
        if "return" not in hints:
            raise TypeError(f"Function `{function_name}` must have a return type.")

        input_model = hints[parameters[0].name]
        output_model = hints["return"]

        # Check if input and output types are subclasses of Pydantic BaseModel
        if not (inspect.isclass(input_model) and issubclass(input_model, BaseModel)):
            raise TypeError(
                f"Input to `{function_name}` must be a subclass of pydantic.BaseModel"
            )

        if not (inspect.isclass(output_model) and issubclass(output_model, BaseModel)):
            raise TypeError(
                f"Return type of `{function_name}` must be a subclass of pydantic.BaseModel"
            )

        if timeout:

            @wraps(func)
            def timed_handler(data):
                """
                Handler that runs with a timeout. Returns None if not completed in time.
                """
                result = [None]
                done = threading.Event()

                def run():
                    try:
                        result[0] = func(data)
                    except Exception as e:
                        logger.task_fail(f"Exception in `{function_name}`: {e}")  # type: ignore
                    finally:
                        done.set()

                thread = threading.Thread(target=run)
                thread.start()
                finished = done.wait(timeout)

                if not finished:
                    logger.task_timeout(  # type: ignore
                        f"`{function_name}` timed out after {timeout} seconds"
                    )
                    # Do not wait for the result, just return None immediately
                    return None

                return result[0]

            add_handler(timed_handler, input_model, output_model)
            return func

        # If no timeout, add handler directly
        add_handler(func, input_model, output_model)
        return func

    return decorator
