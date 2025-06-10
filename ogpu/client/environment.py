from enum import IntFlag
from typing import List, Union


class Environment(IntFlag):
    """Environment types with bit mask values for combinations."""

    CPU = 1
    NVIDIA = 2
    AMD = 4


def combine_environments(*environments: Environment) -> int:
    """
    Combine multiple environments using bitwise OR.

    Args:
        environments: Environment values to combine

    Returns:
        Combined environment mask as integer

    Example:
        >>> combine_environments(Environment.CPU, Environment.NVIDIA)
        3
    """
    result = 0
    for env in environments:
        result |= env.value
    return result


def parse_environments(mask: int) -> List[Environment]:
    """
    Parse environment mask into list of Environment values.

    Args:
        mask: Integer mask representing combined environments

    Returns:
        List of Environment values present in the mask

    Example:
        >>> parse_environments(3)
        [<Environment.CPU: 1>, <Environment.NVIDIA: 2>]
    """
    environments = []
    for env in Environment:
        if mask & env.value:
            environments.append(env)
    return environments


def environment_names(mask: int) -> List[str]:
    """
    Get human-readable names for environments in mask.

    Args:
        mask: Integer mask representing combined environments

    Returns:
        List of environment names

    Example:
        >>> environment_names(5)
        ['CPU', 'AMD']
    """
    return [env.name for env in parse_environments(mask) if env.name is not None]
