import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .environment import Environment, combine_environments
from .utils import publish_to_ipfs


class DeliveryMethod(Enum):
    """Enum for delivery method options.

    Attributes:
        MANUAL_CONFIRMATION: Client manually confirms the response
        FIRST_RESPONSE: First provider to submit a response wins
    """

    MANUAL_CONFIRMATION = 0  # client manually confirms the response
    FIRST_RESPONSE = 1  # first provider to submit a response wins


class SourceParams(BaseModel):
    """Source parameters for blockchain interaction.

    Attributes:
        client: Address of the client publishing the source
        imageMetadataUrl: URL to the image metadata JSON file
        imageEnvironments: Bitmask of supported environments
        minPayment: Minimum payment required in wei
        minAvailableLockup: Minimum lockup amount in wei
        maxExpiryDuration: Maximum task duration in seconds
        privacyEnabled: Whether privacy features are enabled
        optionalParamsUrl: URL to optional parameters
        deliveryMethod: Response delivery method (enum value)
        lastUpdateTime: Unix timestamp of last update
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
    """Task parameters for blockchain interaction.

    Attributes:
        source: Address of the source to run the task on
        config: URL to the task configuration JSON file
        expiryTime: Unix timestamp when task expires
        payment: Payment amount for the task in wei
    """

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
    """Image metadata structure for task sources.

    Attributes:
        cpu: URL to CPU-only docker-compose.yml file
        nvidia: URL to NVIDIA GPU docker-compose.yml file
        amd: URL to AMD GPU docker-compose.yml file
        name: Human-readable name for the source
        description: Description of the AI service
        logoUrl: URL to the source logo image
    """

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
    """Docker compose file paths for different environments.

    Attributes:
        cpu: URL to CPU-only docker-compose.yml file
        nvidia: URL to NVIDIA GPU docker-compose.yml file
        amd: URL to AMD GPU docker-compose.yml file
    """

    cpu: str = ""
    nvidia: str = ""
    amd: str = ""


@dataclass
class SourceInfo:
    """User-friendly source information structure.

    Attributes:
        name: Human-readable name for the source
        description: Description of the AI service
        logoUrl: URL to the source logo image
        imageEnvs: Docker environment configurations
        minPayment: Minimum payment required in wei
        minAvailableLockup: Minimum lockup amount in wei
        maxExpiryDuration: Maximum task duration in seconds
        deliveryMethod: How responses are delivered
    """

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
    """Configuration structure for tasks.

    Attributes:
        function_name: Name of the function to call on the source
        data: Input data for the function (Pydantic model or dictionary)
    """

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
    """User-friendly task information structure.

    Attributes:
        source: Address of the source to run the task on
        config: Task input configuration and function call
        expiryTime: Unix timestamp when task expires
        payment: Payment amount for the task in wei
    """

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
    """Response data structure for task responses.

    Attributes:
        address: Blockchain address of the response
        task: Address of the task this responds to
        provider: Address of the provider who submitted the response
        data: Response data from the AI service
        payment: Payment amount in wei
        status: Response status code
        timestamp: Unix timestamp when response was submitted
        confirmed: Whether the response has been confirmed
    """

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
    """Simplified confirmed response data structure.

    Attributes:
        address: Blockchain address of the confirmed response
        data: The confirmed response data
    """

    address: str
    data: str

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "address": self.address,
            "data": self.data,
        }
