from pathlib import Path

from mecademic_cycle_report.mxprog_inspection import (
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