import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .environment import Environment, combine_environments
from .utils import publish_to_ipfs


class DeliveryMethod(Enum):
    """Enum for delivery method options."""

    MANUAL_CONFIRMATION = 0  # client manually confirms the response
    FIRST_RESPONSE = 1  # first provider to submit a response wins


class SourceParams(BaseModel):
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

    def to_tuple(self):
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
    source: str
    config: str
    expiryTime: int
    payment: int

    def to_tuple(self):
        return (
            self.source,
            self.config,
            self.expiryTime,
            self.payment,
        )


@dataclass
class ImageMetadata:
    """Image metadata structure for task sources."""

    cpu: str
    nvidia: str
    amd: str
    name: str
    description: str
    logoUrl: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "cpu": self.cpu,
            "nvidia": self.nvidia,
            "amd": self.amd,
            "name": self.name,
            "description": self.description,
            "logoUrl": self.logoUrl,
        }


@dataclass
class ImageEnvironments:
    """Docker compose file paths for different environments."""

    cpu: str = ""
    nvidia: str = ""
    amd: str = ""


@dataclass
class SourceInfo:
    """User-friendly source information structure."""

    name: str
    description: str
    logoUrl: str
    imageEnvs: ImageEnvironments
    minPayment: int  # in wei
    minAvailableLockup: int  # in wei
    maxExpiryDuration: int  # in seconds
    deliveryMethod: DeliveryMethod = DeliveryMethod.MANUAL_CONFIRMATION

    def to_source_params(self, client_address: str) -> SourceParams:
        """Convert to SourceParams for internal use."""

        # Create ImageMetadata from SourceInfo
        image_metadata = ImageMetadata(
            cpu=self.imageEnvs.cpu,
            nvidia=self.imageEnvs.nvidia,
            amd=self.imageEnvs.amd,
            name=self.name,
            description=self.description,
            logoUrl=self.logoUrl,
        )

        # Publish image metadata to IPFS
        metadata_url = publish_to_ipfs(
            image_metadata.to_dict(), "imageMetadata.json", "application/json"
        )

        # Map ImageEnvironments fields to Environment enum values
        environments = []
        if self.imageEnvs.cpu:
            environments.append(Environment.CPU)
        if self.imageEnvs.nvidia:
            environments.append(Environment.NVIDIA)
        if self.imageEnvs.amd:
            environments.append(Environment.AMD)

        # Combine environments (at least one is guaranteed to be provided)
        combined_envs = combine_environments(*environments)

        return SourceParams(
            client=client_address,
            imageMetadataUrl=metadata_url,
            imageEnvironments=combined_envs,
            minPayment=self.minPayment,
            minAvailableLockup=self.minAvailableLockup,
            maxExpiryDuration=self.maxExpiryDuration,
            ## Default values for optional parameters
            privacyEnabled=False,
            optionalParamsUrl="",
            deliveryMethod=self.deliveryMethod.value,
            lastUpdateTime=int(time.time()),
        )


@dataclass
class TaskInput:
    """Configuration structure for tasks."""

    function_name: str
    data: BaseModel | dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "function_name": self.function_name,
            "data": (
                self.data.model_dump()
                if isinstance(self.data, BaseModel)
                else self.data
            ),
        }


@dataclass
class TaskInfo:
    """User-friendly task information structure."""

    source: str
    config: TaskInput
    expiryTime: int
    payment: int

    def to_task_params(self) -> TaskParams:
        """Convert to TaskParams for internal use."""
        # Publish task config to IPFS
        config_url = publish_to_ipfs(
            self.config.to_dict(), "taskConfig.json", "application/json"
        )

        return TaskParams(
            source=self.source,
            config=config_url,
            expiryTime=self.expiryTime,
            payment=self.payment,
        )


@dataclass
class Response:
    """Response data structure for task responses."""

    address: str
    task: str
    provider: str
    data: str
    payment: int
    status: int
    timestamp: int
    confirmed: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "address": self.address,
            "task": self.task,
            "provider": self.provider,
            "data": self.data,
            "payment": self.payment,
            "status": self.status,
            "timestamp": self.timestamp,
            "confirmed": self.confirmed,
        }


@dataclass
class ConfirmedResponse:
    """Simplified confirmed response data structure."""

    address: str
    data: str

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "address": self.address,
            "data": self.data,
        }
