from mecademic_cycle_report.checkpoint_spec import (
    CheckpointObservation,
    CheckpointValidationError,
    ExpectedCheckpoint,
    validate_expected_checkpoints,
    validate_observation,
)


def test_validate_expected_checkpoints_rejects_duplicate_ids() -> None:
    checkpoints = [
        ExpectedCheckpoint(checkpoint_id=10, label="start"),
        ExpectedCheckpoint(checkpoint_id=10, label="end"),
    ]

    try:
        validate_expected_checkpoints(checkpoints)
    except CheckpointValidationError as exc:
        assert "Duplicate checkpoint id" in str(exc)
    else:
        raise AssertionError("Expected duplicate checkpoint ids to fail")


def test_validate_expected_checkpoints_rejects_framework_reserved_range() -> None:
    checkpoints = [ExpectedCheckpoint(checkpoint_id=7000, label="reserved")]

    try:
        validate_expected_checkpoints(checkpoints)
    except CheckpointValidationError as exc:
        assert "7000-7999" in str(exc)
    else:
        raise AssertionError("Expected reserved framework checkpoint ids to fail")


def test_validate_observation_rejects_unknown_status() -> None:
    try:
        validate_observation(CheckpointObservation(checkpoint_id=1, status="bad", elapsed_s=1.0))
    except CheckpointValidationError as exc:
        assert "Unsupported checkpoint status" in str(exc)
    else:
        raise AssertionError("Expected invalid checkpoint status to fail")


def test_validate_expected_checkpoints_rejects_multiple_queue_next_run_markers() -> None:
    checkpoints = [
        ExpectedCheckpoint(checkpoint_id=10, label="handoff_1", queue_next_run=True),
        ExpectedCheckpoint(checkpoint_id=20, label="handoff_2", queue_next_run=True),
        ExpectedCheckpoint(checkpoint_id=30, label="end"),
    ]

    try:
        validate_expected_checkpoints(checkpoints)
    except CheckpointValidationError as exc:
        assert "queue_next_run" in str(exc)
    else:
        raise AssertionError("Expected multiple queue_next_run markers to fail")


def test_validate_expected_checkpoints_rejects_final_queue_next_run_marker() -> None:
    checkpoints = [
        ExpectedCheckpoint(checkpoint_id=10, label="start"),
        ExpectedCheckpoint(checkpoint_id=20, label="handoff", queue_next_run=True),
    ]

    try:
        validate_expected_checkpoints(checkpoints)
    except CheckpointValidationError as exc:
        assert "final checkpoint" in str(exc)
    else:
        raise AssertionError("Expected final queue_next_run marker to fail")
