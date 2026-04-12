"""Client-role SDK surface.

Phase 1 transitional layer. End users import publishing helpers and type
builders from here. The functions delegate to ``ogpu.protocol`` internally
but preserve the v0.2.0.x return types (string addresses / tx hashes) so the
existing example scripts and in-flight test code keep working until
v0.2.1 ships after Phase 7. Phase 2 flips ``publish_source`` / ``publish_task``
to return ``Source`` / ``Task`` instances; Phase 7 rewrites examples.
"""

from __future__ import annotations

from typing import Any

from eth_account import Account

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
) -> str:
    """Publish a source. Returns the new source contract address (string).

    Phase 1 transitional: accepts the old kwargs (nonce, auto_fix_nonce,
    max_retries) and silently ignores them — ``TxExecutor`` now handles the
    retry logic centrally. Return type will change to ``Source`` in Phase 2.
    """
    from ..protocol.nexus import extract_source_address
    from ..protocol.nexus import publish_source as _publish_source

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)

    params = source_info.to_source_params(account.address)
    receipt = _publish_source(params, signer=account)
    return extract_source_address(receipt)


def publish_task(
    task_info: TaskInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> str:
    """Publish a task. Returns the new task contract address (string).

    Phase 1 transitional — see ``publish_source``.
    """
    from ..protocol.controller import extract_task_address
    from ..protocol.controller import publish_task as _publish_task

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)

    params = task_info.to_task_params()
    receipt = _publish_task(params, signer=account)
    return extract_task_address(receipt)


def confirm_response(
    response_address: str,
    private_key: str | None = None,
    **_ignored: Any,
) -> str:
    """Confirm a response. Returns the tx hash string.

    Phase 1 transitional wrapper.
    """
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
    """Set agent status on the Terminal contract. Returns the tx hash string.

    Phase 1 transitional wrapper — replaces the deleted ``ogpu.agent.set_agent``.
    New protocol-level API at ``ogpu.protocol.terminal.set_agent`` uses
    ``signer=`` instead of ``private_key=``.
    """
    from ..protocol.terminal import set_agent as _set_agent

    if private_key is None:
        private_key = get_private_key()
    account = Account.from_key(private_key)
    receipt = _set_agent(agent_address, value, signer=account)
    return receipt.tx_hash


__all__ = [
    # Publishing (transitional string returns)
    "publish_source",
    "publish_task",
    "confirm_response",
    "set_agent",
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
