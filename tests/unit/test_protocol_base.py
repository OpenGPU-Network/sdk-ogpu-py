from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from eth_account import Account
from web3.exceptions import ContractLogicError

from ogpu.protocol._base import (
    REVERT_PATTERN_MAP,
    ZERO_ADDRESS,
    TxExecutor,
    _DEFAULT_CHUNK_SIZE,
    _extract_revert_reason,
    _paginated_call,
    _permission_error_for,
    decode_revert,
    load_contract,
)
from ogpu.types.errors import (
    GasError,
    InsufficientBalanceError,
    NonceError,
    NotMasterError,
    NotProviderError,
    NotSourceOwnerError,
    NotTaskOwnerError,
    SourceInactiveError,
    TaskAlreadyFinalizedError,
    TaskExpiredError,
    TxRevertError,
)

_HEX_KEY = "0x" + "11" * 32


class TestConstants:
    def test_zero_address(self):
        assert ZERO_ADDRESS == "0x" + "0" * 40

    def test_default_chunk_size(self):
        assert _DEFAULT_CHUNK_SIZE == 100


class TestRevertPatternMap:
    def test_all_expected_keys_present(self):
        expected = {
            "NotOwner",
            "NotMaster",
            "NotProvider",
            "Expired",
            "AlreadyConfirmed",
            "AlreadyFinalized",
            "InsufficientBalance",
            "InsufficientLockup",
            "UnbondingNotElapsed",
            "NotEligible",
            "SourceInactive",
        }
        assert expected.issubset(set(REVERT_PATTERN_MAP.keys()))


class TestExtractRevertReason:
    def test_execution_reverted_prefix(self):
        exc = Exception("execution reverted: NotOwner")
        assert _extract_revert_reason(exc) == "NotOwner"

    def test_bare_revert(self):
        exc = Exception("revert: Expired")
        assert "Expired" in _extract_revert_reason(exc)

    def test_unknown_format_returns_message(self):
        exc = Exception("some random error")
        assert _extract_revert_reason(exc) == "some random error"


class TestPermissionErrorFor:
    def test_source_context_returns_source_owner_error(self):
        err = _permission_error_for("Nexus.updateSource(0xSRC)", "0xCaller")
        assert isinstance(err, NotSourceOwnerError)
        assert err.caller == "0xCaller"

    def test_task_context_returns_task_owner_error(self):
        err = _permission_error_for("Controller.cancelTask(0xTASK)", "0xCaller")
        assert isinstance(err, NotTaskOwnerError)


class TestDecodeRevert:
    def test_known_reason_decodes_to_typed(self):
        exc = Exception("execution reverted: NotMaster")
        decoded = decode_revert(exc, context="Terminal.announceMaster", caller="0xC")
        assert isinstance(decoded, NotMasterError)
        assert decoded.account == "0xC"

    def test_provider_revert(self):
        exc = Exception("execution reverted: NotProvider")
        decoded = decode_revert(exc, context="Nexus.attempt", caller="0xP")
        assert isinstance(decoded, NotProviderError)

    def test_expired_revert(self):
        exc = Exception("execution reverted: Expired")
        decoded = decode_revert(exc, context="Controller.publishTask(0xTASK)", caller="0xC")
        assert isinstance(decoded, TaskExpiredError)

    def test_already_finalized_revert(self):
        exc = Exception("execution reverted: AlreadyFinalized")
        decoded = decode_revert(exc, context="Controller.cancelTask(0xT)", caller="0xC")
        assert isinstance(decoded, TaskAlreadyFinalizedError)

    def test_insufficient_balance_revert(self):
        exc = Exception("execution reverted: InsufficientBalance")
        decoded = decode_revert(exc, context="Vault.lock", caller="0xC")
        assert isinstance(decoded, InsufficientBalanceError)

    def test_source_inactive_revert(self):
        exc = Exception("execution reverted: SourceInactive")
        decoded = decode_revert(exc, context="Nexus.register(0xSRC)", caller="0xC")
        assert isinstance(decoded, SourceInactiveError)

    def test_unknown_reason_falls_back_to_revert_error(self):
        exc = Exception("execution reverted: MysterySomething")
        decoded = decode_revert(exc, context="ctx", caller="0xC")
        assert isinstance(decoded, TxRevertError)
        assert "MysterySomething" in decoded.reason

    def test_substring_match_when_no_exact_key(self):
        exc = Exception("execution reverted: NotMaster: extra message")
        decoded = decode_revert(exc, context="ctx", caller="0xC")
        assert isinstance(decoded, NotMasterError)


class TestPaginatedCall:
    def test_upper_none_uses_count_fn(self):
        count = MagicMock(return_value=5)
        fetch = MagicMock(
            side_effect=[
                [f"0x{i:040x}" for i in (1, 2, 3)],
                [f"0x{i:040x}" for i in (4, 5)],
            ]
        )
        result = _paginated_call(count, fetch, chunk_size=3)
        assert len(result) == 5
        count.assert_called_once()
        assert fetch.call_count == 2

    def test_explicit_upper_skips_count(self):
        count = MagicMock(return_value=999)
        fetch = MagicMock(return_value=[f"0x{i:040x}" for i in (1, 2)])
        result = _paginated_call(count, fetch, lower=0, upper=2, chunk_size=10)
        count.assert_not_called()
        assert len(result) == 2

    def test_zero_addresses_filtered(self):
        fetch = MagicMock(
            return_value=[ZERO_ADDRESS, "0x" + "a" * 40, ZERO_ADDRESS, "0x" + "b" * 40]
        )
        result = _paginated_call(
            lambda: 4, fetch, lower=0, upper=4, chunk_size=10
        )
        assert len(result) == 2
        assert ZERO_ADDRESS not in result

    def test_chunk_size_respected(self):
        fetch_calls = []

        def fetch(lower, upper):
            fetch_calls.append((lower, upper))
            return [f"0x{i:040x}" for i in range(lower + 1, upper + 1)]

        result = _paginated_call(lambda: 10, fetch, upper=10, chunk_size=3)
        assert len(result) == 10
        assert [c[1] - c[0] for c in fetch_calls] == [3, 3, 3, 1]


class TestLoadContract:
    def test_singleton_resolution(self):
        fake_web3 = MagicMock()
        fake_web3.to_checksum_address = lambda a: a
        fake_contract = MagicMock(name="contract")
        fake_web3.eth.contract.return_value = fake_contract

        with (
            patch("ogpu.protocol._base._get_web3", return_value=fake_web3),
            patch(
                "ogpu.client.chain_config.ChainConfig.load_abi",
                return_value=[{"name": "publishSource", "type": "function"}],
            ),
            patch(
                "ogpu.client.chain_config.ChainConfig.get_contract_address",
                return_value="0xNEXUS",
            ) as get_addr,
        ):
            result = load_contract("NexusAbi")
            assert result is fake_contract
            get_addr.assert_called_once_with("NEXUS")

    def test_explicit_address(self):
        fake_web3 = MagicMock()
        fake_web3.to_checksum_address = lambda a: a
        with (
            patch("ogpu.protocol._base._get_web3", return_value=fake_web3),
            patch("ogpu.client.chain_config.ChainConfig.load_abi", return_value=[]),
            patch(
                "ogpu.client.chain_config.ChainConfig.get_contract_address"
            ) as get_addr,
        ):
            load_contract("TaskAbi", address="0xTASK")
            get_addr.assert_not_called()
            fake_web3.eth.contract.assert_called_once_with(address="0xTASK", abi=[])

    def test_unknown_singleton_raises(self):
        with (
            patch("ogpu.protocol._base._get_web3", return_value=MagicMock()),
            patch("ogpu.client.chain_config.ChainConfig.load_abi", return_value=[]),
        ):
            with pytest.raises(ValueError, match="no singleton address"):
                load_contract("TaskAbi")


class TestTxExecutor:
    def _make_contract(self, fn_name: str = "doThing"):
        contract = MagicMock()
        contract.address = "0x" + "4" * 40
        build_tx = MagicMock(return_value={"from": "0x1", "nonce": 0, "gas": 1})
        fn = MagicMock()
        fn.build_transaction = build_tx
        function_builder = MagicMock(return_value=fn)
        setattr(contract.functions, fn_name, function_builder)
        return contract, function_builder, fn

    def _setup_web3(self, receipt_status: int = 1):
        web3 = MagicMock()
        web3.eth.account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"raw"
        )
        tx_hash = MagicMock()
        tx_hash.hex.return_value = "a" * 64
        web3.eth.send_raw_transaction.return_value = tx_hash
        web3.eth.wait_for_transaction_receipt.return_value = {
            "transactionHash": bytes.fromhex("a" * 64),
            "blockNumber": 1,
            "gasUsed": 21000,
            "status": receipt_status,
            "logs": [],
        }
        web3.to_checksum_address = lambda a: a
        return web3

    def test_happy_path(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch(
                "ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=5
            ),
            patch(
                "ogpu.client.nonce_manager.NonceManager.increment_nonce"
            ) as inc,
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract, "doThing", (42,), signer=sample_account
            )
            receipt = executor.execute()

        assert receipt.status == 1
        assert receipt.block_number == 1
        assert receipt.gas_used == 21000
        inc.assert_called_once()

    def test_revert_decoded(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()

        def raise_revert(*a, **kw):
            raise ContractLogicError("execution reverted: NotOwner")

        contract.functions.doThing(42).build_transaction.side_effect = raise_revert

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=1),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract,
                "doThing",
                (42,),
                signer=sample_account,
                context="Controller.cancelTask(0xT)",
            )
            with pytest.raises(NotTaskOwnerError):
                executor.execute()

    def test_nonce_error_retries_then_succeeds(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()
        call_counter = {"n": 0}

        def flaky_send(*a, **kw):
            call_counter["n"] += 1
            if call_counter["n"] == 1:
                raise RuntimeError("nonce too low")
            tx_hash = MagicMock()
            tx_hash.hex.return_value = "a" * 64
            return tx_hash

        web3.eth.send_raw_transaction.side_effect = flaky_send

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch(
                "ogpu.client.nonce_manager.NonceManager.reset_nonce"
            ) as reset,
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account, max_retries=3
            )
            receipt = executor.execute()
            assert receipt.status == 1
            assert call_counter["n"] == 2
            reset.assert_called()

    def test_nonce_error_exhausts_retries(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()

        web3.eth.send_raw_transaction.side_effect = RuntimeError("nonce too low")

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account, max_retries=2
            )
            with pytest.raises(NonceError):
                executor.execute()

    def test_underpriced_retries_with_backoff(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()
        call_counter = {"n": 0}

        def flaky_send(*a, **kw):
            call_counter["n"] += 1
            if call_counter["n"] == 1:
                raise RuntimeError("replacement transaction underpriced")
            tx_hash = MagicMock()
            tx_hash.hex.return_value = "a" * 64
            return tx_hash

        web3.eth.send_raw_transaction.side_effect = flaky_send

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
            patch("ogpu.protocol._base.time.sleep") as sleeper,
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account, max_retries=3
            )
            receipt = executor.execute()
            assert receipt.status == 1
            sleeper.assert_called_with(5)

    def test_underpriced_exhausts_to_gas_error(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()
        web3.eth.send_raw_transaction.side_effect = RuntimeError(
            "replacement transaction underpriced"
        )

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
            patch("ogpu.protocol._base.time.sleep"),
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account, max_retries=2
            )
            with pytest.raises(GasError):
                executor.execute()

    def test_receipt_status_zero_raises_revert(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3(receipt_status=0)

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account
            )
            with pytest.raises(TxRevertError):
                executor.execute()

    def test_non_retryable_exception_bubbles(self, sample_account):
        contract, _, _ = self._make_contract()
        web3 = self._setup_web3()
        web3.eth.send_raw_transaction.side_effect = RuntimeError("something else")

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account
            )
            with pytest.raises(RuntimeError, match="something else"):
                executor.execute()

    def test_value_passed_for_payable(self, sample_account):
        contract, _, fn = self._make_contract()
        web3 = self._setup_web3()

        with (
            patch("ogpu.protocol._base._get_web3", return_value=web3),
            patch("ogpu.client.nonce_manager.NonceManager.get_nonce", return_value=3),
            patch("ogpu.client.nonce_manager.NonceManager.increment_nonce"),
            patch("ogpu.client.nonce_manager.NonceManager.reset_nonce"),
        ):
            executor = TxExecutor(
                contract, "doThing", (), signer=sample_account, value=1000
            )
            executor.execute()

        call_args = fn.build_transaction.call_args[0][0]
        assert call_args["value"] == 1000

    def test_default_context_uses_contract_and_fn(self, sample_account):
        contract, _, _ = self._make_contract()
        executor = TxExecutor(contract, "doThing", (), signer=sample_account)
        assert contract.address in executor.context
        assert "doThing" in executor.context
