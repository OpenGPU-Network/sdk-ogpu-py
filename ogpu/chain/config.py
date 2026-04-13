"""Chain selection, contract addresses, RPC URLs, and ABI loading.

``ChainConfig`` is the central knob for everything network-related: which
chain to talk to, which contracts to call on that chain, which RPC node to
use, and which ABIs to load. It's a process-wide global with classmethod
accessors — you don't instantiate it.

Default chain is ``OGPU_MAINNET``. Call ``ChainConfig.set_chain(ChainId.OGPU_TESTNET)``
to switch. Every SDK module that talks to the chain reads the current
chain from ``ChainConfig`` transparently.
"""

from __future__ import annotations

import json
import os
from enum import Enum

from web3 import Web3

from ..types.errors import ChainNotSupportedError, InvalidRpcUrlError


class ChainId(Enum):
    """Supported OGPU networks.

    The enum value is the actual ``chainId`` used in EIP-155 transaction
    signing. Used as a key in ``ChainConfig.CHAIN_CONTRACTS`` and
    ``CHAIN_RPC_URLS`` to look up network-specific configuration.

    Members:
        OGPU_MAINNET: Production OGPU chain (chainId 1071).
        OGPU_TESTNET: Test OGPU chain (chainId 200820172034).
    """

    OGPU_MAINNET = 1071
    OGPU_TESTNET = 200820172034


#: RPC URL per chain. Mutable — ``Web3Manager.update_rpc_url`` rewrites the
#: entry when a user calls ``ChainConfig.set_rpc(url)``, so this module-level
#: dict stays in sync with whatever the latest override is.
CHAIN_RPC_URLS: dict[ChainId, str] = {
    ChainId.OGPU_MAINNET: "https://mainnet-rpc.ogpuscan.io",
    ChainId.OGPU_TESTNET: "https://testnetrpc.ogpuscan.io",
}


class ChainConfig:
    """Process-wide chain configuration.

    Everything is a classmethod — you call ``ChainConfig.set_chain(...)``
    or ``ChainConfig.get_rpc()`` without instantiating. State is stored
    on the class itself, so it's shared across the entire process.

    The class holds:

    - **``CHAIN_CONTRACTS``** — the mapping from ``ChainId`` to
      ``{contract_name: address}`` for every singleton contract
      (NEXUS, CONTROLLER, TERMINAL, VAULT).
    - **``CHAIN_DIRECTORIES``** — subdirectory name under ``chain/abis/``
      where per-chain ABI files live.
    - **``_current_chain``** — which chain is globally active.
    - **``_loaded_abis``** — cache of parsed ABI dicts per chain.

    Thread-safe for read-heavy workloads (most of the state is write-once
    or set at startup). If you swap chains at runtime from multiple
    threads, serialize the swap yourself.
    """

    CHAIN_CONTRACTS: dict[ChainId, dict[str, str]] = {
        ChainId.OGPU_TESTNET: {
            "NEXUS": "0xF87bb2f3edB991a998992f14d35fE142e6Bb50b1",
            "CONTROLLER": "0x9fb6022074Fd7Bdb429de0776eb693cA0CB55E09",
            "TERMINAL": "0x1ea332Fc14a5AFD3AF3852B45C263Ab5b1Dd6f52",
            "VAULT": "0x15905a2FbD3EF5d3532b931b5656BB9EB493Bb15",
        },
        ChainId.OGPU_MAINNET: {
            "NEXUS": "0x2b0cC6058313801D5feb184a539e3a0C5A87a6a1",
            "CONTROLLER": "0x8661F4B9c30e07A04d795A192478dfD905625a1D",
            "TERMINAL": "0xaEBC7b712D38Fc4d841f0732c21B8774339869D3",
            "VAULT": "0xa5c582254AA313528898311362bc698b041580cC",
        },
    }

    CHAIN_DIRECTORIES: dict[ChainId, str] = {
        ChainId.OGPU_TESTNET: "testnet",
        ChainId.OGPU_MAINNET: "mainnet",
    }

    _DEFAULT_RPC_URLS: dict[ChainId, str] = {
        ChainId.OGPU_MAINNET: "https://mainnet-rpc.ogpuscan.io",
        ChainId.OGPU_TESTNET: "https://testnetrpc.ogpuscan.io",
    }

    _current_chain: ChainId | None = ChainId.OGPU_MAINNET
    _loaded_abis: dict[ChainId, dict[str, object]] = {}

    # ------------------------------------------------------------------ #
    # Chain selection
    # ------------------------------------------------------------------ #

    @classmethod
    def set_chain(cls, chain_id: ChainId) -> None:
        """Switch the globally-active chain.

        Every subsequent SDK call resolves contracts, RPC, and ABIs
        against this chain. Typically called once at program startup.

        Args:
            chain_id: The target chain.

        Raises:
            ChainNotSupportedError: If the given chain is not in
                ``CHAIN_CONTRACTS``.

        Example:
            ```python
            from ogpu import ChainConfig, ChainId
            ChainConfig.set_chain(ChainId.OGPU_TESTNET)
            ```
        """
        if chain_id not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=chain_id)
        cls._current_chain = chain_id

    @classmethod
    def get_current_chain(cls) -> ChainId:
        """Return the globally-active chain.

        Returns:
            The currently selected ``ChainId``.

        Raises:
            ChainNotSupportedError: If ``set_chain`` was never called
                and no default is available (shouldn't happen in practice —
                the default is ``OGPU_MAINNET``).

        Example:
            ```python
            ChainConfig.get_current_chain()
            # <ChainId.OGPU_MAINNET: 1071>
            ```
        """
        if cls._current_chain is None:
            raise ChainNotSupportedError(chain_id=None)
        return cls._current_chain

    @classmethod
    def get_contract_address(cls, contract_name: str) -> str:
        """Return the address of a singleton contract on the current chain.

        Used internally by ``load_contract`` to resolve NEXUS / CONTROLLER /
        TERMINAL / VAULT addresses. You rarely need to call this directly
        unless you're doing low-level web3 work outside the SDK.

        Args:
            contract_name: One of ``"NEXUS"``, ``"CONTROLLER"``,
                ``"TERMINAL"``, ``"VAULT"``.

        Returns:
            The 0x-prefixed checksummed address of the contract.

        Raises:
            ChainNotSupportedError: If the current chain has no contract
                mapping.
            ValueError: If the ``contract_name`` isn't configured for
                this chain.

        Example:
            ```python
            ChainConfig.get_contract_address("NEXUS")
            # '0x2b0cC6058313801D5feb184a539e3a0C5A87a6a1'
            ```
        """
        current = cls.get_current_chain()
        if current not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=current)
        contracts = cls.CHAIN_CONTRACTS[current]
        if contract_name not in contracts:
            raise ValueError(f"Contract {contract_name} not configured for chain {current}")
        return contracts[contract_name]

    @classmethod
    def get_all_supported_chains(cls) -> list[ChainId]:
        """Return every ``ChainId`` the SDK knows how to talk to.

        Returns:
            List of supported ``ChainId`` members.
        """
        return list(cls.CHAIN_CONTRACTS.keys())

    # ------------------------------------------------------------------ #
    # ABI loading
    # ------------------------------------------------------------------ #

    @classmethod
    def get_chain_abi_directory(cls) -> str:
        """Absolute path to the ABI directory for the current chain.

        The SDK ships ABIs in two subdirectories — ``ogpu/chain/abis/mainnet/``
        and ``ogpu/chain/abis/testnet/`` — and this method returns the
        one matching the current chain.

        Returns:
            Absolute filesystem path.

        Raises:
            ChainNotSupportedError: If the current chain doesn't have an
                ABI directory registered.
        """
        current = cls.get_current_chain()
        if current not in cls.CHAIN_DIRECTORIES:
            raise ChainNotSupportedError(chain_id=current)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "abis", cls.CHAIN_DIRECTORIES[current])

    @classmethod
    def load_abi(cls, abi_name: str) -> object:
        """Load a contract ABI JSON file for the current chain.

        Caches the parsed result per chain — subsequent calls are free.
        The ``abi_name`` is the filename without extension, e.g.
        ``"NexusAbi"`` for ``NexusAbi.json``.

        Args:
            abi_name: ABI file basename, e.g. ``"NexusAbi"``,
                ``"ControllerAbi"``, ``"TerminalAbi"``, ``"VaultAbi"``,
                ``"SourceAbi"``, ``"TaskAbi"``, ``"ResponseAbi"``.

        Returns:
            The parsed ABI (typically a list of dicts).

        Raises:
            FileNotFoundError: If no ABI file with that name exists for
                the current chain.
        """
        current = cls.get_current_chain()
        if current in cls._loaded_abis and abi_name in cls._loaded_abis[current]:
            return cls._loaded_abis[current][abi_name]

        abi_path = os.path.join(cls.get_chain_abi_directory(), f"{abi_name}.json")
        if not os.path.exists(abi_path):
            raise FileNotFoundError(f"ABI file not found: {abi_path}")

        with open(abi_path) as fh:
            abi_data: object = json.load(fh)

        cls._loaded_abis.setdefault(current, {})[abi_name] = abi_data
        return abi_data

    # ------------------------------------------------------------------ #
    # RPC configuration (new in v0.2.1 — decision F2)
    # ------------------------------------------------------------------ #

    @classmethod
    def set_rpc(cls, url: str, chain: ChainId | None = None) -> None:
        """Override the RPC URL for a given chain.

        Validates the URL by running ``Web3.is_connected()`` against it
        *before* committing the change. If the probe fails, raises
        ``InvalidRpcUrlError`` and leaves the existing URL unchanged.

        After a successful override, invalidates any cached Web3 instance
        for the affected chain so the next SDK call reconnects with the
        new URL.

        Args:
            url: The new RPC endpoint URL (http or https).
            chain: Which chain to override. Defaults to the currently
                active chain.

        Raises:
            ChainNotSupportedError: If ``chain`` is not a recognized
                OGPU chain.
            InvalidRpcUrlError: If the URL is unreachable or the probe
                connection fails.

        Example:
            ```python
            # Point at a local Anvil fork
            ChainConfig.set_rpc("http://127.0.0.1:8545")

            # Override a specific chain without switching
            ChainConfig.set_rpc(
                "https://my-node.example",
                chain=ChainId.OGPU_TESTNET,
            )
            ```
        """
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=target)

        probe = Web3(Web3.HTTPProvider(url))
        try:
            reachable = probe.is_connected()
        except Exception as exc:  # noqa: BLE001 — treated as unreachable
            raise InvalidRpcUrlError(url=url) from exc
        if not reachable:
            raise InvalidRpcUrlError(url=url)

        from .web3 import Web3Manager

        Web3Manager.update_rpc_url(target, url)

    @classmethod
    def get_rpc(cls, chain: ChainId | None = None) -> str:
        """Return the configured RPC URL for a chain.

        Reflects any overrides done via ``set_rpc``. Useful for logging,
        debugging, or passing the URL to an external library.

        Args:
            chain: Which chain to query. Defaults to the currently
                active chain.

        Returns:
            The current RPC URL for that chain.

        Raises:
            ChainNotSupportedError: If ``chain`` is not a recognized
                OGPU chain.

        Example:
            ```python
            ChainConfig.get_rpc()
            # 'https://mainnet-rpc.ogpuscan.io'
            ```
        """
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls.CHAIN_CONTRACTS:
            raise ChainNotSupportedError(chain_id=target)
        return CHAIN_RPC_URLS[target]

    @classmethod
    def reset_rpc(cls, chain: ChainId | None = None) -> None:
        """Restore the built-in default RPC URL for a chain.

        Undoes any earlier ``set_rpc`` overrides for the given chain
        and invalidates the cached Web3 instance so the next call
        reconnects against the default.

        Args:
            chain: Which chain to reset. Defaults to the currently
                active chain.

        Raises:
            ChainNotSupportedError: If ``chain`` is not a recognized
                OGPU chain.

        Example:
            ```python
            ChainConfig.set_rpc("http://127.0.0.1:8545")
            # ... later ...
            ChainConfig.reset_rpc()  # back to the OGPU default
            ```
        """
        target = chain if chain is not None else cls.get_current_chain()
        if target not in cls._DEFAULT_RPC_URLS:
            raise ChainNotSupportedError(chain_id=target)
        from .web3 import Web3Manager

        Web3Manager.update_rpc_url(target, cls._DEFAULT_RPC_URLS[target])
