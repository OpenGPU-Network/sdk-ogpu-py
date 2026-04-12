"""Receipt dataclass — unified return type for every write operation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Receipt:
    """Result of a successful on-chain transaction."""

    tx_hash: str
    block_number: int
    gas_used: int
    status: int
    logs: list[Any] = field(default_factory=list)
    timestamp: int = 0

    @classmethod
    def from_web3_receipt(cls, receipt: Any, timestamp: int = 0) -> Receipt:
        """Build a ``Receipt`` from a ``web3.types.TxReceipt`` dict."""
        tx_hash = receipt["transactionHash"]
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()
        if isinstance(tx_hash, (bytes, bytearray)):
            tx_hash = tx_hash.hex()
        if not str(tx_hash).startswith("0x"):
            tx_hash = "0x" + str(tx_hash)
        return cls(
            tx_hash=str(tx_hash),
            block_number=int(receipt["blockNumber"]),
            gas_used=int(receipt["gasUsed"]),
            status=int(receipt["status"]),
            logs=list(receipt.get("logs", [])),
            timestamp=int(timestamp),
        )
