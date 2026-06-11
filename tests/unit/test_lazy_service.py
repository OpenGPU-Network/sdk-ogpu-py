"""``ogpu.service`` deps are optional — core import must not require them."""

import subprocess
import sys

import pytest

# Runs in a subprocess with the service-only deps (fastapi, uvicorn,
# sentry_sdk, colorama) blocked at the import level, simulating an
# install without the ``ogpu[service]`` extra.
_BLOCKED_ENV_SCRIPT = """
import sys

class Blocker:
    BLOCKED = {"fastapi", "uvicorn", "sentry_sdk", "colorama"}

    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in self.BLOCKED:
            # name= matters: the real import system sets it, and
            # ogpu/service/__init__.py branches on exc.name
            raise ModuleNotFoundError(f"No module named {name!r} (simulated)", name=name)

sys.meta_path.insert(0, Blocker())

import ogpu

assert ogpu.client.publish_task is not None

# star-import must also work without the extra — "service" must not be
# in __all__, or this getattr's it and explodes
ns = {}
exec("from ogpu import *", ns)
assert "client" in ns and "service" not in ns

try:
    ogpu.service
except ImportError as exc:
    assert "ogpu[service]" in str(exc), str(exc)
else:
    raise SystemExit("expected ImportError when accessing ogpu.service")
"""


def test_import_ogpu_without_service_deps():
    result = subprocess.run(
        [sys.executable, "-c", _BLOCKED_ENV_SCRIPT],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_service_accessible_when_deps_installed():
    pytest.importorskip("fastapi", reason="requires the ogpu[service] extra")
    import ogpu

    assert ogpu.service.start is not None
    assert ogpu.service.expose is not None
