from __future__ import annotations

import pytest

from ogpu.types.enums import Role
from ogpu.types.errors import (
    ChainNotSupportedError,
    ConfigError,
    GasError,
    IPFSError,
    IPFSFetchError,
    IPFSGatewayError,
    InsufficientBalanceError,
    InsufficientLockupError,
    InvalidRpcUrlError,
    InvalidSignerError,
    MasterNotFoundError,
    MissingSignerError,
    NonceError,
    NotEligibleError,
    NotFoundError,
    NotMasterError,
    NotProviderError,
    NotSourceOwnerError,
    NotTaskOwnerError,
    OGPUError,
    PermissionError,
    ProviderNotFoundError,
    ResponseAlreadyConfirmedError,
    ResponseNotFoundError,
    SourceInactiveError,
    SourceNotFoundError,
    StateError,
    TaskAlreadyFinalizedError,
    TaskExpiredError,
    TaskNotFoundError,
    TxError,
    TxRevertError,
    UnbondingPeriodNotElapsedError,
    VaultError,
)


class TestBaseHierarchy:
    def test_all_errors_inherit_from_ogpu_error(self):
        for cls in [
            NotFoundError, StateError, PermissionError, VaultError,
            TxError, ConfigError, IPFSError,
        ]:
            assert issubclass(cls, OGPUError)

    def test_ogpu_error_inherits_from_exception(self):
        assert issubclass(OGPUError, Exception)


class TestNotFoundDomain:
    @pytest.mark.parametrize(
        "cls",
        [
            TaskNotFoundError,
            SourceNotFoundError,
            ResponseNotFoundError,
            ProviderNotFoundError,
            MasterNotFoundError,
        ],
    )
    def test_inherits_from_not_found(self, cls):
        assert issubclass(cls, NotFoundError)

    def test_address_stored(self):
        err = TaskNotFoundError(address="0xabc")
        assert err.address == "0xabc"
        assert "0xabc" in str(err)

    def test_catch_by_domain(self):
        with pytest.raises(NotFoundError):
            raise SourceNotFoundError("0xabc")
        with pytest.raises(OGPUError):
            raise ResponseNotFoundError("0xabc")


class TestStateDomain:
    def test_task_expired_stores_fields(self):
        err = TaskExpiredError(task="0xtask", expiry=9999)
        assert err.task == "0xtask"
        assert err.expiry == 9999
        assert "9999" in str(err)

    def test_task_already_finalized(self):
        err = TaskAlreadyFinalizedError(task="0xtask")
        assert err.task == "0xtask"

    def test_response_already_confirmed(self):
        err = ResponseAlreadyConfirmedError(response="0xresp")
        assert "0xresp" in str(err)

    def test_source_inactive(self):
        err = SourceInactiveError(source="0xsrc")
        assert "0xsrc" in str(err)

    def test_catch_by_state_domain(self):
        with pytest.raises(StateError):
            raise TaskExpiredError("0xtask", 1)


class TestPermissionDomain:
    def test_not_task_owner(self):
        err = NotTaskOwnerError(task="0xtask", caller="0xC")
        assert err.task == "0xtask"
        assert err.caller == "0xC"

    def test_not_source_owner(self):
        err = NotSourceOwnerError(source="0xsrc", caller="0xC")
        assert err.source == "0xsrc"
        assert err.caller == "0xC"

    def test_not_master(self):
        err = NotMasterError(account="0xacc")
        assert err.account == "0xacc"

    def test_not_provider(self):
        err = NotProviderError(account="0xacc")
        assert err.account == "0xacc"

    def test_catch_by_permission_domain(self):
        with pytest.raises(PermissionError):
            raise NotMasterError("0xacc")


class TestVaultDomain:
    def test_insufficient_balance(self):
        err = InsufficientBalanceError(account="0xA", required=10, available=5)
        assert err.required == 10
        assert err.available == 5
        assert "10" in str(err) and "5" in str(err)

    def test_insufficient_lockup(self):
        err = InsufficientLockupError(account="0xA", required=10, available=2)
        assert err.required == 10

    def test_unbonding_period(self):
        err = UnbondingPeriodNotElapsedError(account="0xA", remaining_seconds=120)
        assert err.remaining_seconds == 120

    def test_not_eligible(self):
        err = NotEligibleError(account="0xA")
        assert err.account == "0xA"

    def test_catch_by_vault_domain(self):
        with pytest.raises(VaultError):
            raise InsufficientBalanceError("0xA", 1, 0)


class TestTxDomain:
    def test_tx_revert_error(self):
        err = TxRevertError(reason="NotOwner")
        assert err.reason == "NotOwner"
        assert "NotOwner" in str(err)

    def test_nonce_error(self):
        err = NonceError(address="0xA", tried=5, suggested=6)
        assert err.tried == 5
        assert err.suggested == 6

    def test_gas_error(self):
        err = GasError(reason="too low")
        assert "too low" in str(err)

    def test_invalid_rpc_url_error(self):
        err = InvalidRpcUrlError(url="https://bad.example")
        assert "bad.example" in str(err)


class TestConfigDomain:
    def test_missing_signer_with_role(self):
        err = MissingSignerError(role=Role.CLIENT)
        assert err.role == Role.CLIENT
        assert "CLIENT_PRIVATE_KEY" in str(err)

    def test_missing_signer_without_role(self):
        err = MissingSignerError(role=None)
        assert err.role is None
        assert "signer" in str(err).lower()

    def test_invalid_signer(self):
        err = InvalidSignerError(reason="bad hex")
        assert "bad hex" in str(err)

    def test_chain_not_supported(self):
        err = ChainNotSupportedError(chain_id=42)
        assert err.chain_id == 42


class TestIPFSDomain:
    def test_fetch_error(self):
        err = IPFSFetchError(url="ipfs://Qm", reason="timeout")
        assert err.url == "ipfs://Qm"
        assert err.reason == "timeout"

    def test_gateway_error(self):
        err = IPFSGatewayError(gateway="https://gw", status_code=503)
        assert err.status_code == 503

    def test_catch_by_ipfs_domain(self):
        with pytest.raises(IPFSError):
            raise IPFSGatewayError("https://gw", 500)
