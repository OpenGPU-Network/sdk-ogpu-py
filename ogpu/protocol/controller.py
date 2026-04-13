"""Controller contract — low-level wrappers.

The Controller contract handles client-side task lifecycle operations:
publishing new tasks, confirming responses, and canceling tasks. Its
role is distinct from Nexus — Controller mediates payment escrow and
task finalization, while Nexus is the registry and attempt coordinator.

You rarely call these functions directly — the ``ogpu.client`` wrappers
(``publish_task``, ``confirm_response``, ``cancel_task``) build the
params, resolve signers, and hand the result back as instance classes
or typed receipts.
"""

from __future__ import annotations

from ..types.enums import Role
from ..types.metadata import TaskParams
from ..types.receipt import Receipt
from ._base import TxExecutor, _get_web3, load_contract
from ._signer import Signer, resolve_signer


def publish_task(
    params: TaskParams,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Controller.publishTask(params)`` to publish a new task.

    The Controller escrows the payment from the caller, deploys a new
    Task contract, and emits ``TaskPublished`` from Nexus. The returned
    receipt carries that event log — decode it with
    ``extract_task_address`` to get the new task's address.

    This is the low-level entry point. ``client.publish_task`` is the
    user-facing wrapper that builds the ``TaskParams`` from a
    ``TaskInfo`` (including IPFS upload of the config payload) and
    wraps the receipt in a ``Task`` instance.

    Args:
        params: Fully-built ``TaskParams`` with ``config`` already
            pointing at an IPFS-hosted ``TaskInput`` JSON.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``
            env var.

    Returns:
        ``Receipt`` for the published task.

    Raises:
        SourceInactiveError: If the target source is inactive.
        InsufficientBalanceError: If the client doesn't have enough
            vault balance to cover the task's payment.
        MissingSignerError: If no signer is available.
    """
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("ControllerAbi")
    return TxExecutor(
        contract,
        "publishTask",
        (params.to_tuple(),),
        signer=account,
        context="Controller.publishTask",
    ).execute()


def confirm_response(
    response_address: str,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Controller.confirmResponse(response)`` to finalize a task.

    Must be called by the task's client (or their authorized agent).
    Flips the response to ``CONFIRMED``, the parent task to
    ``FINALIZED``, and triggers payment release from the vault to the
    winning provider.

    Only needed for sources using ``MANUAL_CONFIRMATION`` delivery —
    sources with ``FIRST_RESPONSE`` delivery finalize automatically on
    the first ``submitResponse``.

    Args:
        response_address: Response contract address to confirm.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the confirmation.

    Raises:
        NotTaskOwnerError: Caller isn't the task's client.
        ResponseAlreadyConfirmedError: Response is already confirmed.
        ResponseNotFoundError: No Response contract at that address.
    """
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("ControllerAbi")
    web3 = _get_web3()
    checksum = web3.to_checksum_address(response_address)
    return TxExecutor(
        contract,
        "confirmResponse",
        (checksum,),
        signer=account,
        context=f"Controller.confirmResponse({checksum})",
    ).execute()


def extract_task_address(receipt: Receipt) -> str:
    """Decode the ``TaskPublished`` event to get the new task's address.

    Used by the ``client.publish_task`` wrapper to turn the raw receipt
    from ``publish_task`` into a concrete ``Task`` instance. The event
    is emitted by Nexus even though the call goes through Controller,
    so the Nexus ABI is used for decoding.

    Args:
        receipt: The ``Receipt`` returned by ``publish_task``.

    Returns:
        Checksummed address of the newly-deployed Task contract.

    Raises:
        ValueError: If the receipt does not contain a ``TaskPublished``
            event — shouldn't happen for a successful publish.
    """
    nexus = load_contract("NexusAbi")
    logs = nexus.events.TaskPublished().process_receipt({"logs": receipt.logs})
    if not logs:
        raise ValueError("TaskPublished event not found in receipt logs")
    return _get_web3().to_checksum_address(logs[0]["args"]["task"])


def cancel_task(
    task_address: str,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Controller.cancelTask(task)`` to cancel a task before any attempts.

    Only works while the task is in ``NEW`` state — once any provider
    has called ``attempt``, cancel reverts with
    ``TaskAlreadyFinalizedError`` (or similar). Must be called by the
    task's client.

    Successfully canceling a task releases the escrowed payment back
    to the client and transitions the task to ``CANCELED``.

    Args:
        task_address: Task contract to cancel.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the cancellation.

    Raises:
        NotTaskOwnerError: Caller isn't the task's client.
        TaskAlreadyFinalizedError: Task is already past ``NEW`` state.
    """
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("ControllerAbi")
    addr = _get_web3().to_checksum_address(task_address)
    return TxExecutor(
        contract,
        "cancelTask",
        (addr,),
        signer=account,
        context=f"Controller.cancelTask({addr})",
    ).execute()
