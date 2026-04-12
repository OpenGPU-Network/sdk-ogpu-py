from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.client.chain_config import ChainId
from ogpu.client.web3_manager import Web3Manager, get_web3_for_chain


class TestWeb3Manager:
    def test_caches_instance_per_chain(self):
        Web3Manager._web3_instances.clear()
        probe = MagicMock()
        probe.is_connected.return_value = True

        with patch("ogpu.client.web3_manager.Web3", return_value=probe):
            a = Web3Manager.get_web3_instance(ChainId.OGPU_MAINNET)
            b = Web3Manager.get_web3_instance(ChainId.OGPU_MAINNET)
        assert a is b

    def test_uses_current_chain_when_omitted(self):
        Web3Manager._web3_instances.clear()
        probe = MagicMock()
        probe.is_connected.return_value = True

        with patch("ogpu.client.web3_manager.Web3", return_value=probe):
            a = Web3Manager.get_web3_instance()
        assert a is probe

    def test_unreachable_raises_connection_error(self):
        Web3Manager._web3_instances.clear()
        probe = MagicMock()
        probe.is_connected.return_value = False

        with patch("ogpu.client.web3_manager.Web3", return_value=probe):
            with pytest.raises(ConnectionError):
                Web3Manager.get_web3_instance(ChainId.OGPU_MAINNET)

    def test_update_rpc_url_invalidates_cache(self):
        Web3Manager._web3_instances.clear()
        probe = MagicMock()
        probe.is_connected.return_value = True
        with patch("ogpu.client.web3_manager.Web3", return_value=probe):
            Web3Manager.get_web3_instance(ChainId.OGPU_MAINNET)
        assert ChainId.OGPU_MAINNET in Web3Manager._web3_instances
        Web3Manager.update_rpc_url(ChainId.OGPU_MAINNET, "https://new.example")
        assert ChainId.OGPU_MAINNET not in Web3Manager._web3_instances

    def test_get_web3_for_chain_convenience(self):
        Web3Manager._web3_instances.clear()
        probe = MagicMock()
        probe.is_connected.return_value = True
        with patch("ogpu.client.web3_manager.Web3", return_value=probe):
            assert get_web3_for_chain(ChainId.OGPU_TESTNET) is probe
