import time
from typing import Any

from pydantic import BaseModel


class SourceParams(BaseModel):
    clientAddress: str
    imageMetadataUrl: str
    imageEnvironments: bytes
    minPayment: int
    minAvailableLockup: int
    maxExpiryTime: int
    privacyEnabled: bool
    optionalParamsUrl: str
    deliveryMethod: int
    lastUpdateTime: int = int(time.time())

    def to_tuple(self):
        return (
            self.clientAddress,
            self.imageMetadataUrl,
            self.imageEnvironments,
            self.minPayment,
            self.minAvailableLockup,
            self.maxExpiryTime,
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
