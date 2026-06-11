"""
Basic imports for registering, serving, and logging user-defined functions.
"""

_OPTIONAL_DEPS = ("fastapi", "uvicorn", "sentry_sdk", "colorama")

try:
    from .decorators import expose, init  # Function registration decorators
    from .logger import logger  # Logging interface
    from .server import start  # Server launcher
except ImportError as exc:
    # Only translate "the [service] extra isn't installed" — any other
    # ImportError (version incompatibility, a broken module) must
    # surface as-is, or the user gets told to install something they
    # already have.
    missing = exc.name or ""
    if missing.split(".")[0] in _OPTIONAL_DEPS:
        raise ImportError(
            "ogpu.service requires optional dependencies that are not installed. "
            'Install them with: pip install "ogpu[service]"'
        ) from exc
    raise
