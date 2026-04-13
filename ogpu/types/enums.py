"""SDK-wide enum definitions.

Every status enum mirrors a Solidity ``enum`` on the corresponding contract.
Values are ``uint8`` on-chain and map 1:1 to the Python member order below.

The SDK decodes raw integers from contract calls into these typed enums
automatically — you shouldn't have to compare to raw numbers in your code.
"""

from __future__ import annotations

from enum import Enum, IntEnum, IntFlag


class TaskStatus(IntEnum):
    """Lifecycle state of a ``Task`` contract.

    Tasks progress through these states as providers attempt, respond,
    and the client confirms. The protocol transitions happen on the
    ``Nexus`` contract — this enum mirrors the Solidity ``TaskStatus``
    enum 1:1.

    Members:
        NEW: Task was just published, no attempts yet.
        ATTEMPTED: At least one provider has called ``attempt``.
        RESPONDED: At least one provider has submitted a response.
        CANCELED: Client called ``cancel_task`` before any attempts.
        EXPIRED: Task's ``expiryTime`` passed before finalization; set on
            the next ``Nexus.attempt`` call.
        FINALIZED: A response was confirmed (via ``confirm_response`` for
            ``MANUAL_CONFIRMATION``, or automatically on first submit for
            ``FIRST_RESPONSE``). Task is done.

    Example:
        ```python
        task = Task.load("0x...")
        task.get_status()
        # <TaskStatus.NEW: 0>

        task.get_status() == TaskStatus.FINALIZED
        # False
        ```
    """

    NEW = 0
    ATTEMPTED = 1
    RESPONDED = 2
    CANCELED = 3
    EXPIRED = 4
    FINALIZED = 5


class SourceStatus(IntEnum):
    """Lifecycle state of a ``Source`` contract.

    Sources are either accepting new tasks (``ACTIVE``) or permanently
    closed to new tasks (``INACTIVE``). Inactivation is one-way — once
    a source is inactivated, it cannot be reactivated. Existing tasks
    continue to their natural lifecycle but no new tasks can be
    published against the source.

    Members:
        ACTIVE: Source accepts new tasks.
        INACTIVE: Source is closed to new tasks. Publishing reverts
            with ``SourceInactiveError``.
    """

    ACTIVE = 0
    INACTIVE = 1


class ResponseStatus(IntEnum):
    """Lifecycle state of a ``Response`` contract.

    Responses are either waiting for confirmation (``SUBMITTED``) or
    have been confirmed by the client (``CONFIRMED``). Confirmation
    releases payment from the vault and finalizes the parent task.

    Members:
        SUBMITTED: Provider submitted a response, awaiting client decision
            (``MANUAL_CONFIRMATION``) or automatic confirmation
            (``FIRST_RESPONSE`` — flips immediately to ``CONFIRMED``).
        CONFIRMED: Client (or the protocol, for first-response delivery)
            has confirmed this response as the winner.
    """

    SUBMITTED = 0
    CONFIRMED = 1


class Environment(IntFlag):
    """Docker-compose execution environments supported by a source.

    An ``IntFlag`` — combine with bitwise OR to indicate that a source
    provides images for multiple hardware targets. The on-chain
    ``imageEnvironments`` field is a ``uint8`` bitmask using the same
    values.

    Members:
        CPU: Generic x86_64 CPU-only image (value = 1).
        NVIDIA: NVIDIA GPU image using CUDA (value = 2).
        AMD: AMD GPU image using ROCm (value = 4).

    Example:
        ```python
        Environment.CPU | Environment.NVIDIA
        # <Environment.NVIDIA|CPU: 3>

        combine_environments(Environment.CPU, Environment.AMD)
        # 5
        ```
    """

    CPU = 1
    NVIDIA = 2
    AMD = 4


class DeliveryMethod(Enum):
    """How a Task's winning response is selected.

    Set on a source via ``SourceInfo.deliveryMethod`` at publish time and
    inherited by every task published to that source.

    Members:
        MANUAL_CONFIRMATION: Multiple providers can attempt and submit.
            Client reviews the responses and explicitly calls
            ``confirm_response`` on the one they accept. Slower but
            higher-quality.
        FIRST_RESPONSE: The first submitted response is automatically
            confirmed on-chain. Fast and cheap — no manual client action
            required. Good for public-result tasks.

    Example:
        ```python
        from ogpu.client import SourceInfo, DeliveryMethod
        info = SourceInfo(..., deliveryMethod=DeliveryMethod.FIRST_RESPONSE)
        ```
    """

    MANUAL_CONFIRMATION = 0
    FIRST_RESPONSE = 1


class Role(Enum):
    """Identifies which role a signer is acting as.

    ``resolve_signer`` uses this to pick the right ``*_PRIVATE_KEY``
    environment variable when no explicit signer is passed:

    - ``Role.CLIENT`` → reads ``CLIENT_PRIVATE_KEY``
    - ``Role.PROVIDER`` → reads ``PROVIDER_PRIVATE_KEY``
    - ``Role.MASTER`` → reads ``MASTER_PRIVATE_KEY``
    - ``Role.AGENT`` → reads ``AGENT_PRIVATE_KEY``

    You rarely touch this directly — every high-level wrapper
    (``client.publish_task``, ``agent.register_to``, etc.) already knows
    which role it's acting as and passes it to ``resolve_signer``
    internally. You only see it in error messages
    (``MissingSignerError(role=...)``) or when calling ``resolve_signer``
    by hand for custom protocol flows.

    Note:
        Agents are not *principals* in the agent-delegation model — an
        agent is an address authorized to sign on behalf of a master or
        client. The role exists purely so the SDK can look up the agent's
        own env var when it signs. See PRD N1 for the full rationale.
    """

    CLIENT = "client"
    PROVIDER = "provider"
    MASTER = "master"
    AGENT = "agent"


def combine_environments(*environments: Environment) -> int:
    """Combine multiple ``Environment`` values via bitwise OR.

    Useful when constructing an ``imageEnvironments`` bitmask by hand for
    a ``SourceParams`` tuple. Most user code doesn't need this — the
    client wrapper builds the bitmask automatically from the
    ``ImageEnvironments`` dataclass in a ``SourceInfo``.

    Args:
        *environments: Any number of ``Environment`` members.

    Returns:
        An integer bitmask combining all given environments.

    Example:
        ```python
        combine_environments(Environment.CPU, Environment.NVIDIA)
        # 3

        combine_environments(Environment.CPU, Environment.NVIDIA, Environment.AMD)
        # 7
        ```
    """
    result = 0
    for env in environments:
        result |= env.value
    return result


def parse_environments(mask: int) -> list[Environment]:
    """Decode an ``imageEnvironments`` bitmask back into individual environments.

    The inverse of ``combine_environments``. Given a ``uint8`` mask from
    an on-chain ``SourceParams`` tuple, return the list of ``Environment``
    members that are set.

    Args:
        mask: Integer bitmask, typically ``source.get_params().imageEnvironments``.

    Returns:
        List of ``Environment`` members that appear in the mask, in
        declaration order (CPU, NVIDIA, AMD).

    Example:
        ```python
        parse_environments(5)
        # [<Environment.CPU: 1>, <Environment.AMD: 4>]
        ```
    """
    return [env for env in Environment if mask & env.value]


def environment_names(mask: int) -> list[str]:
    """Return the human-readable names for environments set in a bitmask.

    A convenience over ``parse_environments`` that yields strings suitable
    for logs, dashboards, and user-facing display.

    Args:
        mask: Integer bitmask, typically ``source.get_params().imageEnvironments``.

    Returns:
        List of environment name strings in declaration order.

    Example:
        ```python
        environment_names(5)
        # ['CPU', 'AMD']
        environment_names(7)
        # ['CPU', 'NVIDIA', 'AMD']
        ```
    """
    return [env.name for env in parse_environments(mask) if env.name is not None]
