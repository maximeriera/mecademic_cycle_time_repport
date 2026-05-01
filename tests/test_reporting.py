import csv
import json
from pathlib import Path

from mecademic_cycle_report.analysis import build_run_metrics
from mecademic_cycle_report.checkpoint_spec import CheckpointObservation, ExpectedCheckpoint
from mecademic_cycle_report.config import AppConfig, AnalysisSettings, RobotSettings
from mecademic_cycle_report.reporting import build_report_payload, write_report_artifacts
from mecademic_cycle_report.runner import RunRecord
from mecademic_cycle_report.scenario_matrix import ScenarioProfile


def test_write_report_artifacts_creates_json_and_csv_outputs(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(
            runs=1,
            warmup_runs=0,
            alignment_run=True,
            contingency_percent=20.0,
            output_dir=str(tmp_path),
        ),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800})],
    )
    startup_record = RunRecord(
        scenario=ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800}),
        metrics=build_run_metrics("baseline", 0, ["start"], [1.0], 20.0, measurement_phase="single_run"),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.0)],
        rendered_program_path="rendered/program.mxprog",
        include_in_summary=False,
    )
    accel_record = RunRecord(
        scenario=ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800}),
        metrics=build_run_metrics("baseline", 0, ["start"], [0.9], 20.0, measurement_phase="accel_only"),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.9)],
        rendered_program_path="rendered/program_steady.mxprog",
        include_in_summary=False,
    )
    record = RunRecord(
        scenario=ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800}),
        metrics=build_run_metrics("baseline", 1, ["start"], [0.8], 20.0),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.8)],
        rendered_program_path="rendered/program_steady.mxprog",
    )
    decel_record = RunRecord(
        scenario=ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800}),
        metrics=build_run_metrics("baseline", 0, ["start"], [0.95], 20.0, measurement_phase="decel_only"),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.95)],
        rendered_program_path="rendered/program_steady.mxprog",
        include_in_summary=False,
    )
    variant_record = RunRecord(
        scenario=ScenarioProfile(name="baseline-variables.SPD_INSERT-plus10pct", variables={"SPD_INSERT": 880}),
        metrics=build_run_metrics(
            "baseline-variables.SPD_INSERT-plus10pct",
            1,
            ["start"],
            [1.1],
            20.0,
        ),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.1)],
        rendered_program_path="rendered/program_plus10.mxprog",
    )

    payload = build_report_payload(
        config,
        [startup_record, accel_record, record, decel_record, variant_record],
        program_path="programs/floor_mounted.mxprog",
        referenced_program_variables={"SPD_INSERT"},
        warnings=[],
        robot_runtime={
            "program_load_method": "LoadProgram",
            "ready_status": {
                "simulation_mode": 1,
                "homing_state": True,
                "pause_motion_status": False,
            },
        },
    )
    paths = write_report_artifacts(payload, tmp_path)

    assert Path(paths["json"]).exists()
    assert Path(paths["markdown"]).exists()
    assert Path(paths["records_csv"]).exists()
    assert Path(paths["summary_csv"]).exists()
    assert (tmp_path / "logo.png").exists()
    with Path(paths["records_csv"]).open(encoding="utf-8", newline="") as handle:
        records_rows = list(csv.DictReader(handle))
    with Path(paths["summary_csv"]).open(encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))
    report_json = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))

    assert json.loads(records_rows[0]["applied_variables_json"]) == {"SPD_INSERT": 800}
    assert json.loads(summary_rows[0]["applied_variables_json"]) == {"SPD_INSERT": 800}
    assert report_json["program"]["referenced_variables"] == ["SPD_INSERT"]
    assert report_json["program"]["name"] == "floor_mounted.mxprog"
    assert report_json["records"][0]["applied_inputs"]["variables"]["SPD_INSERT"] == 800
    assert report_json["robot"]["runtime"]["program_load_method"] == "LoadProgram"
    assert report_json["robot"]["runtime"]["ready_status"]["simulation_mode"] == 1
    assert report_json["analysis"]["alignment_run"] is True
    markdown_report = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert "![Mecademic logo](logo.png)" in markdown_report
    assert "# Mecademic Cycle Time Report - floor_mounted.mxprog" in markdown_report
    assert "Startup plus steady-state measurement: `True`" in markdown_report
    assert "In-between steady-state runs summarized per scenario: `1`" in markdown_report
    assert "## Measurement Breakdown" in markdown_report
    assert "- Single run measurement: `1.000s`" in markdown_report
    assert "- First chained cycle (accel-dominant): `0.900s`" in markdown_report
    assert "- Last chained cycle (decel-dominant): `0.950s`" in markdown_report
    assert "- In-between steady-state runs: `1` summarized with avg `0.800s`, min `0.800s`, max `0.800s`" in markdown_report
    assert "## Impact Insights" in markdown_report
    assert "baseline-variables.SPD_INSERT-plus10pct" in markdown_report
    assert "- Applied time scaling: `100%`" in markdown_report
    assert "- Blending:" not in markdown_report
    assert "- Gripper open delay:" not in markdown_report
    assert "- Gripper close delay:" not in markdown_report
    assert "- Rendered program file: `program.mxprog`" in markdown_report
    assert "- Rendered program path: `rendered/program.mxprog`" in markdown_report
    assert "### baseline single run measurement" in markdown_report
    assert "### baseline first chained cycle (accel-dominant)" in markdown_report
    assert "### baseline last chained cycle (decel-dominant)" in markdown_report


def test_write_report_artifacts_preserves_grouped_random_summaries(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(
            runs=1,
            warmup_runs=0,
            alignment_run=False,
            contingency_percent=20.0,
            output_dir=str(tmp_path),
        ),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[
            ScenarioProfile(
                name="baseline-pick_position-random-1",
                analysis_name="baseline-pick_position-random",
                variables={"PICK_X": 10.0, "PICK_Y": -18.0},
            ),
            ScenarioProfile(
                name="baseline-pick_position-random-2",
                analysis_name="baseline-pick_position-random",
                variables={"PICK_X": 11.0, "PICK_Y": -19.0},
            ),
        ],
    )
    records = [
        RunRecord(
            scenario=config.scenarios[0],
            metrics=build_run_metrics("baseline-pick_position-random", 1, ["start"], [1.0], 20.0),
            observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.0)],
            rendered_program_path="rendered/random1.mxprog",
        ),
        RunRecord(
            scenario=config.scenarios[1],
            metrics=build_run_metrics("baseline-pick_position-random", 1, ["start"], [1.2], 20.0),
            observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.2)],
            rendered_program_path="rendered/random2.mxprog",
        ),
    ]

    payload = build_report_payload(config, records, program_path="programs/random_case.mxprog")
    paths = write_report_artifacts(payload, tmp_path)
    summary_rows = list(csv.DictReader(Path(paths["summary_csv"]).open(encoding="utf-8", newline="")))
    markdown_report = Path(paths["markdown"]).read_text(encoding="utf-8")

    assert [row["scenario_name"] for row in summary_rows] == ["baseline-pick_position-random"]
    assert (tmp_path / "logo.png").exists()
    assert "![Mecademic logo](logo.png)" in markdown_report
    assert "### baseline-pick_position-random" in markdown_report
    assert "- Random samples summarized: `2`" in markdown_report
    assert "- Applied time scaling: `100%`" in markdown_report
    assert "`PICK_X` sampled over `10` to `11` (mean `10.5`)" in markdown_report
    assert "baseline-pick_position-random run 1 (baseline-pick_position-random-1)" not in markdown_report
    assert "### baseline-pick_position-random-1" not in markdown_report


def test_write_report_artifacts_renders_measurement_breakdown_without_alignment_when_transients_exist(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(
            runs=1,
            warmup_runs=0,
            alignment_run=False,
            contingency_percent=20.0,
            output_dir=str(tmp_path),
        ),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline", variables={"SPD_INSERT": 150})],
    )
    accel_record = RunRecord(
        scenario=config.scenarios[0],
        metrics=build_run_metrics("baseline", 0, ["start"], [0.9], 20.0, measurement_phase="accel_only"),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.9)],
        rendered_program_path="rendered/program.mxprog",
        include_in_summary=False,
    )
    decel_record = RunRecord(
        scenario=config.scenarios[0],
        metrics=build_run_metrics("baseline", 0, ["start"], [1.1], 20.0, measurement_phase="decel_only"),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.1)],
        rendered_program_path="rendered/program.mxprog",
        include_in_summary=False,
    )
    steady_state_record = RunRecord(
        scenario=config.scenarios[0],
        metrics=build_run_metrics("baseline", 1, ["start"], [1.0], 20.0),
        observations=[CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=1.0)],
        rendered_program_path="rendered/program.mxprog",
    )

    payload = build_report_payload(config, [accel_record, decel_record, steady_state_record])
    paths = write_report_artifacts(payload, tmp_path)
    markdown_report = Path(paths["markdown"]).read_text(encoding="utf-8")

    assert "Startup plus steady-state measurement: `False`" in markdown_report
    assert "## Measurement Breakdown" in markdown_report
    assert "- First chained cycle (accel-dominant): `0.900s`" in markdown_report
    assert "- Last chained cycle (decel-dominant): `1.100s`" in markdown_report
    assert "- In-between steady-state runs: `1` summarized with avg `1.000s`, min `1.000s`, max `1.000s`" in markdown_report