"""Terminal contract — low-level wrappers.

Phase 1 surface:
- ``set_agent(agent, value, *, signer)`` — contract-faithful setAgent
- ``revoke_agent(agent, *, signer)`` — one-line convenience over ``set_agent(.., False)``

Subsequent phases add announce_master / announce_provider / remove_provider,
plus Terminal view accessors and base/live data setters.
"""

from __future__ import annotations

from ..types.enums import Role
from ..types.errors import InvalidSignerError
from ..types.receipt import Receipt
from ._base import TxExecutor, _get_web3, load_contract
from ._signer import Signer, resolve_signer


def set_agent(
    agent: str,
    value: bool,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Call ``Terminal.setAgent(agent, value)`` and return the receipt.

    Only a Client or Master can set an agent — providers are not principals
    in the agent-delegation model (per protocol). The signer env-var fallback
    uses the ``CLIENT_PRIVATE_KEY`` role by default; pass ``signer=`` with a
    master's key to set an agent for a master.
    """
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


def revoke_agent(
    agent: str,
    *,
    signer: Signer | None = None,
) -> Receipt:
    """Convenience wrapper — equivalent to ``set_agent(agent, False, signer=...)``."""
    return set_agent(agent, False, signer=signer)
