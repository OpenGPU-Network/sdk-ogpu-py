from typing import Callable, List, Tuple, Type

from pydantic import BaseModel

# List of registered handler functions: (function, input model, output model)
_exposed_handlers: List[Tuple[Callable, Type[BaseModel], Type[BaseModel]]] = []

# Single registered initialization function
_init_handler: Callable | None = None


def add_handler(
    fn: Callable, input_model: Type[BaseModel], output_model: Type[BaseModel]
):
    """
    Registers a new handler function with its input and output models.

    Args:
        fn (Callable): The handler function to register.
        input_model (Type[BaseModel]): The Pydantic model for input validation.
        output_model (Type[BaseModel]): The Pydantic model for output validation.
    """
    _exposed_handlers.append((fn, input_model, output_model))


def get_handlers():
    """
    Returns all registered handler functions.

    Returns:
        List[Tuple[Callable, Type[BaseModel], Type[BaseModel]]]:
            A list of tuples containing the handler function, input model, and output model.
    """
    return _exposed_handlers


def add_init_handler(fn: Callable):
    """
    Registers a single initialization function to be executed at server startup.
    If an init handler is already registered, raises an error.

    Args:
        fn (Callable): The initialization function to register.
    """
    global _init_handler
    if _init_handler is not None:
        raise ValueError(
            f"An init handler `{_init_handler.__name__}` is already registered. Only one init function is allowed."
        )
    _init_handler = fn


def get_init_handler():
    """
    Returns the registered initialization function.

    Returns:
        Callable | None: The initialization function or None if not registered.
    """
    return _init_handler
