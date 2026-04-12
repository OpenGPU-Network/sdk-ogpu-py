"""Terminal contract — low-level wrappers."""

from __future__ import annotations

from typing import Any

from ..types.enums import Role
from ..types.errors import InvalidSignerError
from ..types.receipt import Receipt
from ._base import TxExecutor, _get_web3, load_contract
from ._signer import Signer, resolve_signer

# ---------------------------------------------------------------------------
# Write functions
# ---------------------------------------------------------------------------


def set_agent(agent: str, value: bool, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.setAgent(agent, value)``. Client or Master role."""
    account = resolve_signer(signer, role=Role.CLIENT)
    contract = load_contract("TerminalAbi")
    web3 = _get_web3()
    if not web3.is_address(agent):
        raise InvalidSignerError(reason=f"Invalid agent address: {agent}")
    checksum = web3.to_checksum_address(agent)
    return TxExecutor(
        contract,
        "setAgent",
        (checksum, bool(value)),
        signer=account,
        context=f"Terminal.setAgent({checksum}, {value})",
    ).execute()


def revoke_agent(agent: str, *, signer: Signer | None = None) -> Receipt:
    """Convenience — ``set_agent(agent, False, signer=...)``."""
    return set_agent(agent, False, signer=signer)


def announce_master(master_address: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.announceMaster(master)``. Provider-role caller."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("TerminalAbi")
    addr = _get_web3().to_checksum_address(master_address)
    return TxExecutor(
        contract,
        "announceMaster",
        (addr,),
        signer=account,
        context=f"Terminal.announceMaster({addr})",
    ).execute()


def announce_provider(provider: str, amount: int, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.announceProvider(provider, amount)`` (payable). Master-role caller."""
    account = resolve_signer(signer, role=Role.MASTER)
    contract = load_contract("TerminalAbi")
    addr = _get_web3().to_checksum_address(provider)
    return TxExecutor(
        contract,
        "announceProvider",
        (addr, amount),
        signer=account,
        value=amount,
        context=f"Terminal.announceProvider({addr})",
    ).execute()


def remove_provider(provider: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.removeProvider(provider)``. Master-role caller."""
    account = resolve_signer(signer, role=Role.MASTER)
    contract = load_contract("TerminalAbi")
    addr = _get_web3().to_checksum_address(provider)
    return TxExecutor(
        contract,
        "removeProvider",
        (addr,),
        signer=account,
        context=f"Terminal.removeProvider({addr})",
    ).execute()


def remove_container(provider: str, source: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.removeContainer(provider, source)``. Master-role caller."""
    account = resolve_signer(signer, role=Role.MASTER)
    contract = load_contract("TerminalAbi")
    web3 = _get_web3()
    p = web3.to_checksum_address(provider)
    s = web3.to_checksum_address(source)
    return TxExecutor(
        contract,
        "removeContainer",
        (p, s),
        signer=account,
        context=f"Terminal.removeContainer({p}, {s})",
    ).execute()


def set_base_data(data: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.setBaseData(data)``. Provider-role caller."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("TerminalAbi")
    return TxExecutor(
        contract,
        "setBaseData",
        (data,),
        signer=account,
        context="Terminal.setBaseData",
    ).execute()


def set_live_data(data: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.setLiveData(data)``. Provider-role caller."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("TerminalAbi")
    return TxExecutor(
        contract,
        "setLiveData",
        (data,),
        signer=account,
        context="Terminal.setLiveData",
    ).execute()


def set_default_agent_disabled(value: bool, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.setDefaultAgentDisabled(value)``. Provider-role caller."""
    account = resolve_signer(signer, role=Role.PROVIDER)
    contract = load_contract("TerminalAbi")
    return TxExecutor(
        contract,
        "setDefaultAgentDisabled",
        (bool(value),),
        signer=account,
        context="Terminal.setDefaultAgentDisabled",
    ).execute()


# ---------------------------------------------------------------------------
# Read functions
# ---------------------------------------------------------------------------


def _terminal() -> Any:
    return load_contract("TerminalAbi")


def get_master_of(provider: str) -> str:
    return str(_terminal().functions.masterOf(provider).call())


def get_provider_of(master: str) -> str:
    return str(_terminal().functions.providerOf(master).call())


def get_base_data_of(provider: str) -> str:
    return str(_terminal().functions.baseDataOf(provider).call())


def get_live_data_of(provider: str) -> str:
    return str(_terminal().functions.liveDataOf(provider).call())


def is_master(address: str) -> bool:
    return bool(_terminal().functions.isMaster(address).call())


def is_provider(address: str) -> bool:
    return bool(_terminal().functions.isProvider(address).call())


def is_agent_of(account: str, agent: str) -> bool:
    return bool(_terminal().functions.isAgentOf(account, agent).call())


def is_default_agent_disabled(address: str) -> bool:
    return bool(_terminal().functions.defaultAgentDisabled(address).call())
