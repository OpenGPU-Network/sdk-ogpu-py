from typing import Callable, List, Tuple, Type

from pydantic import BaseModel

# List of registered handler functions: (function, input model, output model)
_exposed_handlers: List[Tuple[Callable, Type[BaseModel], Type[BaseModel]]] = []


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
