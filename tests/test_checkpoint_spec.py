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


def test_validate_observation_rejects_unknown_status() -> None:
    try:
        validate_observation(CheckpointObservation(checkpoint_id=1, status="bad", elapsed_s=1.0))
    except CheckpointValidationError as exc:
        assert "Unsupported checkpoint status" in str(exc)
    else:
        raise AssertionError("Expected invalid checkpoint status to fail")
