"""Agent-role SDK surface.

An **agent** is an address authorized via ``Terminal.setAgent(agent, True)``
by a master or client (per PRD N1, not a provider). Once authorized, the
agent's own key can sign Nexus operations that the protocol accepts via
``isAgentOf(principal, msg.sender)`` checks — without the principal ever
touching the transaction.

The agent is a **scheduler role**: it registers providers to sources,
chooses which providers attempt which tasks, and unregisters stale
providers. It does NOT produce responses — response content comes from
a real compute run (the docker source executing its handler) and must
be signed by the provider whose image produced it. That is why
``submit_response`` is intentionally absent from this surface.

Terminal writes that use ``msg.sender`` to identify the provider
(``setBaseData``, ``setLiveData``, ``setDefaultAgentDisabled``) are also
not mirrored here — those require the provider's own key.

Every function reads ``AGENT_PRIVATE_KEY`` from the environment when
``private_key`` is omitted.

Example:
    ```python
    from ogpu import agent

    # Register a provider to a source (agent signs)
    agent.register_to("0xSRC", "0xPROVIDER", env=1)

    # Submit an attempt
    agent.attempt("0xTASK", "0xPROVIDER", suggested_payment=10**16)

    # Unregister a stale provider
    agent.unregister_from("0xSRC", "0xPROVIDER")
    ```
"""

from __future__ import annotations

from typing import Any

from ..protocol._signer import resolve_signer
from ..types.enums import Role
from ..types.receipt import Receipt


def register_to(
    source: str,
    provider: str,
    env: int,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Register a provider to a source on behalf of the authorizing principal.

    Calls ``Nexus.register`` signed by the agent's key. The protocol
    authorizes the call via its ``isAgentOf`` check against the master
    (or client) that authorized this agent via ``Terminal.setAgent``.

    Args:
        source: Source contract address to register to.
        provider: Provider address being registered. Must be a provider
            managed by the principal that authorized the agent.
        env: Preferred environment bitmask (``Environment.CPU.value`` =
            1, ``NVIDIA`` = 2, ``AMD`` = 4).
        private_key: Agent signer. Falls back to ``AGENT_PRIVATE_KEY``
            environment variable.

    Returns:
        ``Receipt`` for the registration.

    Raises:
        InsufficientLockupError: Provider doesn't hold enough lockup.
        SourceInactiveError: Source is inactivated.
        MissingSignerError: If no signer is available.
    """
    from ..protocol.nexus import register

    account = resolve_signer(private_key, role=Role.AGENT)
    return register(source, provider, env, signer=account)


def unregister_from(
    source: str,
    provider: str,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Unregister a provider from a source on behalf of the authorizing principal.

    Calls ``Nexus.unregister`` signed by the agent's key.

    Args:
        source: Source contract address.
        provider: Provider address to unregister.
        private_key: Agent signer. Falls back to ``AGENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the unregistration.
    """
    from ..protocol.nexus import unregister

    account = resolve_signer(private_key, role=Role.AGENT)
    return unregister(source, provider, signer=account)


def attempt(
    task: str,
    provider: str,
    suggested_payment: int,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Submit an attempt on behalf of a provider, signed by the agent's key.

    Calls ``Nexus.attempt`` — records that the provider is working on
    the task, sets the task status to ``ATTEMPTED`` on first call, and
    commits the provider to eventually produce a response.

    The agent signs, but the ``provider`` argument is the address the
    attempt is attributed to on-chain — the agent is a scheduler, not
    an attempter.

    Args:
        task: Task contract address.
        provider: Provider the attempt is attributed to.
        suggested_payment: Advisory payment the provider expects from
            the client's escrowed payment, in wei.
        private_key: Agent signer. Falls back to ``AGENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the attempt.

    Raises:
        TaskExpiredError: Task has passed its ``expiryTime``.
        TaskAlreadyFinalizedError: Task is in terminal state.
    """
    from ..protocol.nexus import attempt as _attempt

    account = resolve_signer(private_key, role=Role.AGENT)
    return _attempt(task, provider, suggested_payment, signer=account)


__all__ = [
    "register_to",
    "unregister_from",
    "attempt",
]
