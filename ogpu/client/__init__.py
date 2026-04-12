"""Client-role SDK surface.

Publishing helpers return live instance classes (``Source``, ``Task``) as of
Phase 2. ``confirm_response`` and ``set_agent`` still return tx-hash strings
and will migrate to ``Receipt`` in a later phase.
"""

from __future__ import annotations

from typing import Any

from eth_account import Account

from ..protocol.response import Response
from ..protocol.source import Source
from ..protocol.task import Task
from ..types import (
    DeliveryMethod,
    Environment,
    ImageEnvironments,
    SourceInfo,
    SourceMetadata,
    TaskInfo,
    TaskInput,
    combine_environments,
    environment_names,
    parse_environments,
)
from .chain_config import ChainConfig, ChainId
from .config import get_private_key
from .nonce_utils import (
    clear_all_nonce_caches,
    fix_nonce,
    get_nonce_info,
    reset_nonce_cache,
)


def publish_source(
    source_info: SourceInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Source:
    """Publish a source. Returns a ``Source`` instance bound to the new contract."""
    from ..protocol.nexus import extract_source_address
    from ..protocol.nexus import publish_source as _publish_source

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)

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

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)

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

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)
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

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)
    receipt = _set_agent(agent_address, value, signer=account)
    return receipt.tx_hash


def get_task_responses(
    task_address: str,
    lower: int = 0,
    upper: int | None = None,
) -> list[Response]:
    """Thin forwarder — delegates to ``Task(addr).get_responses()``."""
    return Task(task_address).get_responses(lower=lower, upper=upper)


__all__ = [
    # Publishing (instance returns)
    "publish_source",
    "publish_task",
    "confirm_response",
    "set_agent",
    "get_task_responses",
    # Instance classes (re-exported for convenience)
    "Source",
    "Task",
    "Response",
    # Nonce utilities
    "fix_nonce",
    "reset_nonce_cache",
    "clear_all_nonce_caches",
    "get_nonce_info",
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
    # Chain configuration
    "ChainConfig",
    "ChainId",
]
