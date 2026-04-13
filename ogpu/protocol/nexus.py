"""Nexus contract — low-level wrappers.

The Nexus contract is the central registry for sources, tasks, and
provider registrations. Every client-side publish operation, every
provider-side task execution, and most status-changing flows run through
Nexus.

This module is a thin 1:1 mirror of the ``NexusAbi`` function surface.
You rarely call these functions directly — the ``ogpu.client`` wrappers
(``publish_source``, ``update_source``, ``inactivate_source``), the
``ogpu.agent`` wrappers (``register_to``, ``attempt``), and the instance
classes (``Source.set_params``, ``Task.cancel``) all delegate here.
"""

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
    """Call ``Nexus.publishSource(params)`` to deploy a new source.

    This is the low-level entry point. ``client.publish_source`` is the
    user-facing wrapper that builds the ``SourceParams`` from a
    ``SourceInfo`` (including IPFS upload of metadata) and then wraps
    the receipt in a ``Source`` instance.

    Args:
        params: Fully-built ``SourceParams`` with ``imageMetadataUrl``
            already pointing at an IPFS-hosted ``SourceMetadata`` JSON.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``
            env var.

    Returns:
        ``Receipt`` for the published source. Use ``extract_source_address``
        to pull the new source's contract address out of the receipt's
        ``SourcePublished`` event log.

    Raises:
        MissingSignerError: If no signer is available.
        TxRevertError / other OGPUError: See ``TxExecutor.execute``.
    """
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
    """Decode the ``SourcePublished`` event log to get the new source's address.

    Used by the ``client.publish_source`` wrapper to turn the raw
    receipt returned by ``publish_source`` into a concrete ``Source``
    instance.

    Args:
        receipt: The ``Receipt`` returned by ``publish_source``.

    Returns:
        Checksummed address of the newly-deployed source contract.

    Raises:
        ValueError: If the receipt does not contain a ``SourcePublished``
            event — shouldn't happen in practice for a successful publish.
    """
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
    """Call ``Nexus.updateSource(source, params)`` to change source parameters.

    Goes through Nexus (rather than the source contract directly) so the
    ``SourceUpdated`` event fires. Must be called by the source's owner.

    Args:
        source_address: The source contract to update.
        params: The new ``SourceParams`` tuple. Typically rebuilt from a
            fresh ``SourceInfo`` via the client wrapper
            ``client.update_source``.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the update transaction.

    Raises:
        NotSourceOwnerError: If the signer isn't the source's owner.
        MissingSignerError: If no signer is available.
    """
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
    """Call ``Nexus.inactivateSource(source)`` to close a source to new tasks.

    One-way transition — there is no "re-activate". Existing tasks under
    the source continue their natural lifecycle but no new tasks can
    be published against it.

    Args:
        source_address: The source contract to inactivate.
        signer: Client signer. Falls back to ``CLIENT_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the inactivation.

    Raises:
        NotSourceOwnerError: If the signer isn't the source's owner.
        MissingSignerError: If no signer is available.
    """
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
    """Call ``Nexus.register(source, provider, preferredEnvironment)``.

    Registers a provider to attempt tasks on a source. Can be called by:

    - The provider itself (passing their own address as ``provider``)
    - The provider's master (who manages them)
    - An agent authorized by the master via ``Terminal.setAgent``

    The protocol's ``isAgentOf`` check in the contract authorizes
    agent-based calls. The signer's role resolution defaults to
    ``PROVIDER`` (reads ``PROVIDER_PRIVATE_KEY``), but you can pass
    any authorized key explicitly via ``signer=``.

    Args:
        source: Source contract address to register to.
        provider: Provider address being registered. Same as signer for
            self-registration; different for master/agent-driven flows.
        env: Preferred environment bitmask from ``Environment``
            (1 = CPU, 2 = NVIDIA, 4 = AMD). Pass a single value — this
            call registers the provider for one environment at a time.
        signer: The signing key. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the registration.

    Raises:
        InsufficientLockupError: Provider doesn't hold enough lockup
            for this source's ``minAvailableLockup``.
        SourceInactiveError: Source is already inactivated.
    """
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
    """Call ``Nexus.unregister(source, provider)``.

    Removes a provider from the source's registrant list. Follows the
    same authorization rules as ``register`` — self, master, or
    authorized agent can call.

    Args:
        source: Source contract address.
        provider: Provider address being unregistered.
        signer: The signing key. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the unregistration.
    """
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
    """Call ``Nexus.attempt(task, provider, suggestedPayment)``.

    Records that a provider is attempting a task. The provider is
    committing to produce a response — the suggested payment field is
    an advisory number about what the provider expects to receive from
    the client's escrowed payment for the task.

    Follows the same authorization rules as ``register``. Sets the
    task's status to ``ATTEMPTED`` on first call if it was ``NEW``.
    If the task has already expired, the transaction may mark it as
    ``EXPIRED`` instead.

    Args:
        task: Task contract address.
        provider: Provider address making the attempt.
        suggested_payment: Advisory payment amount in wei.
        signer: The signing key. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the attempt.

    Raises:
        TaskExpiredError: Task's ``expiryTime`` has passed.
        TaskAlreadyFinalizedError: Task is already in terminal state.
    """
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
    """Call ``Nexus.submitResponse(responseParams)``.

    Deploys a new Response contract and attaches it to the task. The
    ``data`` field inside ``response_params`` is the on-chain record of
    the response — typically an IPFS URL pointing at the actual payload
    (see ``ogpu.ipfs.publish_to_ipfs``).

    Must be called by the provider (or an agent authorized by the
    provider's master). For ``FIRST_RESPONSE`` delivery, this call
    automatically confirms and finalizes the task; for
    ``MANUAL_CONFIRMATION``, the response enters ``SUBMITTED`` state
    and the client must later call ``confirm_response``.

    Args:
        response_params: Pre-built ``ResponseParams`` with task,
            provider, data URL, and payment.
        signer: The signing key. Falls back to ``PROVIDER_PRIVATE_KEY``.

    Returns:
        ``Receipt`` for the submission. Decode ``ResponseSubmitted``
        from the logs to get the new Response contract address.

    Raises:
        TaskExpiredError / TaskAlreadyFinalizedError: Task isn't
            accepting new responses.
    """
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
