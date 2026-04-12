"""Event watchers — mock async tests. No chain access."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ogpu.events.types import (
    AttemptedEvent,
    RegisteredEvent,
    ResponseStatusChangedEvent,
    ResponseSubmittedEvent,
    TaskPublishedEvent,
    TaskStatusChangedEvent,
)
from ogpu.events.watchers import (
    watch_attempted,
    watch_registered,
    watch_response_status_changed,
    watch_response_submitted,
    watch_task_published,
    watch_task_status_changed,
)
from ogpu.types.enums import ResponseStatus, TaskStatus

_TASK = "0x" + "bb" * 20
_SRC = "0x" + "aa" * 20
_RESP = "0x" + "cc" * 20
_PROV = "0x" + "dd" * 20


def _make_entry(args, block=100, tx_hash=b"\xab" * 32, log_index=0):
    return {"args": args, "blockNumber": block, "transactionHash": tx_hash, "logIndex": log_index}


def _mock_filter(entries_batches):
    """Return an AsyncMock filter that yields entries_batches on successive get_new_entries calls."""
    filt = AsyncMock()
    call_count = {"n": 0}

    async def get_entries():
        idx = call_count["n"]
        call_count["n"] += 1
        if idx < len(entries_batches):
            return entries_batches[idx]
        raise StopIteration

    filt.get_new_entries = get_entries
    return filt


async def _collect_one(gen):
    """Collect the first event from an async generator with a timeout."""
    try:
        async def _inner():
            async for event in gen:
                return event
            return None
        return await asyncio.wait_for(_inner(), timeout=1.0)
    except asyncio.TimeoutError:
        return None


def _patch_infra(filter_obj):
    """Patch get_async_web3 + get_nexus_contract to return mocks with the given filter."""
    w3 = AsyncMock()
    w3.eth.block_number = 1

    contract = AsyncMock()
    for event_name in (
        "TaskPublished", "Attempted", "ResponseSubmitted",
        "ResponseStatusChanged", "TaskStatusChanged", "Registered",
    ):
        getattr(contract.events, event_name).create_filter = AsyncMock(return_value=filter_obj)

    return (
        patch("ogpu.events.watchers.get_async_web3", return_value=w3),
        patch("ogpu.events.watchers.get_nexus_contract", return_value=contract),
    )


class TestWatchTaskPublished:
    @pytest.mark.asyncio
    async def test_yields_matching_event(self):
        entry = _make_entry({"task": _TASK, "source": _SRC})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_task_published(_SRC, from_block=0, poll_interval=0.01))
        assert isinstance(event, TaskPublishedEvent)
        assert event.task == _TASK
        assert event.source == _SRC

    @pytest.mark.asyncio
    async def test_skips_non_matching_source(self):
        entry = _make_entry({"task": _TASK, "source": "0x" + "ff" * 20})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_task_published(_SRC, from_block=0, poll_interval=0.01))
        assert event is None


class TestWatchAttempted:
    @pytest.mark.asyncio
    async def test_yields_event(self):
        entry = _make_entry({"task": _TASK, "provider": _PROV, "suggestedPayment": 100})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_attempted(_TASK, from_block=0, poll_interval=0.01))
        assert isinstance(event, AttemptedEvent)
        assert event.provider == _PROV
        assert event.suggested_payment == 100


class TestWatchResponseSubmitted:
    @pytest.mark.asyncio
    async def test_yields_event(self):
        entry = _make_entry({"response": _RESP, "task": _TASK})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_response_submitted(_TASK, from_block=0, poll_interval=0.01))
        assert isinstance(event, ResponseSubmittedEvent)
        assert event.response == _RESP


class TestWatchResponseStatusChanged:
    @pytest.mark.asyncio
    async def test_yields_event_with_enum(self):
        entry = _make_entry({"response": _RESP, "status": 1})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_response_status_changed(_RESP, from_block=0, poll_interval=0.01))
        assert isinstance(event, ResponseStatusChangedEvent)
        assert event.status == ResponseStatus.CONFIRMED


class TestWatchTaskStatusChanged:
    @pytest.mark.asyncio
    async def test_yields_event_with_enum(self):
        entry = _make_entry({"task": _TASK, "status": 5})
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_task_status_changed(_TASK, from_block=0, poll_interval=0.01))
        assert isinstance(event, TaskStatusChangedEvent)
        assert event.status == TaskStatus.FINALIZED


class TestWatchRegistered:
    @pytest.mark.asyncio
    async def test_yields_event(self):
        entry = _make_entry({
            "provider": _PROV, "registrantId": 7,
            "source": _SRC, "preferredEnvironment": 1,
        })
        filt = _mock_filter([[entry]])
        p1, p2 = _patch_infra(filt)
        with p1, p2:
            event = await _collect_one(watch_registered(_SRC, from_block=0, poll_interval=0.01))
        assert isinstance(event, RegisteredEvent)
        assert event.registrant_id == 7
        assert event.provider == _PROV
