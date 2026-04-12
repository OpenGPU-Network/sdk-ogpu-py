"""Nexus contract — low-level wrappers."""

from __future__ import annotations

from ..types.enums import Role
from ..types.metadata import SourceParams
from ..types.receipt import Receipt
from ._base import TxExecutor, _get_web3, load_contract
from ._signer import Signer, resolve_signer


def publish_source(
    params: SourceParams,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Nexus.publishSource(params)`` and return the mined receipt."""
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("NexusAbi")
    return TxExecutor(
        contract,
        "publishSource",
        (params.to_tuple(),),
        signer=account,
        context="Nexus.publishSource",
    ).execute()


def extract_source_address(receipt: Receipt) -> str:
    """Parse the ``SourcePublished`` log out of a publish receipt."""
    contract = load_contract("NexusAbi")
    logs = contract.events.SourcePublished().process_receipt({"logs": receipt.logs})
    if not logs:
        raise ValueError("SourcePublished event not found in receipt logs")
    return _get_web3().to_checksum_address(logs[0]["args"]["source"])


def update_source(
    source_address: str,
    params: SourceParams,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Nexus.updateSource(source, params)``."""
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("NexusAbi")
    addr = _get_web3().to_checksum_address(source_address)
    return TxExecutor(
        contract,
        "updateSource",
        (addr, params.to_tuple()),
        signer=account,
        context=f"Nexus.updateSource({addr})",
    ).execute()


def inactivate_source(
    source_address: str,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Nexus.inactivateSource(source)``."""
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("NexusAbi")
    addr = _get_web3().to_checksum_address(source_address)
    return TxExecutor(
        contract,
        "inactivateSource",
        (addr,),
        signer=account,
        context=f"Nexus.inactivateSource({addr})",
    ).execute()
