from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ExpectedCheckpoint:
    """Native Mecademic checkpoint expected during a program run."""

    checkpoint_id: int
    label: str
    timeout_s: float | None = None
    required: bool = True


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


def validate_expected_checkpoints(checkpoints: Iterable[ExpectedCheckpoint]) -> list[ExpectedCheckpoint]:
    ordered = list(checkpoints)
    if not ordered:
        raise CheckpointValidationError("At least one checkpoint must be configured")

    seen_ids: set[int] = set()
    for checkpoint in ordered:
        if checkpoint.checkpoint_id <= 0:
            raise CheckpointValidationError("Checkpoint ids must be positive integers")
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
