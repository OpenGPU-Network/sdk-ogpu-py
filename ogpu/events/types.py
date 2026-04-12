"""Typed event dataclasses — frozen snapshots of on-chain Nexus events."""

from __future__ import annotations

from dataclasses import dataclass

from ..types.enums import ResponseStatus, TaskStatus


@dataclass(frozen=True)
class TaskPublishedEvent:
    task: str
    source: str
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class AttemptedEvent:
    task: str
    provider: str
    suggested_payment: int
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class ResponseSubmittedEvent:
    response: str
    task: str
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class ResponseStatusChangedEvent:
    response: str
    status: ResponseStatus
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class TaskStatusChangedEvent:
    task: str
    status: TaskStatus
    block_number: int
    transaction_hash: str
    log_index: int


@dataclass(frozen=True)
class RegisteredEvent:
    provider: str
    registrant_id: int
    source: str
    block_number: int
    transaction_hash: str
    log_index: int
