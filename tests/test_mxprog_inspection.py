from pathlib import Path

from mecademic_cycle_report.mxprog_inspection import (
    _append_path_suffix_without_duplicate,
    build_scenario_template_payload,
    extract_program_checkpoint_ids,
    extract_program_variables,
    find_missing_scenario_variables,
)
from mecademic_cycle_report.scenario_matrix import ScenarioProfile


def test_extract_program_variables_reads_vars_references(tmp_path: Path) -> None:
    program_path = tmp_path / "program.mxprog"
    program_path.write_text(
        "MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\nSetCartLinVel(vars.SPD_INSERT)\n",
        encoding="utf-8",
    )

    assert extract_program_variables(program_path) == {"PICK_X", "PICK_Y", "SPD_INSERT"}


def test_find_missing_scenario_variables_reports_per_scenario() -> None:
    missing = find_missing_scenario_variables(
        {"PICK_X", "PICK_Y", "SPD_INSERT"},
        [
            ScenarioProfile(name="complete", variables={"PICK_X": 1, "PICK_Y": 2, "SPD_INSERT": 800}),
            ScenarioProfile(name="missing-y", variables={"PICK_X": 1, "SPD_INSERT": 800}),
        ],
    )

    assert missing == {"missing-y": ["PICK_Y"]}


def test_extract_program_checkpoint_ids_preserves_first_occurrence_order(tmp_path: Path) -> None:
    program_path = tmp_path / "program.mxprog"
    program_path.write_text(
        "SetCheckpoint(10)\nSetCheckpoint(20)\nSetCheckpoint(10)\nSetCheckpoint(30)\n",
        encoding="utf-8",
    )

    assert extract_program_checkpoint_ids(program_path) == [10, 20, 30]


def test_build_scenario_template_payload_uses_detected_variables_and_checkpoints(tmp_path: Path) -> None:
    program_path = tmp_path / "cell.mxprog"
    program_path.write_text(
        "SetCheckpoint(1)\n"
        "MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\n"
        "SetCartLinVel(vars.SPD_INSERT)\n"
        "SetCheckpoint(2)\n",
        encoding="utf-8",
    )

    payload = build_scenario_template_payload(
        program_path,
        robot_address="10.0.0.5",
        enforce_sim_mode=False,
        output_root="artifacts/generated",
        output_subdir="batch_a",
    )

    assert payload["robot"] == {"address": "10.0.0.5", "enforce_sim_mode": False}
    assert payload["analysis"]["output_dir"] == "artifacts/generated/batch_a/cell"
    assert payload["checkpoints"] == [
        {"checkpoint_id": 1, "label": "checkpoint_1", "timeout_s": 10.0},
        {"checkpoint_id": 2, "label": "checkpoint_2", "timeout_s": 10.0},
    ]
    assert payload["scenarios"]["profiles"] == [
        {
            "name": "baseline",
            "variables": {
                "PICK_X": "__TODO__",
                "PICK_Y": "__TODO__",
                "SPD_INSERT": "__TODO__",
            },
        }
    ]


def test_append_path_suffix_without_duplicate_avoids_repeating_tail() -> None:
    assert _append_path_suffix_without_duplicate(
        Path("artifacts/generated"),
        Path("generated"),
    ) == Path("artifacts/generated")
    assert _append_path_suffix_without_duplicate(
        Path("artifacts"),
        Path("generated"),
    ) == Path("artifacts/generated")