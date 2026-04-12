from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ogpu.client.chain_config import ChainConfig, ChainId
from ogpu.types.errors import ChainNotSupportedError, InvalidRpcUrlError


class TestDefaults:
    def test_default_chain_is_mainnet(self):
        assert ChainConfig.get_current_chain() == ChainId.OGPU_MAINNET

    def test_supported_chains_include_both(self):
        chains = ChainConfig.get_all_supported_chains()
        assert ChainId.OGPU_MAINNET in chains
        assert ChainId.OGPU_TESTNET in chains


class TestSetChain:
    def test_switch_to_testnet(self):
        ChainConfig.set_chain(ChainId.OGPU_TESTNET)
        assert ChainConfig.get_current_chain() == ChainId.OGPU_TESTNET

    def test_invalid_chain_raises_chain_not_supported(self):
        bogus = MagicMock()
        with pytest.raises(ChainNotSupportedError):
            ChainConfig.set_chain(bogus)


class TestContractAddress:
    def test_mainnet_has_three_contracts(self):
        ChainConfig.set_chain(ChainId.OGPU_MAINNET)
        assert ChainConfig.get_contract_address("NEXUS").startswith("0x")
        assert ChainConfig.get_contract_address("CONTROLLER").startswith("0x")
        assert ChainConfig.get_contract_address("TERMINAL").startswith("0x")

    def test_unknown_contract_raises(self):
        with pytest.raises(ValueError):
            ChainConfig.get_contract_address("BOGUS")


class TestGetRpc:
    def test_mainnet_default(self):
        assert "mainnet-rpc.ogpuscan.io" in ChainConfig.get_rpc()

    def test_explicit_chain(self):
        assert "testnetrpc.ogpuscan.io" in ChainConfig.get_rpc(ChainId.OGPU_TESTNET)

    def test_unsupported_raises(self):
        with pytest.raises(ChainNotSupportedError):
            ChainConfig.get_rpc(MagicMock())


class TestSetRpc:
    def test_success_updates_web3_manager(self):
        probe = MagicMock()
        probe.is_connected.return_value = True
        with (
            patch(
                "ogpu.client.chain_config.Web3", return_value=probe
            ),
            patch(
                "ogpu.client.web3_manager.Web3Manager.update_rpc_url"
            ) as update,
        ):
            ChainConfig.set_rpc("https://my-node.example", ChainId.OGPU_MAINNET)
            update.assert_called_once_with(
                ChainId.OGPU_MAINNET, "https://my-node.example"
            )

    def test_unreachable_raises(self):
        probe = MagicMock()
        probe.is_connected.return_value = False
        with patch("ogpu.client.chain_config.Web3", return_value=probe):
            with pytest.raises(InvalidRpcUrlError):
                ChainConfig.set_rpc("https://broken.example")

    def test_connect_exception_raises(self):
        probe = MagicMock()
        probe.is_connected.side_effect = Exception("boom")
        with patch("ogpu.client.chain_config.Web3", return_value=probe):
            with pytest.raises(InvalidRpcUrlError):
                ChainConfig.set_rpc("https://boom.example")

    def test_unsupported_chain_raises(self):
        with pytest.raises(ChainNotSupportedError):
            ChainConfig.set_rpc("https://x.example", MagicMock())


class TestResetRpc:
    def test_restores_default(self):
        with patch(
            "ogpu.client.web3_manager.Web3Manager.update_rpc_url"
        ) as update:
            ChainConfig.reset_rpc(ChainId.OGPU_MAINNET)
            args = update.call_args[0]
            assert args[0] == ChainId.OGPU_MAINNET
            assert "mainnet-rpc.ogpuscan.io" in args[1]

    def test_uses_current_chain_when_omitted(self):
        ChainConfig.set_chain(ChainId.OGPU_TESTNET)
        with patch(
            "ogpu.client.web3_manager.Web3Manager.update_rpc_url"
        ) as update:
            ChainConfig.reset_rpc()
            args = update.call_args[0]
            assert args[0] == ChainId.OGPU_TESTNET
            assert "testnetrpc.ogpuscan.io" in args[1]


class TestLoadAbi:
    def test_loads_real_abi_from_disk(self):
        abi = ChainConfig.load_abi("NexusAbi")
        assert isinstance(abi, list)
        assert len(abi) > 0

    def test_caches_after_first_load(self):
        ChainConfig.load_abi("ControllerAbi")
        cached = ChainConfig._loaded_abis[ChainConfig.get_current_chain()]
        assert "ControllerAbi" in cached

    def test_missing_raises(self):
        with pytest.raises(FileNotFoundError):
            ChainConfig.load_abi("NotARealAbi")
