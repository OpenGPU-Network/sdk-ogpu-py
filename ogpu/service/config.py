import os
from importlib.metadata import version

SDK_VERSION = version("ogpu")

SENTRY_DSN = os.getenv("OGPU_SDK_SENTRY_DSN")

PROTOCOL_VERSION = os.getenv("PROTOCOL_VERSION")

SOURCE_ADDRESS = os.getenv("SOURCE_ADDRESS", "0xundefined")
PROVIDER_ADDRESS = os.getenv("PROVIDER_ADDRESS", "0xundefined")
CALLBACK_URL = os.getenv("CALLBACK_URL")


SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 5555
