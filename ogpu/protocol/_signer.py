"""Signer resolution — bridges ``signer=`` parameters and env-var fallbacks.

Every write operation in ``ogpu.protocol`` accepts a ``signer`` argument. When
omitted, ``resolve_signer(signer=None, role=...)`` looks up the matching
``*_PRIVATE_KEY`` environment variable (one per role). Vault operations pass
``role=None``, which disables the env-var fallback per decision C1-vault —
the user must pass ``signer=`` explicitly or get a ``MissingSignerError``.
"""

from __future__ import annotations

import os
from typing import cast

from eth_account import Account
from eth_account.signers.local import LocalAccount

from ..types.enums import Role
from ..types.errors import InvalidSignerError, MissingSignerError

Signer = str | LocalAccount


def resolve_signer(
    signer: Signer | None,
    role: Role | None = None,
) -> LocalAccount:
    """Turn a ``signer`` argument (or env-var fallback) into a ``LocalAccount``.

    - If ``signer`` is a ``LocalAccount``, it is returned unchanged.
    - If ``signer`` is a hex string, it is parsed via ``Account.from_key``.
    - If ``signer`` is ``None`` and ``role`` is provided, the matching
      ``<ROLE>_PRIVATE_KEY`` environment variable is consulted.
    - If ``signer`` is ``None`` and ``role`` is ``None`` (vault), or the env
      var is unset, ``MissingSignerError`` is raised.
    """
    if isinstance(signer, LocalAccount):
        return signer

    if isinstance(signer, str):
        try:
            return cast(LocalAccount, Account.from_key(signer))
        except Exception as exc:
            raise InvalidSignerError(reason=str(exc)) from exc

    if signer is not None:
        raise InvalidSignerError(reason=f"Unsupported signer type: {type(signer).__name__}")

    if role is None:
        raise MissingSignerError(role=None)

    env_var = f"{role.value.upper()}_PRIVATE_KEY"
    key = os.getenv(env_var)
    if not key:
        raise MissingSignerError(role=role)

    try:
        return cast(LocalAccount, Account.from_key(key))
    except Exception as exc:
        raise InvalidSignerError(
            reason=f"Environment variable {env_var} is not a valid private key: {exc}"
        ) from exc
