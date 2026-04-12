"""Client-role SDK surface.

Thin wrappers around the protocol layer for the client role. Every call
accepts a ``private_key=`` kwarg that is resolved via
``resolve_signer(private_key, role=Role.CLIENT)`` — falling back to the
``CLIENT_PRIVATE_KEY`` env var when omitted.

Chain configuration (`ChainConfig`, `ChainId`, `fix_nonce`, etc.) lives in
``ogpu.chain`` and is re-exported at the top level: ``from ogpu import
ChainConfig``. Old imports ``from ogpu.client import ChainConfig`` no
longer work — see the v0.2.1 CHANGELOG.
"""

from __future__ import annotations

from typing import Any

from ..protocol._signer import resolve_signer
from ..protocol.response import Response
from ..protocol.source import Source
from ..protocol.task import Task
from ..types import (
    DeliveryMethod,
    Environment,
    ImageEnvironments,
    Receipt,
    Role,
    SourceInfo,
    SourceMetadata,
    TaskInfo,
    TaskInput,
    combine_environments,
    environment_names,
    parse_environments,
)


def publish_source(
    source_info: SourceInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Source:
    """Publish a source. Returns a ``Source`` instance bound to the new contract."""
    from ..protocol.nexus import extract_source_address
    from ..protocol.nexus import publish_source as _publish_source

    account = resolve_signer(private_key, role=Role.CLIENT)
    params = source_info.to_source_params(account.address)
    receipt = _publish_source(params, signer=account)
    addr = extract_source_address(receipt)
    return Source(addr)


def publish_task(
    task_info: TaskInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Task:
    """Publish a task. Returns a ``Task`` instance bound to the new contract."""
    from ..protocol.controller import extract_task_address
    from ..protocol.controller import publish_task as _publish_task

    account = resolve_signer(private_key, role=Role.CLIENT)
    params = task_info.to_task_params()
    receipt = _publish_task(params, signer=account)
    addr = extract_task_address(receipt)
    return Task(addr)


def confirm_response(
    response_address: str,
    private_key: str | None = None,
    **_ignored: Any,
) -> str:
    """Confirm a response. Returns the tx hash string."""
    from ..protocol.controller import confirm_response as _confirm_response

    account = resolve_signer(private_key, role=Role.CLIENT)
    receipt = _confirm_response(response_address, signer=account)
    return receipt.tx_hash


def set_agent(
    agent_address: str,
    value: bool,
    private_key: str | None = None,
    **_ignored: Any,
) -> str:
    """Set agent status on the Terminal contract. Returns the tx hash string."""
    from ..protocol.terminal import set_agent as _set_agent

    account = resolve_signer(private_key, role=Role.CLIENT)
    receipt = _set_agent(agent_address, value, signer=account)
    return receipt.tx_hash


def get_task_responses(
    task_address: str,
    lower: int = 0,
    upper: int | None = None,
) -> list[Response]:
    """Thin forwarder — delegates to ``Task(addr).get_responses()``."""
    return Task(task_address).get_responses(lower=lower, upper=upper)


def cancel_task(
    task: str | Task,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Cancel a task. Returns ``Receipt``."""
    from ..protocol.controller import cancel_task as _cancel_task

    account = resolve_signer(private_key, role=Role.CLIENT)
    return _cancel_task(str(task), signer=account)


def update_source(
    source: str | Source,
    new_info: SourceInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Update a source's on-chain params. Returns ``Receipt``."""
    from ..protocol.nexus import update_source as _update_source

    account = resolve_signer(private_key, role=Role.CLIENT)
    params = new_info.to_source_params(account.address)
    return _update_source(str(source), params, signer=account)


def inactivate_source(
    source: str | Source,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Inactivate a source. Returns ``Receipt``."""
    from ..protocol.nexus import inactivate_source as _inactivate_source

    account = resolve_signer(private_key, role=Role.CLIENT)
    return _inactivate_source(str(source), signer=account)


__all__ = [
    # Publishing (instance returns)
    "publish_source",
    "publish_task",
    "confirm_response",
    "set_agent",
    "get_task_responses",
    # Phase 3 client operations
    "cancel_task",
    "update_source",
    "inactivate_source",
    # Instance classes (re-exported for convenience)
    "Source",
    "Task",
    "Response",
    # Types re-exported from ogpu.types
    "SourceInfo",
    "TaskInfo",
    "TaskInput",
    "SourceMetadata",
    "ImageEnvironments",
    "DeliveryMethod",
    "Environment",
    "combine_environments",
    "environment_names",
    "parse_environments",
]
