"""Signer resolution — bridges ``signer=`` parameters and env-var fallbacks.

Every write operation in ``ogpu.protocol`` accepts a ``signer`` keyword
argument that can be a hex private key string, an ``eth_account.LocalAccount``,
or ``None``. When ``None``, ``resolve_signer`` falls back to the role-specific
``*_PRIVATE_KEY`` environment variable (``CLIENT_PRIVATE_KEY``,
``PROVIDER_PRIVATE_KEY``, ``MASTER_PRIVATE_KEY``, ``AGENT_PRIVATE_KEY``).

Vault operations deliberately pass ``role=None`` to disable env-var fallback —
the user must pass ``signer=`` explicitly or get a ``MissingSignerError``. This
prevents accidentally depositing or withdrawing from the wrong account when
multiple roles share the same process.
"""

from __future__ import annotations

import os
from typing import cast

from eth_account import Account
from eth_account.signers.local import LocalAccount

from ..types.enums import Role
from ..types.errors import InvalidSignerError, MissingSignerError

#: Accepted types for the ``signer=`` parameter on every write operation.
#: A hex private key string is parsed via ``eth_account.Account.from_key``;
#: a ``LocalAccount`` is passed through unchanged. This gives forward
#: compatibility with hardware wallets, KMS providers, and Fireblocks-style
#: signer classes that implement the ``LocalAccount`` interface.
Signer = str | LocalAccount


def resolve_signer(
    signer: Signer | None,
    role: Role | None = None,
) -> LocalAccount:
    """Normalize a ``signer`` argument to a ``LocalAccount``.

    The entry point every write operation in the SDK uses to turn a
    user-provided signer into a concrete account the transaction layer
    can sign with. Handles three cases:

    1. **Already a ``LocalAccount``** — returned unchanged. This is the
       path hardware wallets, KMS, and other external signer backends
       take: construct a ``LocalAccount``-shaped object once, pass it
       in as ``signer=``.
    2. **Hex string** — parsed via ``Account.from_key``. Most common path.
    3. **``None``** — fall back to the role-specific env var. If
       ``role`` is also ``None`` (vault operations), raise
       ``MissingSignerError`` immediately.

    Args:
        signer: The user-provided signer, or ``None`` to trigger the
            env-var fallback.
        role: Which role the operation is acting as — controls which
            env var to read when ``signer`` is ``None``. Pass ``None``
            to disable the fallback entirely (vault convention).

    Returns:
        A ``LocalAccount`` ready to sign transactions.

    Raises:
        MissingSignerError: If ``signer`` is ``None`` and either no
            ``role`` is set or the role's env var is unset.
        InvalidSignerError: If ``signer`` is a string that isn't a
            valid private key, or a type the resolver doesn't know
            how to handle, or the env var contains an invalid key.

    Example:
        ```python
        import os
        from eth_account import Account
        from ogpu.protocol._signer import resolve_signer
        from ogpu.types import Role

        # Explicit hex string
        acc = resolve_signer("0x" + "11" * 32, role=Role.CLIENT)
        print(acc.address)
        # '0x...'

        # Pre-built LocalAccount (e.g. from a hardware wallet)
        local = Account.from_key("0x" + "11" * 32)
        resolve_signer(local, role=Role.CLIENT) is local
        # True

        # Env var fallback — reads CLIENT_PRIVATE_KEY
        os.environ["CLIENT_PRIVATE_KEY"] = "0x" + "11" * 32
        acc = resolve_signer(None, role=Role.CLIENT)

        # Vault-style: no fallback allowed
        resolve_signer(None, role=None)  # raises MissingSignerError
        ```
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
