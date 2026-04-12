"""Controller contract — low-level wrappers."""

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
    """Call ``Controller.publishTask(params)`` and return the mined receipt."""
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
    """Call ``Controller.confirmResponse(response)`` and return the receipt."""
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
    """Parse the ``TaskPublished`` Nexus log out of a publishTask receipt.

    ``publishTask`` is called on Controller but emits ``TaskPublished`` on
    Nexus. The Nexus ABI is used to decode the log.
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
    """Call ``Controller.cancelTask(task)``."""
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
