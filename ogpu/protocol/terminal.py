"""Terminal contract — low-level wrappers.

The Terminal contract handles identity and delegation: master/provider
pairing, agent authorization, and provider metadata (base and live data).
It's the contract that answers "who is who?" on-chain.

This module mirrors the Terminal ABI 1:1. Higher-level wrappers live in
``ogpu.client.set_agent`` (client-side agent setup), ``Provider`` /
``Master`` instance classes (role-scoped operations), and ``ogpu.agent``
(scheduler-role delegation).
"""

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
    """Call ``Terminal.setAgent(agent, value)`` to authorize or revoke an agent.

    Only clients and masters can set agents. Providers **cannot** — the
    ``Terminal.AgentSet`` event is only triggered by client or master
    signers (see PRD N1 for the protocol rationale).

    Once authorized (``value=True``), the agent's own key can sign
    Nexus operations on behalf of the principal — the contract checks
    ``isAgentOf(principal, msg.sender)`` to authorize calls. Revoke by
    calling again with ``value=False``, or use the ``revoke_agent``
    one-liner.

    The default env-var fallback is ``CLIENT_PRIVATE_KEY`` — pass
    ``signer=`` with a master key to set an agent for a master instead.

    Args:
        agent: Address to authorize/revoke as an agent.
        value: True to authorize, False to revoke.
        signer: Client or master signer. Defaults to
            ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the setAgent call.

    Raises:
        InvalidSignerError: If ``agent`` is not a valid Ethereum address.
        MissingSignerError: If no signer is available.

    Example:
        ```python
        from ogpu.protocol import terminal

        # Client authorizes an agent to sign on their behalf
        terminal.set_agent("0xAGENT", True, signer=CLIENT_KEY)

        # Master authorizes the scheduling agent (The Order)
        terminal.set_agent(
            "0x306Dc3fF30254675B209D916475094401aCC4a1E",
            True,
            signer=MASTER_KEY,
        )
        ```
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


def revoke_agent(agent: str, *, signer: Signer | None = None) -> Receipt:
    """Revoke an agent's authorization.

    Shorthand for ``set_agent(agent, False, signer=...)``. Follows the
    same role/authorization rules — only the principal that authorized
    the agent can revoke.

    Args:
        agent: Address to revoke.
        signer: Client or master signer. Defaults to
            ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the revocation.
    """
    return set_agent(agent, False, signer=signer)


def announce_master(master_address: str, *, signer: Signer | None = None) -> Receipt:
    """Call ``Terminal.announceMaster(master)``. Provider-role caller.

    Second half of the master/provider pairing handshake. After the
    master has called ``announceProvider`` to claim a provider, the
    provider calls ``announceMaster`` to confirm the link from their
    side. Both calls must succeed for ``masterOf(provider)`` to resolve.

    Args:
        master_address: Master address the provider is pairing with.
        signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the announceMaster call.
    """
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
    """Call ``Terminal.announceProvider(provider, amount)``. Master-role caller, payable.

    First half of the master/provider pairing handshake. The master
    claims a provider and sends an initial funding amount in the same
    transaction — the amount gets credited to the provider's vault
    lockup so they become immediately eligible to register to sources.

    Pairing is completed when the provider subsequently calls
    ``announceMaster(master)``.

    Args:
        provider: Provider address being announced.
        amount: Initial lockup amount in wei. Sent as ``msg.value`` in
            the transaction. Pass 0 if the provider already has enough
            lockup from prior deposits.
        signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the announceProvider call.
    """
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
    """Call ``Terminal.removeProvider(provider)``. Master-role caller.

    Breaks the pairing between a master and a provider. After the call,
    ``masterOf(provider)`` no longer resolves and the provider is no
    longer considered managed by that master.

    Args:
        provider: Provider address to remove.
        signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the remove call.
    """
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
    """Call ``Terminal.removeContainer(provider, source)``. Master-role caller.

    Signals that a provider should stop running the source's container.
    Used by the Provider App as a management signal — the container
    itself is not uninstalled by this call; the Provider App reads the
    ``RemoveContainer`` event and tears down the docker instance.

    Args:
        provider: Provider whose container should stop.
        source: Source whose container should stop.
        signer: Master signer. Falls back to ``MASTER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the remove call.
    """
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
    """Call ``Terminal.setBaseData(data)``. Provider-role caller.

    Updates the long-lived metadata URL for a provider. Base data is
    what appears in dashboards — name, description, capabilities,
    hardware specs. The URL typically points at an IPFS-hosted JSON.

    Uses ``msg.sender`` to identify the provider — only the provider
    themselves can update their own base data. Agents cannot call this
    on behalf of a provider.

    Args:
        data: New base data URL (usually IPFS).
        signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the setBaseData call.
    """
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
    """Call ``Terminal.setLiveData(data)``. Provider-role caller.

    Updates the short-lived status URL for a provider. Live data is
    ephemeral — current load, health check results, version info —
    and is refreshed more frequently than base data.

    Like ``set_base_data``, this uses ``msg.sender`` and cannot be
    called by an agent on behalf of a provider.

    Args:
        data: New live data URL.
        signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the setLiveData call.
    """
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
    """Call ``Terminal.setDefaultAgentDisabled(value)``. Provider-role caller.

    Opts a provider out of (or back into) default agent delegation.
    When disabled, the default scheduling agent (The Order) no longer
    dispatches tasks to this provider automatically — the provider
    becomes invisible to the built-in scheduler and has to be
    dispatched manually.

    Like the base/live data setters, this uses ``msg.sender`` to
    identify the provider.

    Args:
        value: True to disable the default agent, False to re-enable it.
        signer: Provider signer. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the setDefaultAgentDisabled call.
    """
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
    """Return the Terminal contract instance (singleton for the current chain)."""
    return load_contract("TerminalAbi")


def get_master_of(provider: str) -> str:
    """Return the master paired with a provider.

    Returns the zero address if the provider is not currently paired
    with any master.

    Args:
        provider: Provider address to look up.

    Returns:
        The master's checksummed address, or the zero address if unpaired.
    """
    return str(_terminal().functions.masterOf(provider).call())


def get_provider_of(master: str) -> str:
    """Return the provider paired with a master.

    The inverse lookup of ``get_master_of``. Returns the zero address
    if the master has not paired with any provider.

    Args:
        master: Master address to look up.

    Returns:
        The provider's checksummed address, or the zero address if unpaired.
    """
    return str(_terminal().functions.providerOf(master).call())


def get_base_data_of(provider: str) -> str:
    """Return the current base data URL for a provider.

    Args:
        provider: Provider address to look up.

    Returns:
        The base data URL as stored on-chain, or an empty string if
        never set.
    """
    return str(_terminal().functions.baseDataOf(provider).call())


def get_live_data_of(provider: str) -> str:
    """Return the current live data URL for a provider.

    Args:
        provider: Provider address to look up.

    Returns:
        The live data URL as stored on-chain, or an empty string if
        never set.
    """
    return str(_terminal().functions.liveDataOf(provider).call())


def is_master(address: str) -> bool:
    """Return whether an address is registered as a master.

    Args:
        address: Address to check.

    Returns:
        True if the address has been announced as a master by at least
        one provider.
    """
    return bool(_terminal().functions.isMaster(address).call())


def is_provider(address: str) -> bool:
    """Return whether an address is registered as a provider.

    Args:
        address: Address to check.

    Returns:
        True if the address has been announced as a provider by at
        least one master.
    """
    return bool(_terminal().functions.isProvider(address).call())


def is_agent_of(account: str, agent: str) -> bool:
    """Return whether ``agent`` is authorized to sign on behalf of ``account``.

    Args:
        account: The principal (client or master address).
        agent: The candidate agent address.

    Returns:
        True if ``account`` has called ``set_agent(agent, True)``.
    """
    return bool(_terminal().functions.isAgentOf(account, agent).call())


def is_default_agent_disabled(address: str) -> bool:
    """Return whether the provider opted out of default agent delegation.

    Args:
        address: Provider address to check.

    Returns:
        True if the provider has disabled the default scheduling agent.
    """
    return bool(_terminal().functions.defaultAgentDisabled(address).call())
