from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


FRAMEWORK_CHECKPOINT_ID_MIN = 7000
FRAMEWORK_CHECKPOINT_ID_MAX = 7999


@dataclass(frozen=True, slots=True)
class ExpectedCheckpoint:
    """Native Mecademic checkpoint expected during a program run."""

    checkpoint_id: int
    label: str
    timeout_s: float | None = None
    required: bool = True
    queue_next_run: bool = False


@dataclass(frozen=True, slots=True)
class CheckpointObservation:
    """Observed checkpoint response from the robot."""

    checkpoint_id: int
    status: str
    elapsed_s: float
    label: str | None = None
    detail: str | None = None


class CheckpointValidationError(ValueError):
    """Raised when checkpoint definitions are invalid."""


VALID_STATUSES = {"reached", "discarded", "timeout"}


def is_framework_checkpoint_id(checkpoint_id: int) -> bool:
    return FRAMEWORK_CHECKPOINT_ID_MIN <= checkpoint_id <= FRAMEWORK_CHECKPOINT_ID_MAX


def boundary_checkpoint_ids(pair_index: int) -> tuple[int, int]:
    if pair_index < 0:
        raise CheckpointValidationError("Boundary checkpoint pair index cannot be negative")
    start_checkpoint_id = FRAMEWORK_CHECKPOINT_ID_MIN + (pair_index * 2)
    end_checkpoint_id = start_checkpoint_id + 1
    if end_checkpoint_id > FRAMEWORK_CHECKPOINT_ID_MAX:
        raise CheckpointValidationError(
            "Framework boundary checkpoint range 7000-7999 is exhausted"
        )
    return start_checkpoint_id, end_checkpoint_id


def validate_expected_checkpoints(checkpoints: Iterable[ExpectedCheckpoint]) -> list[ExpectedCheckpoint]:
    ordered = list(checkpoints)
    if not ordered:
        return ordered

    queue_next_run_count = sum(1 for checkpoint in ordered if checkpoint.queue_next_run)
    if queue_next_run_count > 1:
        raise CheckpointValidationError("At most one checkpoint may be marked queue_next_run")
    if ordered[-1].queue_next_run:
        raise CheckpointValidationError("The final checkpoint cannot be marked queue_next_run")

    seen_ids: set[int] = set()
    for checkpoint in ordered:
        if checkpoint.checkpoint_id <= 0:
            raise CheckpointValidationError("Checkpoint ids must be positive integers")
        if is_framework_checkpoint_id(checkpoint.checkpoint_id):
            raise CheckpointValidationError(
                "Checkpoint ids in range 7000-7999 are reserved for framework boundary checkpoints"
            )
        if checkpoint.checkpoint_id in seen_ids:
            raise CheckpointValidationError(
                f"Duplicate checkpoint id detected: {checkpoint.checkpoint_id}"
            )
        if checkpoint.timeout_s is not None and checkpoint.timeout_s <= 0:
            raise CheckpointValidationError("Checkpoint timeouts must be greater than zero")
        seen_ids.add(checkpoint.checkpoint_id)

    return ordered


def validate_observation(observation: CheckpointObservation) -> CheckpointObservation:
    if observation.status not in VALID_STATUSES:
        raise CheckpointValidationError(
            f"Unsupported checkpoint status: {observation.status}"
        )
    if observation.elapsed_s < 0:
        raise CheckpointValidationError("Checkpoint elapsed time cannot be negative")
    return observation
