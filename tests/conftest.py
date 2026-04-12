"""Shared fixtures for the Phase 1 test suite."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from eth_account import Account


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset every process-wide cache before and after each test."""
    from ogpu.client.chain_config import ChainConfig, ChainId
    from ogpu.client.nonce_manager import NonceManager
    from ogpu.client.web3_manager import Web3Manager

    ChainConfig._current_chain = ChainId.OGPU_MAINNET
    ChainConfig._loaded_abis.clear()
    Web3Manager._web3_instances.clear()
    NonceManager.clear_all()
    yield
    NonceManager.clear_all()
    Web3Manager._web3_instances.clear()


@pytest.fixture
def sample_account():
    return Account.from_key("0x" + "11" * 32)


@pytest.fixture
def sample_account_2():
    return Account.from_key("0x" + "22" * 32)


@pytest.fixture
def mock_web3():
    web3 = MagicMock()
    web3.to_checksum_address = lambda a: a
    web3.is_address = lambda a: (
        isinstance(a, str) and a.startswith("0x") and len(a) == 42
    )
    web3.is_connected.return_value = True
    web3.eth.chain_id = 1071
    web3.eth.gas_price = 10**9
    web3.eth.get_transaction_count = MagicMock(return_value=7)
    return web3


@pytest.fixture
def mock_contract():
    contract = MagicMock()
    contract.address = "0x0000000000000000000000000000000000000042"
    return contract


@pytest.fixture
def mock_receipt_dict():
    return {
        "transactionHash": bytes.fromhex("a" * 64),
        "blockNumber": 100,
        "gasUsed": 21000,
        "status": 1,
        "logs": [],
    }
