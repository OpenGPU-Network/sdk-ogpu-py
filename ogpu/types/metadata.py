"""Metadata and on-chain struct types.

Three layers of types live here, all pure data (no side effects, no
network I/O):

1. **User-facing builders** — ``SourceInfo``, ``TaskInfo``, ``TaskInput``,
   ``ImageEnvironments``, ``SourceMetadata``. These are what you construct
   in application code before calling ``client.publish_source`` /
   ``client.publish_task``.

2. **On-chain struct mirrors** — ``SourceParams``, ``TaskParams``,
   ``ResponseParams``. These are 1:1 typed mirrors of the Solidity tuples
   passed to or returned from the contracts. The client layer builds them
   from the user-facing builders before calling ``TxExecutor``.

3. **Snapshot dataclasses** — ``SourceSnapshot``, ``TaskSnapshot``,
   ``ResponseSnapshot``, ``ProviderSnapshot``, ``MasterSnapshot``. Frozen
   captures returned by each instance class's ``snapshot()`` method —
   every field fetched in one logical batch of RPCs, then cached locally.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .enums import DeliveryMethod, ResponseStatus, SourceStatus, TaskStatus


@dataclass
class ImageEnvironments:
    """Docker-compose URLs for each hardware environment a source supports.

    A source may provide one, two, or three compose files — one per
    target hardware. Empty strings mean the source does not support
    that environment. The client layer translates the non-empty fields
    into an ``imageEnvironments`` bitmask when building ``SourceParams``.

    Attributes:
        cpu: URL to a docker-compose file for generic CPU execution.
        nvidia: URL to a docker-compose file for NVIDIA GPU execution.
        amd: URL to a docker-compose file for AMD GPU execution.

    Example:
        ```python
        ImageEnvironments(cpu="https://raw.githubusercontent.com/.../compose.yml")
        ImageEnvironments(
            cpu="https://.../compose.cpu.yml",
            nvidia="https://.../compose.gpu.yml",
        )
        ```
    """

    cpu: str = ""
    nvidia: str = ""
    amd: str = ""


@dataclass
class SourceMetadata:
    """Off-chain metadata package for a source.

    This is what gets uploaded to IPFS before ``Nexus.publishSource`` is
    called — the resulting URL goes into ``SourceParams.imageMetadataUrl``.
    Contains both the docker-compose URLs (one per environment) and the
    display fields shown in dashboards (name, description, logo).

    Formerly named ``ImageMetadata`` — the name was misleading because
    it sounded like just-the-docker-image metadata, when it actually
    contains the full off-chain source descriptor.

    Attributes:
        cpu: Docker-compose URL for CPU execution.
        nvidia: Docker-compose URL for NVIDIA GPU execution.
        amd: Docker-compose URL for AMD GPU execution.
        name: Human-readable source name.
        description: Short description of what the source does.
        logoUrl: URL to a logo image for display.

    Example:
        ```python
        meta = SourceMetadata(
            cpu="https://.../compose.yml",
            nvidia="",
            amd="",
            name="sentiment-analyzer",
            description="DistilBERT classifier",
            logoUrl="https://example.com/logo.png",
        )
        meta.to_dict()
        # {'cpu': 'https://.../compose.yml', 'nvidia': '', 'amd': '', ...}
        ```
    """

    cpu: str
    nvidia: str
    amd: str
    name: str
    description: str
    logoUrl: str

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict representation suitable for JSON serialization."""
        return {
            "cpu": self.cpu,
            "nvidia": self.nvidia,
            "amd": self.amd,
            "name": self.name,
            "description": self.description,
            "logoUrl": self.logoUrl,
        }


class SourceParams(BaseModel):
    """Typed mirror of the Solidity ``Nexus.publishSource`` input tuple.

    You rarely construct this by hand — the client wrapper builds it
    from a ``SourceInfo`` before calling the contract. You do see it
    coming back from ``Source.get_params()``, and it appears inside
    ``SourceSnapshot``.

    The ``to_tuple`` method produces the raw tuple that web3 expects
    when encoding the transaction data.

    Attributes:
        client: Address that owns the source (the one who published it).
        imageMetadataUrl: IPFS URL pointing at a ``SourceMetadata`` JSON.
        imageEnvironments: Bitmask of ``Environment`` flags.
        minPayment: Minimum wei a task must pay to be publishable.
        minAvailableLockup: Minimum vault lockup a provider must hold
            to register to this source.
        maxExpiryDuration: Maximum seconds a task against this source
            can live before expiring.
        privacyEnabled: Reserved for future use — currently always False.
        optionalParamsUrl: Reserved for future use — currently empty.
        deliveryMethod: Integer value of the ``DeliveryMethod`` enum
            (0 = MANUAL_CONFIRMATION, 1 = FIRST_RESPONSE).
        lastUpdateTime: Unix timestamp of the last update to this source.
    """

    client: str
    imageMetadataUrl: str
    imageEnvironments: int
    minPayment: int
    minAvailableLockup: int
    maxExpiryDuration: int
    privacyEnabled: bool
    optionalParamsUrl: str
    deliveryMethod: int
    lastUpdateTime: int = int(time.time())

    def to_tuple(self) -> tuple[str, str, int, int, int, int, bool, str, int, int]:
        """Return the raw tuple web3 expects for contract encoding."""
        return (
            self.client,
            self.imageMetadataUrl,
            self.imageEnvironments,
            self.minPayment,
            self.minAvailableLockup,
            self.maxExpiryDuration,
            self.privacyEnabled,
            self.optionalParamsUrl,
            self.deliveryMethod,
            self.lastUpdateTime,
        )


class TaskParams(BaseModel):
    """Typed mirror of the Solidity ``Controller.publishTask`` input tuple.

    Built by the client wrapper from a ``TaskInfo``. You see it coming
    back from ``Task.get_params()``, and it appears inside ``TaskSnapshot``.

    Attributes:
        source: Source contract address the task targets.
        config: IPFS URL pointing at a JSON-encoded ``TaskInput``.
        expiryTime: Unix timestamp after which the task is considered expired.
        payment: Amount in wei the client is willing to pay per completion.
    """

    source: str
    config: str
    expiryTime: int
    payment: int

    def to_tuple(self) -> tuple[str, str, int, int]:
        """Return the raw tuple web3 expects for contract encoding."""
        return (self.source, self.config, self.expiryTime, self.payment)


@dataclass(frozen=True)
class ResponseParams:
    """Typed mirror of what ``Response.getResponseParams()`` returns on-chain.

    Also used as the *input* when a provider calls
    ``Nexus.submitResponse`` — frozen because once constructed, the
    values are what gets encoded and sent.

    Attributes:
        task: Task contract address this response is for.
        provider: Provider address that produced the response.
        data: Off-chain payload URL (typically IPFS).
        payment: Wei the provider is claiming for this response.

    Example:
        ```python
        from ogpu.types import ResponseParams
        params = ResponseParams(
            task="0xTASK",
            provider="0xPROV",
            data="https://cipfs.../Qm123",
            payment=10**16,
        )
        ```
    """

    task: str
    provider: str
    data: str
    payment: int


@dataclass
class TaskInput:
    """Operational input for a task — function name + data + extras.

    The client puts this into ``TaskInfo.config``. The client wrapper
    uploads it to IPFS before publishing, so the on-chain
    ``TaskParams.config`` field ends up as an IPFS URL. Providers
    download it, decode the JSON, and call the matching ``@expose``'d
    handler on their running source.

    The ``function_name`` field is mandatory — it's how the source
    framework routes the call to the right handler. Everything else
    (``data``, plus any extra kwargs) is passed through unchanged.

    Attributes:
        function_name: Name of the handler to invoke on the source.
            Must match an ``@ogpu.service.expose()``'d function.
        data: The actual input payload. Accepts a Pydantic model or a
            plain dict. Pydantic models are dumped via ``model_dump()``
            before serialization.

    Extras:
        Any additional keyword arguments passed to ``__init__`` become
        top-level fields in the serialized config alongside
        ``function_name`` and ``data``. Useful for attaching metadata
        the source handler inspects (priority, sensitivity, campus, ...).

    Example:
        ```python
        # Plain dict
        TaskInput(function_name="predict", data={"text": "hello"})

        # Pydantic model
        from pydantic import BaseModel
        class Req(BaseModel):
            text: str
            top_k: int = 1
        TaskInput(function_name="predict", data=Req(text="hi", top_k=5))

        # Extras
        TaskInput(
            function_name="predict",
            data={"text": "hi"},
            priority="high",
            sensitivity="low",
        ).to_dict()
        # {'function_name': 'predict', 'data': {'text': 'hi'},
        #  'priority': 'high', 'sensitivity': 'low'}
        ```
    """

    function_name: str
    data: BaseModel | dict[str, Any]
    _extra: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        function_name: str,
        data: BaseModel | dict[str, Any],
        **kwargs: Any,
    ) -> None:
        self.function_name = function_name
        self.data = data
        self._extra = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-ready dict representation.

        ``data`` is dumped via ``model_dump()`` if it's a Pydantic model,
        otherwise passed through as-is. Extra kwargs are merged at the
        top level.
        """
        result: dict[str, Any] = {
            "function_name": self.function_name,
            "data": (self.data.model_dump() if isinstance(self.data, BaseModel) else self.data),
        }
        result.update(self._extra)
        return result


@dataclass
class SourceInfo:
    """User-facing source builder.

    Construct one of these, then pass it to ``client.publish_source``.
    The client wrapper handles uploading the metadata to IPFS and
    building the final ``SourceParams`` tuple — this dataclass is a
    pure data container with no side effects.

    Attributes:
        name: Human-readable source name.
        description: Short description of what the source does.
        logoUrl: URL to a logo image (any HTTP-fetchable location).
        imageEnvs: Docker-compose URLs per hardware environment.
        minPayment: Minimum wei a task must offer to be publishable
            against this source.
        minAvailableLockup: Minimum vault lockup a provider must hold
            to register to this source.
        maxExpiryDuration: Maximum seconds a task against this source
            can live before expiring.
        deliveryMethod: How winning responses get confirmed — either
            ``MANUAL_CONFIRMATION`` (client explicitly confirms) or
            ``FIRST_RESPONSE`` (automatic on first submit).

    Example:
        ```python
        from web3 import Web3
        from ogpu.client import SourceInfo, ImageEnvironments, DeliveryMethod
        info = SourceInfo(
            name="sentiment-analyzer",
            description="DistilBERT classifier",
            logoUrl="https://example.com/logo.png",
            imageEnvs=ImageEnvironments(cpu="https://.../compose.yml"),
            minPayment=Web3.to_wei(0.01, "ether"),
            minAvailableLockup=Web3.to_wei(0.5, "ether"),
            maxExpiryDuration=86400,
            deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
        )
        ```
    """

    name: str
    description: str
    logoUrl: str
    imageEnvs: ImageEnvironments
    minPayment: int
    minAvailableLockup: int
    maxExpiryDuration: int
    deliveryMethod: DeliveryMethod = DeliveryMethod.MANUAL_CONFIRMATION


@dataclass
class TaskInfo:
    """User-facing task builder.

    Construct one of these, then pass it to ``client.publish_task``.
    The client wrapper uploads ``config`` to IPFS and builds the
    final ``TaskParams`` tuple — this dataclass is pure data.

    Attributes:
        source: Source contract address the task targets.
        config: ``TaskInput`` holding the function name + data + extras.
        expiryTime: Unix timestamp after which the task expires and
            cannot be attempted. Must be less than
            ``now + source.maxExpiryDuration``.
        payment: Amount in wei to pay the winning provider. Must be
            at least ``source.minPayment``.

    Example:
        ```python
        import time
        from web3 import Web3
        from ogpu.client import TaskInfo, TaskInput
        info = TaskInfo(
            source="0xSOURCE",
            config=TaskInput(function_name="predict", data={"text": "hi"}),
            expiryTime=int(time.time()) + 3600,
            payment=Web3.to_wei(0.01, "ether"),
        )
        ```
    """

    source: str
    config: TaskInput
    expiryTime: int
    payment: int


# ---------------------------------------------------------------------------
# Snapshot dataclasses — frozen captures returned by Instance.snapshot()
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceSnapshot:
    """Frozen batch capture of a source's on-chain state.

    Returned by ``Source.snapshot()``. Each field is fetched via one
    RPC call during the snapshot; after that, reading fields on the
    snapshot costs nothing — it's just a dataclass.

    Does not include paginated fields (``tasks``, ``registrants``) or
    IPFS-fetching fields (``metadata``). Call those methods on the
    ``Source`` instance directly when you need them.

    Attributes:
        address: Source contract address.
        client: Owner of the source.
        status: Current ``SourceStatus``.
        params: Full ``SourceParams`` tuple from the contract.
        task_count: Total number of tasks ever published against this source.
        registrant_count: Total number of registered providers.
    """

    address: str
    client: str
    status: SourceStatus
    params: SourceParams
    task_count: int
    registrant_count: int


@dataclass(frozen=True)
class TaskSnapshot:
    """Frozen batch capture of a task's on-chain state.

    Returned by ``Task.snapshot()``. See ``SourceSnapshot`` for the
    general pattern — pagination-heavy fields like ``attempters`` and
    ``responses`` are omitted.

    Attributes:
        address: Task contract address.
        source: Source contract address this task was published to.
        status: Current ``TaskStatus``.
        params: Full ``TaskParams`` tuple from the contract.
        payment: Payment in wei.
        expiry_time: Unix timestamp after which the task expires.
        delivery_method: ``DeliveryMethod`` for response confirmation.
        attempt_count: Number of attempts submitted so far.
        winning_provider: Address of the provider whose response was
            confirmed, or None if not yet finalized.
    """

    address: str
    source: str
    status: TaskStatus
    params: TaskParams
    payment: int
    expiry_time: int
    delivery_method: DeliveryMethod
    attempt_count: int
    winning_provider: str | None


@dataclass(frozen=True)
class ResponseSnapshot:
    """Frozen batch capture of a response's on-chain state.

    Returned by ``Response.snapshot()``.

    Attributes:
        address: Response contract address.
        task: Task contract address this response is for.
        params: Full ``ResponseParams`` tuple.
        data: Raw data URL from the params.
        status: Current ``ResponseStatus``.
        timestamp: Unix timestamp when the response was submitted.
        confirmed: Whether this response has been confirmed.
    """

    address: str
    task: str
    params: ResponseParams
    data: str
    status: ResponseStatus
    timestamp: int
    confirmed: bool


@dataclass(frozen=True)
class ProviderSnapshot:
    """Frozen batch capture of a provider's state across Terminal + Vault.

    Returned by ``Provider.snapshot()``. Composes reads from the Terminal
    (pairing, base/live data) and Vault (balance, lockup, earnings,
    eligibility).

    Does not include ``get_registered_sources()`` — that's a paginated
    Nexus read; call it explicitly.

    Attributes:
        address: Provider address.
        master: Address of the master this provider is paired with.
        base_data: Long-lived provider metadata URL (base data).
        live_data: Short-lived provider status URL (live data).
        is_provider: Whether the address is registered as a provider.
        default_agent_disabled: Whether the default agent delegation
            is disabled for this provider.
        balance: Available vault balance in wei.
        lockup: Locked (staked) amount in wei.
        unbonding: Amount currently in the unbonding phase.
        unbonding_timestamp: When the unbonding matures.
        total_earnings: Cumulative earnings across all completed tasks.
        frozen_payment: Amount escrowed against pending attempts.
        sanction: Sanction amount if any.
        is_eligible: Whether the provider is eligible for new tasks.
        is_whitelisted: Whether the provider is on the vault whitelist.
    """

    address: str
    master: str
    base_data: str
    live_data: str
    is_provider: bool
    default_agent_disabled: bool
    balance: int
    lockup: int
    unbonding: int
    unbonding_timestamp: int
    total_earnings: int
    frozen_payment: int
    sanction: int
    is_eligible: bool
    is_whitelisted: bool


@dataclass(frozen=True)
class MasterSnapshot:
    """Frozen batch capture of a master's state across Terminal + Vault.

    Returned by ``Master.snapshot()``. Lighter than ``ProviderSnapshot``
    because masters have a smaller surface — no base/live data, no
    sanction/unbonding timestamps tracked.

    Attributes:
        address: Master address.
        provider: Address of the provider this master is paired with.
        is_master: Whether the address is registered as a master.
        balance: Available vault balance in wei.
        lockup: Locked amount in wei.
        unbonding: Amount currently in the unbonding phase.
        total_earnings: Cumulative earnings.
        frozen_payment: Amount escrowed against pending task work.
        is_eligible: Whether the master is eligible to manage providers.
        is_whitelisted: Whether the master is on the vault whitelist.
    """

    address: str
    provider: str
    is_master: bool
    balance: int
    lockup: int
    unbonding: int
    total_earnings: int
    frozen_payment: int
    is_eligible: bool
    is_whitelisted: bool
