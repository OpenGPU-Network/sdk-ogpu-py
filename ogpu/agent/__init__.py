"""Agent-role SDK surface.

An **agent** is an address authorized via ``Terminal.setAgent(agent, true)`` by
a master or a client (per PRD N1, not a provider). Once authorized, the agent's
own key can sign Nexus operations that the protocol accepts via
``isAgentOf(principal, msg.sender)`` checks — without the master ever having to
touch the transaction.

The agent is a **scheduler role**: it registers providers to sources, chooses
which providers attempt which tasks, and unregisters stale providers. It does
NOT produce responses — response content is output from an actual compute run
and must be signed by the provider whose docker image produced it. That is why
``submit_response`` is intentionally absent from this surface.

Terminal writes that use ``msg.sender`` to identify the provider
(``setBaseData``, ``setLiveData``, ``setDefaultAgentDisabled``) are also not
mirrored here — those require the provider's own key.

Every function reads ``AGENT_PRIVATE_KEY`` from the environment when
``private_key`` is omitted.
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
    """Register a provider to a source, signed by the agent's key."""
    from ..protocol.nexus import register

    account = resolve_signer(private_key, role=Role.AGENT)
    return register(source, provider, env, signer=account)


def unregister_from(
    source: str,
    provider: str,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Unregister a provider from a source, signed by the agent's key."""
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
    """Submit an attempt on behalf of a provider, signed by the agent's key."""
    from ..protocol.nexus import attempt as _attempt

    account = resolve_signer(private_key, role=Role.AGENT)
    return _attempt(task, provider, suggested_payment, signer=account)


__all__ = [
    "register_to",
    "unregister_from",
    "attempt",
]
