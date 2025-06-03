import logging
import os

import sentry_sdk
from colorama import Fore, Style, init

from . import config

init(autoreset=True)

logger = logging.getLogger("ogpu")


if not logger.hasHandlers():
    handler = logging.StreamHandler()

    class PartyFormatter(logging.Formatter):
        """
        Custom formatter that colors log messages by level.
        """

        def format(self, record):
            themes = {
                "DEBUG": (Fore.BLUE, "DEBUG"),
                "INFO": (Fore.GREEN, "INFO "),
                "SUCCESS": (Fore.CYAN, "✅ SUCCESS"),
                "WARNING": (Fore.YELLOW, "WARNING"),
                "ERROR": (Fore.RED, "ERROR"),
                "FAIL": (Fore.RED, "❌ FAIL"),
                "TIMEOUT": (Fore.LIGHTMAGENTA_EX, "⏱️  TIMEOUT"),
                "CRITICAL": (Fore.MAGENTA, "CRITICAL"),
            }
            color, label = themes.get(record.levelname, ("", record.levelname))
            record.levelname = f"{color}{label}{Style.RESET_ALL}"
            return super().format(record)

    formatter = PartyFormatter(
        fmt="[{asctime}] {levelname:<20} {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

# Define custom log levels
SUCCESS_LEVEL = 25
TIMEOUT_LEVEL = 35
FAIL_LEVEL = 45

logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
logging.addLevelName(FAIL_LEVEL, "FAIL")
logging.addLevelName(TIMEOUT_LEVEL, "TIMEOUT")


def task_success(self, message, *args, **kwargs):
    """Custom log level for successful operations."""
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


def task_fail(self, message, *args, **kwargs):
    """Custom log level for failed operations."""
    if self.isEnabledFor(FAIL_LEVEL):
        self._log(FAIL_LEVEL, message, args, **kwargs)
        if config.SENTRY_DSN:
            try:
                sentry_sdk.capture_message(str(message), level="error")
            except Exception:
                pass


def task_timeout(self, message, *args, **kwargs):
    """Custom log level for timeout situations."""
    if self.isEnabledFor(TIMEOUT_LEVEL):
        self._log(TIMEOUT_LEVEL, message, args, **kwargs)
        if config.SENTRY_DSN:
            try:
                sentry_sdk.capture_message(str(message), level="warning")
            except Exception:
                pass


# Add custom levels to Logger
setattr(logging.Logger, "task_success", task_success)
setattr(logging.Logger, "task_fail", task_fail)
setattr(logging.Logger, "task_timeout", task_timeout)


if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=os.getenv("OGPU_SERVICE_ENV", "production"),
        release="0.0.1",
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("source_address", config.SOURCE_ADDRESS)

    logger.info("Sentry logging enabled.")
