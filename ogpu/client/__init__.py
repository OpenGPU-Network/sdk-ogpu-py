"""Client-role SDK surface.

Thin wrappers around the protocol layer for the client role. Every call
accepts a ``private_key=`` kwarg that is resolved via
``resolve_signer(private_key, role=Role.CLIENT)`` — falling back to the
``CLIENT_PRIVATE_KEY`` env var when omitted.

Chain configuration (``ChainConfig``, ``ChainId``, ``fix_nonce``, etc.)
lives in ``ogpu.chain`` and is re-exported at the top level:
``from ogpu import ChainConfig``. Old imports
``from ogpu.client import ChainConfig`` no longer work — see the
v0.2.1 CHANGELOG.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from ..ipfs import publish_to_ipfs
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
    SourceParams,
    TaskInfo,
    TaskInput,
    TaskParams,
    combine_environments,
    environment_names,
    parse_environments,
)
from ..types.errors import TaskExpiredError

logger = logging.getLogger("ogpu.client")


def _check_not_expired(expiry_time: int, stage: str) -> None:
    """Refuse to continue publishing a task whose ``expiryTime`` has passed.

    Guards against the orphaned-task failure mode: when the IPFS pin or
    an RPC call stalls long enough that the task would land on-chain
    already expired (or after the caller gave up), sending the
    transaction only burns gas on a task no provider will pick up.
    Checked before the IPFS upload (fail fast) and again right before
    the transaction is sent (the pin itself may have eaten the budget).
    """
    now = int(time.time())
    if expiry_time <= now:
        logger.warning(
            "publish aborted at %s: expiryTime %d already passed (now %d) — "
            "refusing to publish a task that would be orphaned",
            stage,
            expiry_time,
            now,
        )
        raise TaskExpiredError(task="(not published)", expiry=expiry_time)


def _build_source_params(info: SourceInfo, client_address: str) -> SourceParams:
    """Upload source metadata to IPFS and build the on-chain params tuple.

    Internal helper. Takes a user-facing ``SourceInfo`` dataclass and:

    1. Constructs a ``SourceMetadata`` from the image URLs and display
       fields.
    2. Uploads the metadata as JSON to the OGPU IPFS pinning service
       (``publish_to_ipfs``).
    3. Builds the ``imageEnvironments`` bitmask from which
       ``ImageEnvironments`` fields are non-empty.
    4. Assembles a ``SourceParams`` tuple ready for ``Nexus.publishSource``.

    This used to live as ``SourceInfo.to_source_params()`` on the type
    itself, but that violated the layering rule that ``ogpu.types`` is
    pure data with no network I/O. Moved here to keep the type clean.

    Args:
        info: User-facing source builder.
        client_address: The publishing client's address (from the signer).

    Returns:
        A fully-populated ``SourceParams`` with IPFS URL already set.
    """
    metadata = SourceMetadata(
        cpu=info.imageEnvs.cpu,
        nvidia=info.imageEnvs.nvidia,
        amd=info.imageEnvs.amd,
        name=info.name,
        description=info.description,
        logoUrl=info.logoUrl,
    )
    metadata_url = publish_to_ipfs(metadata.to_dict(), "imageMetadata.json", "application/json")

    combined = 0
    if info.imageEnvs.cpu:
        combined |= Environment.CPU.value
    if info.imageEnvs.nvidia:
        combined |= Environment.NVIDIA.value
    if info.imageEnvs.amd:
        combined |= Environment.AMD.value

    return SourceParams(
        client=client_address,
        imageMetadataUrl=metadata_url,
        imageEnvironments=combined,
        minPayment=info.minPayment,
        minAvailableLockup=info.minAvailableLockup,
        maxExpiryDuration=info.maxExpiryDuration,
        privacyEnabled=False,
        optionalParamsUrl="",
        deliveryMethod=info.deliveryMethod.value,
        lastUpdateTime=int(time.time()),
    )


def _build_task_params(
    info: TaskInfo,
    *,
    ipfs_timeout: float = 30,
    ipfs_retries: int = 2,
    ipfs_backoff: float = 0.5,
    deadline: float | None = None,
) -> TaskParams:
    """Upload task config to IPFS and build the on-chain params tuple.

    Internal helper. Takes a user-facing ``TaskInfo`` dataclass, uploads
    the ``TaskInput`` payload to IPFS as JSON, and returns a
    ``TaskParams`` ready for ``Controller.publishTask``.

    Args:
        info: User-facing task builder.
        ipfs_timeout: Per-attempt cap for the IPFS upload, seconds.
        ipfs_retries: Total attempts on transient IPFS failures.
        ipfs_backoff: Base sleep between IPFS attempts, seconds.
        deadline: Absolute ``time.monotonic()`` cutoff from the caller's
            total publish budget.

    Returns:
        A ``TaskParams`` with ``config`` pointing at the freshly-uploaded
        task config URL.
    """
    config_url = publish_to_ipfs(
        info.config.to_dict(),
        "taskConfig.json",
        "application/json",
        timeout=ipfs_timeout,
        retries=ipfs_retries,
        backoff=ipfs_backoff,
        _deadline=deadline,
    )
    return TaskParams(
        source=info.source,
        config=config_url,
        expiryTime=info.expiryTime,
        payment=info.payment,
    )


def publish_source(
    source_info: SourceInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Source:
    """Publish a new source to the OGPU network.

    Uploads the source metadata to IPFS, calls ``Nexus.publishSource``
    via ``TxExecutor``, and wraps the new source address in a
    ``Source`` instance.

    Args:
        source_info: User-facing ``SourceInfo`` with display fields,
            image URLs, payment config, and delivery method.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``
            environment variable when omitted. May also be a
            ``LocalAccount``.

    Returns:
        A ``Source`` instance bound to the new contract address. You
        can call ``.get_status()``, ``.get_params()``, etc. on it
        immediately.

    Raises:
        MissingSignerError: If no signer is available.
        IPFSGatewayError / IPFSFetchError: If the metadata upload fails.
        TxRevertError or a typed subclass: If the Nexus call reverts.

    Example:
        ```python
        from web3 import Web3
        from ogpu.client import (
            publish_source, SourceInfo, ImageEnvironments, DeliveryMethod,
        )

        source = publish_source(SourceInfo(
            name="sentiment-analyzer",
            description="DistilBERT classifier",
            logoUrl="https://example.com/logo.png",
            imageEnvs=ImageEnvironments(cpu="https://.../compose.yml"),
            minPayment=Web3.to_wei(0.01, "ether"),
            minAvailableLockup=0,
            maxExpiryDuration=86400,
            deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
        ))
        print(source.address, source.get_status())
        ```
    """
    from ..protocol.nexus import extract_source_address
    from ..protocol.nexus import publish_source as _publish_source

    account = resolve_signer(private_key, role=Role.CLIENT)
    params = _build_source_params(source_info, account.address)
    receipt = _publish_source(params, signer=account)
    addr = extract_source_address(receipt)
    return Source(addr)


def publish_task(
    task_info: TaskInfo,
    private_key: str | None = None,
    *,
    ipfs_timeout: float = 30,
    ipfs_retries: int = 2,
    ipfs_backoff: float = 0.5,
    receipt_timeout: float = 120,
    total_timeout: float | None = None,
    **_ignored: Any,
) -> Task:
    """Publish a new task to the OGPU network.

    Uploads the task config (a ``TaskInput``) to IPFS, calls
    ``Controller.publishTask`` via ``TxExecutor``, and wraps the new
    task address in a ``Task`` instance.

    Every leg of the publish is bounded: the IPFS pin by
    ``ipfs_timeout`` × ``ipfs_retries``, the receipt wait by
    ``receipt_timeout``, and (optionally) the whole call by
    ``total_timeout`` — set it and ``publish_task`` always returns or
    raises within that budget, never broadcasting a transaction the
    budget no longer covers.

    Args:
        task_info: User-facing ``TaskInfo`` with source address,
            ``TaskInput`` config, expiry time, and payment.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.
        ipfs_timeout: Per-attempt cap for the IPFS pin, seconds.
            Defaults to 30.
        ipfs_retries: Total IPFS attempts on transient failures
            (connection error, timeout, 5xx). Defaults to 2.
        ipfs_backoff: Base sleep between IPFS attempts, doubled each
            retry. Defaults to 0.5.
        receipt_timeout: Cap on the transaction receipt wait, seconds.
            Defaults to 120.
        total_timeout: Optional single budget in seconds covering pin
            (including retries) + send + receipt. ``None`` (default)
            disables the budget.

    Returns:
        A ``Task`` instance bound to the new contract address.

    Raises:
        MissingSignerError: If no signer is available.
        SourceInactiveError: If the target source has been inactivated.
        InsufficientBalanceError: If the client's vault balance is
            insufficient to cover the task payment.
        IPFSGatewayError / IPFSFetchError: If the config upload fails.
        TaskExpiredError: If ``expiryTime`` has already passed — checked
            before the IPFS upload and again right before the
            transaction is sent, so a stalled pin can never produce an
            on-chain task that is already expired (orphaned, gas wasted).
        TxReceiptTimeoutError: No receipt within ``receipt_timeout`` —
            the transaction WAS broadcast and may still be mined;
            reconcile via the error's ``tx_hash`` before retrying.
        PublishTimeoutError: ``total_timeout`` expired before the
            transaction was broadcast (no gas spent).
        TxRpcError: Unmapped RPC/transport failure (transient variants
            are retried internally first).

    Example:
        ```python
        import time
        from web3 import Web3
        from ogpu.client import publish_task, TaskInfo, TaskInput

        task = publish_task(TaskInfo(
            source="0xSOURCE",
            config=TaskInput(function_name="predict", data={"text": "hi"}),
            expiryTime=int(time.time()) + 3600,
            payment=Web3.to_wei(0.01, "ether"),
        ))
        print(task.address, task.get_status())
        ```
    """
    from ..protocol.controller import extract_task_address
    from ..protocol.controller import publish_task as _publish_task

    deadline = time.monotonic() + total_timeout if total_timeout is not None else None

    account = resolve_signer(private_key, role=Role.CLIENT)
    _check_not_expired(task_info.expiryTime, stage="start")
    params = _build_task_params(
        task_info,
        ipfs_timeout=ipfs_timeout,
        ipfs_retries=ipfs_retries,
        ipfs_backoff=ipfs_backoff,
        deadline=deadline,
    )
    _check_not_expired(task_info.expiryTime, stage="pre-transaction (after IPFS pin)")
    receipt = _publish_task(
        params,
        signer=account,
        receipt_timeout=receipt_timeout,
        deadline=deadline,
        budget=total_timeout,
    )
    addr = extract_task_address(receipt)
    return Task(addr)


def confirm_response(
    response_address: str,
    private_key: str | None = None,
    **_ignored: Any,
) -> str:
    """Confirm a response to finalize the parent task and release payment.

    Calls ``Controller.confirmResponse`` via ``TxExecutor`` and returns
    the transaction hash as a string. Only meaningful for
    ``MANUAL_CONFIRMATION`` delivery — tasks using ``FIRST_RESPONSE``
    finalize automatically on the first submit.

    Args:
        response_address: The response contract to confirm.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        Transaction hash as a 0x-prefixed hex string.

    Raises:
        NotTaskOwnerError: Caller isn't the task's client.
        ResponseAlreadyConfirmedError: Already confirmed.
        MissingSignerError: If no signer is available.

    Example:
        ```python
        from ogpu.client import confirm_response
        tx_hash = confirm_response("0xRESPONSE")
        print(tx_hash)
        # '0x...'
        ```
    """
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
    """Authorize (or revoke) an agent for client-side operations.

    Client-role wrapper over ``Terminal.setAgent``. Use this when you
    want to delegate client-side calls (``publish_task``,
    ``confirm_response``) to an agent address — the agent's key can
    then sign on your behalf.

    For master-side agent setup (delegating provider operations), use
    ``Master(master_addr).set_agent(...)`` instead.

    Args:
        agent_address: Agent to authorize/revoke.
        value: True to authorize, False to revoke.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        Transaction hash as a hex string.
    """
    from ..protocol.terminal import set_agent as _set_agent

    account = resolve_signer(private_key, role=Role.CLIENT)
    receipt = _set_agent(agent_address, value, signer=account)
    return receipt.tx_hash


def get_task_responses(
    task_address: str,
    lower: int = 0,
    upper: int | None = None,
) -> list[Response]:
    """List all responses submitted for a task, as ``Response`` instances.

    Thin forwarder to ``Task(task_address).get_responses(lower, upper)``.
    Useful when you don't want to hold a ``Task`` instance — e.g.
    one-off inspection scripts, dashboards iterating many task addresses.

    Args:
        task_address: Task contract address.
        lower: Start index (inclusive). Defaults to 0.
        upper: End index (exclusive). Defaults to all responses.

    Returns:
        List of ``Response`` instances.

    Example:
        ```python
        from ogpu.client import get_task_responses
        for r in get_task_responses("0xTASK"):
            print(r.address, r.get_status())
        ```
    """
    return Task(task_address).get_responses(lower=lower, upper=upper)


def cancel_task(
    task: str | Task,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Cancel a task (only works before any provider attempts).

    Accepts either a task address string or a ``Task`` instance.
    Returns a ``Receipt`` instead of a tx hash string.

    Args:
        task: Task contract address or ``Task`` instance.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the cancellation.

    Raises:
        NotTaskOwnerError: If the signer isn't the task's client.
        TaskAlreadyFinalizedError: If the task is past ``NEW`` state.

    Example:
        ```python
        from ogpu.client import cancel_task
        receipt = cancel_task("0xTASK")
        print(receipt.tx_hash, receipt.gas_used)
        ```
    """
    from ..protocol.controller import cancel_task as _cancel_task

    account = resolve_signer(private_key, role=Role.CLIENT)
    return _cancel_task(str(task), signer=account)


def update_source(
    source: str | Source,
    new_info: SourceInfo,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Update a source's on-chain parameters.

    Builds a fresh ``SourceParams`` from ``new_info`` (re-uploading the
    metadata to IPFS) and calls ``Nexus.updateSource``. Must be called
    by the source's owner.

    Args:
        source: Source contract address or ``Source`` instance.
        new_info: New ``SourceInfo`` with the updated fields.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the update.

    Raises:
        NotSourceOwnerError: If the signer isn't the source's owner.
    """
    from ..protocol.nexus import update_source as _update_source

    account = resolve_signer(private_key, role=Role.CLIENT)
    params = _build_source_params(new_info, account.address)
    return _update_source(str(source), params, signer=account)


def inactivate_source(
    source: str | Source,
    private_key: str | None = None,
    **_ignored: Any,
) -> Receipt:
    """Inactivate a source (one-way; no reactivation).

    Calls ``Nexus.inactivateSource``. After this, publishing new tasks
    against the source reverts with ``SourceInactiveError``. Existing
    tasks continue their natural lifecycle.

    Args:
        source: Source contract address or ``Source`` instance.
        private_key: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the inactivation.

    Raises:
        NotSourceOwnerError: If the signer isn't the source's owner.
    """
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
