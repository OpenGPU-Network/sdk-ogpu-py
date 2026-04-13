"""Receipt dataclass — unified return type for every write operation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Receipt:
    """Result of a successful on-chain transaction.

    Every state-changing operation in the SDK returns a ``Receipt``
    instance — ``TxExecutor`` builds it from the raw web3 ``TxReceipt``
    after the transaction is mined. This gives you a consistent,
    immutable, typed object to log and inspect without having to touch
    web3's ``AttributeDict``.

    Frozen — create a new instance instead of mutating.

    Attributes:
        tx_hash: Transaction hash as a 0x-prefixed hex string.
        block_number: Block the transaction was included in.
        gas_used: Gas actually consumed by the transaction.
        status: Transaction status (1 = success, 0 = reverted). The SDK
            raises ``TxRevertError`` on status 0, so in practice every
            ``Receipt`` you see has ``status == 1``.
        logs: Raw event log list from the receipt, useful for custom
            event decoding.
        timestamp: Unix timestamp of the block when available, else 0.

    Example:
        ```python
        from ogpu.protocol import controller
        receipt = controller.cancel_task("0x...", signer=KEY)
        print(receipt.tx_hash)
        # '0xabc...'
        print(receipt.block_number, receipt.gas_used)
        # 12345678 21000
        ```
    """

    tx_hash: str
    block_number: int
    gas_used: int
    status: int
    logs: list[Any] = field(default_factory=list)
    timestamp: int = 0

    @classmethod
    def from_web3_receipt(cls, receipt: Any, timestamp: int = 0) -> Receipt:
        """Build a ``Receipt`` from a raw web3 ``TxReceipt`` dict.

        Used internally by ``TxExecutor`` to wrap the result of
        ``web3.eth.wait_for_transaction_receipt``. Handles the transaction
        hash coming in as bytes, ``HexBytes``, or string.

        Args:
            receipt: The ``TxReceipt`` dict returned by web3.
            timestamp: Optional block timestamp, defaults to 0.

        Returns:
            A new ``Receipt`` instance.
        """
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
