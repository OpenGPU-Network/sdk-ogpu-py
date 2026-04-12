"""SDK-wide enum definitions.

Status enums (``TaskStatus``, ``SourceStatus``, ``ResponseStatus``) carry
``uint8`` values that mirror the on-chain Solidity enums. The ordering below
is seeded from protocol design and must be verified against live contracts
before instance classes start decoding them in Phase 2.
"""

from __future__ import annotations

from enum import Enum, IntEnum, IntFlag


class TaskStatus(IntEnum):
    """Lifecycle state of a Task contract. Order matches Solidity enum."""

    NEW = 0
    ATTEMPTED = 1
    RESPONDED = 2
    CANCELED = 3
    EXPIRED = 4
    FINALIZED = 5


class SourceStatus(IntEnum):
    """Lifecycle state of a Source contract."""

    ACTIVE = 0
    INACTIVE = 1


class ResponseStatus(IntEnum):
    """Lifecycle state of a Response contract."""

    SUBMITTED = 0
    CONFIRMED = 1


class Environment(IntFlag):
    """Docker-compose execution environments, bit-maskable."""

    CPU = 1
    NVIDIA = 2
    AMD = 4


class DeliveryMethod(Enum):
    """How a Task's winning response is selected."""

    MANUAL_CONFIRMATION = 0
    FIRST_RESPONSE = 1


class Role(Enum):
    """Role used by the signer resolver to pick the right ``*_PRIVATE_KEY`` env var.

    Agents are not principals in the agent-delegation model (per PRD N1) but
    still need an env-var slot for the ``ogpu.agent`` high-level wrappers that
    sign as an authorized delegate of a master or client. Reads ``AGENT_PRIVATE_KEY``.
    """

    CLIENT = "client"
    PROVIDER = "provider"
    MASTER = "master"
    AGENT = "agent"


def combine_environments(*environments: Environment) -> int:
    """Combine multiple ``Environment`` values via bitwise OR."""
    result = 0
    for env in environments:
        result |= env.value
    return result


def parse_environments(mask: int) -> list[Environment]:
    """Parse an integer mask back into a list of ``Environment`` values."""
    return [env for env in Environment if mask & env.value]


def environment_names(mask: int) -> list[str]:
    """Return human-readable names for the environments in a mask."""
    return [env.name for env in parse_environments(mask) if env.name is not None]
