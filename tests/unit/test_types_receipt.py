from __future__ import annotations

from ogpu.types.receipt import Receipt


class TestReceipt:
    def test_direct_construction(self):
        receipt = Receipt(
            tx_hash="0xabc",
            block_number=5,
            gas_used=100,
            status=1,
        )
        assert receipt.tx_hash == "0xabc"
        assert receipt.block_number == 5
        assert receipt.gas_used == 100
        assert receipt.status == 1
        assert receipt.logs == []
        assert receipt.timestamp == 0

    def test_frozen_dataclass(self):
        receipt = Receipt(tx_hash="0x1", block_number=1, gas_used=1, status=1)
        try:
            receipt.tx_hash = "0x2"  # type: ignore[misc]
            raised = False
        except Exception:
            raised = True
        assert raised

    def test_from_web3_receipt_with_bytes_hash(self):
        raw = {
            "transactionHash": bytes.fromhex("ab" * 32),
            "blockNumber": 10,
            "gasUsed": 42,
            "status": 1,
            "logs": [{"address": "0x1"}],
        }
        receipt = Receipt.from_web3_receipt(raw, timestamp=1234567890)
        assert receipt.block_number == 10
        assert receipt.gas_used == 42
        assert receipt.status == 1
        assert receipt.logs == [{"address": "0x1"}]
        assert receipt.timestamp == 1234567890
        assert receipt.tx_hash.startswith("0x")
        assert len(receipt.tx_hash) == 66  # 0x + 64 hex chars

    def test_from_web3_receipt_with_string_hash(self):
        raw = {
            "transactionHash": "0xdead",
            "blockNumber": 1,
            "gasUsed": 1,
            "status": 1,
            "logs": [],
        }
        receipt = Receipt.from_web3_receipt(raw)
        assert receipt.tx_hash == "0xdead"
