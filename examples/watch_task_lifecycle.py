"""Async event watching: monitor a task for attempts and responses."""

import asyncio

from ogpu.client import ChainConfig, ChainId
from ogpu.events import watch_attempted, watch_response_submitted

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

TASK_ADDRESS = "0xYOUR_TASK_ADDRESS"


async def monitor():
    print(f"Watching task {TASK_ADDRESS} for attempts...")

    async for event in watch_attempted(TASK_ADDRESS):
        print(f"  Attempt from {event.provider} @ block {event.block_number}")
        print(f"  Suggested payment: {event.suggested_payment} wei")

        print("  Now watching for response...")
        async for resp in watch_response_submitted(TASK_ADDRESS):
            print(f"  Response {resp.response} submitted @ block {resp.block_number}")
            return


asyncio.run(monitor())
