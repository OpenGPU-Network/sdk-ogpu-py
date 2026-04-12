"""Nexus contract — low-level wrappers."""

from __future__ import annotations

from ..types.enums import Role
from ..types.metadata import ResponseParams, SourceParams
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


# ---------------------------------------------------------------------------
# Provider-side writes
# ---------------------------------------------------------------------------


def register(source: str, provider: str, env: int, *, signer: Signer | None = None) -> Receipt:
    """Call ``Nexus.register(source, provider, preferredEnvironment)``."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("NexusAbi")
    web3 = _get_web3()
    s = web3.to_checksum_address(source)
    p = web3.to_checksum_address(provider)
    return TxExecutor(
        contract,
        "register",
        (s, p, env),
        signer=account,
        context=f"Nexus.register({s}, {p})",
    ).execute()


def unregister(source: str, provider: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Nexus.unregister(source, provider)``."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("NexusAbi")
    web3 = _get_web3()
    s = web3.to_checksum_address(source)
    p = web3.to_checksum_address(provider)
    return TxExecutor(
        contract,
        "unregister",
        (s, p),
        signer=account,
        context=f"Nexus.unregister({s}, {p})",
    ).execute()


def attempt(
    task: str, provider: str, suggested_payment: int, *, signer: Signer | None = None
) -> Receipt:
    """Call ``Nexus.attempt(task, provider, suggestedPayment)``."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("NexusAbi")
    web3 = _get_web3()
    t = web3.to_checksum_address(task)
    p = web3.to_checksum_address(provider)
    return TxExecutor(
        contract,
        "attempt",
        (t, p, suggested_payment),
        signer=account,
        context=f"Nexus.attempt({t}, {p})",
    ).execute()


def submit_response(response_params: ResponseParams, *, signer: Signer | None = None) -> Receipt:
    """Call ``Nexus.submitResponse(responseParams)``."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("NexusAbi")
    params_tuple = (
        response_params.task,
        response_params.provider,
        response_params.data,
        response_params.payment,
    )
    return TxExecutor(
        contract,
        "submitResponse",
        (params_tuple,),
        signer=account,
        context="Nexus.submitResponse",
    ).execute()
