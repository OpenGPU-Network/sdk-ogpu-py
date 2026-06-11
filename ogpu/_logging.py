"""SDK-wide logging setup and the ``set_verbose`` convenience switch.

The SDK logs through the standard :mod:`logging` module under the
``ogpu`` namespace (``ogpu.ipfs``, ``ogpu.tx``, ...). By default a
``NullHandler`` is attached and nothing is emitted — users with their
own logging configuration control SDK output the usual way::

    logging.getLogger("ogpu").setLevel(logging.DEBUG)

For everyone else, ``ogpu.set_verbose()`` attaches a ready-made stderr
handler with millisecond timestamps, so stage durations (IPFS pin vs
RPC receipt wait) can be read directly off the log. Setting the
``OGPU_VERBOSE`` environment variable (``1`` / ``true`` / ``yes``) does
the same at import time — useful in deployed environments where editing
code isn't an option.
"""

from __future__ import annotations

import logging
import os
import sys

_root = logging.getLogger("ogpu")
_root.addHandler(logging.NullHandler())

#: Handler installed by ``set_verbose`` — tracked so repeated calls
#: don't stack duplicate handlers and ``set_verbose(False)`` can undo.
_verbose_handler: logging.Handler | None = None

# Millisecond resolution matters here: a 0.4s IPFS pin is invisible at
# whole-second timestamps.
_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)s — %(message)s"
_DATEFMT = "%H:%M:%S"


def set_verbose(enabled: bool = True, level: int = logging.DEBUG) -> None:
    """Toggle verbose SDK logging on stderr.

    Attaches a timestamped stderr handler to the ``ogpu`` logger and
    sets its level, so every network stage (IPFS upload, transaction
    build/send, receipt wait) reports what it's doing and how long it
    took. Calling it twice doesn't duplicate output; ``set_verbose(False)``
    removes the handler again.

    This only manages the SDK's own convenience handler. If you already
    configure :mod:`logging` yourself, don't use this — set the level of
    the ``"ogpu"`` logger in your own configuration instead.

    Args:
        enabled: ``True`` to attach the handler, ``False`` to remove it.
        level: Log level for the ``ogpu`` logger while enabled.
            Defaults to ``logging.DEBUG`` (all stage timings). Use
            ``logging.INFO`` for milestones only.

    Example:
        ```python
        import ogpu

        ogpu.set_verbose()
        task = ogpu.client.publish_task(info)
        # 14:02:11.482 DEBUG   ogpu.ipfs — publishing taskConfig.json (312 bytes) to IPFS...
        # 14:02:11.901 INFO    ogpu.ipfs — IPFS pin ok in 0.4s → https://cipfs.ogpuscan.io/ipfs/Qm...
        # 14:02:12.110 DEBUG   ogpu.tx — [Controller.publishTask] tx 0xabc... sent in 0.2s (nonce=42)
        # 14:02:15.214 INFO    ogpu.tx — [Controller.publishTask] mined in block 18203 — receipt wait 3.1s, total 3.5s
        ogpu.set_verbose(False)
        ```
    """
    global _verbose_handler

    if enabled:
        if _verbose_handler is None:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
            _root.addHandler(handler)
            _verbose_handler = handler
        _root.setLevel(level)
    else:
        if _verbose_handler is not None:
            _root.removeHandler(_verbose_handler)
            _verbose_handler = None
            # Only undo the level we set ourselves — if verbose was never
            # on, the user may have configured this level manually.
            _root.setLevel(logging.NOTSET)


def _apply_env_verbose() -> None:
    """Enable verbose logging if ``OGPU_VERBOSE`` is set in the environment.

    Called once from ``ogpu/__init__`` after dotenv loading, so the
    variable works from a ``.env`` file too.
    """
    if os.getenv("OGPU_VERBOSE", "").strip().lower() in ("1", "true", "yes"):
        set_verbose()
