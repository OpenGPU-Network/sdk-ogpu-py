"""Metadata and on-chain struct types.

This module consolidates:
- ``SourceMetadata`` (renamed from ``ImageMetadata``) and ``ImageEnvironments``
- ``SourceParams`` / ``TaskParams`` / ``ResponseParams`` — typed mirrors of the
  Solidity structs passed to and returned from the contracts
- ``SourceInfo`` / ``TaskInfo`` — user-facing builders that upload metadata to
  IPFS and produce the corresponding ``*Params`` objects
- ``TaskInput`` — operational payload for a task (function name + data + extras)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .enums import DeliveryMethod, ResponseStatus, SourceStatus, TaskStatus


@dataclass
class ImageEnvironments:
    """Docker compose URLs for each supported execution environment."""

    cpu: str = ""
    nvidia: str = ""
    amd: str = ""


@dataclass
class SourceMetadata:
    """Off-chain metadata for a Source.

    Formerly named ``ImageMetadata``. Describes the full source package —
    docker-compose URLs per environment plus display fields — and is what
    gets uploaded to IPFS before ``Nexus.publishSource`` is called.
    """

    cpu: str
    nvidia: str
    amd: str
    name: str
    description: str
    logoUrl: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu": self.cpu,
            "nvidia": self.nvidia,
            "amd": self.amd,
            "name": self.name,
            "description": self.description,
            "logoUrl": self.logoUrl,
        }


class SourceParams(BaseModel):
    """Typed mirror of the Solidity ``Nexus.publishSource`` input tuple."""

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
    """Typed mirror of the Solidity ``Controller.publishTask`` input tuple."""

    source: str
    config: str
    expiryTime: int
    payment: int

    def to_tuple(self) -> tuple[str, str, int, int]:
        return (self.source, self.config, self.expiryTime, self.payment)


@dataclass(frozen=True)
class ResponseParams:
    """Typed mirror of what ``Response.getResponseParams()`` returns on-chain."""

    task: str
    provider: str
    data: str
    payment: int


@dataclass
class TaskInput:
    """Operational input for a task — function name + data payload + extras.

    Name intentionally diverges from ``SourceMetadata`` because the semantics
    differ: a task's payload is an *input* to invoke a function, not a metadata
    descriptor of a deployed artifact.
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
        result: dict[str, Any] = {
            "function_name": self.function_name,
            "data": (self.data.model_dump() if isinstance(self.data, BaseModel) else self.data),
        }
        result.update(self._extra)
        return result


@dataclass
class SourceInfo:
    """User-facing source builder — pure data container.

    The client layer uploads ``imageEnvs`` + display fields to IPFS and
    assembles the final ``SourceParams`` before calling the contract. This
    type has no side effects — construct, read, pass along.
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
    """User-facing task builder — pure data container.

    The client layer uploads ``config`` to IPFS and assembles the final
    ``TaskParams`` before calling the contract. This type has no side effects.
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
    address: str
    client: str
    status: SourceStatus
    params: SourceParams
    task_count: int
    registrant_count: int


@dataclass(frozen=True)
class TaskSnapshot:
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
    address: str
    task: str
    params: ResponseParams
    data: str
    status: ResponseStatus
    timestamp: int
    confirmed: bool


@dataclass(frozen=True)
class ProviderSnapshot:
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
