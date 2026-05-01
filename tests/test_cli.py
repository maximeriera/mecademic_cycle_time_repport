from pathlib import Path

import pytest
import yaml

from mecademic_cycle_report.cli import build_parser, main, _derive_generated_analysis_subdir
from mecademic_cycle_report.checkpoint_spec import ExpectedCheckpoint
from mecademic_cycle_report.config import AppConfig, AnalysisSettings, RobotSettings
from mecademic_cycle_report.scenario_matrix import ScenarioProfile


def test_analyze_parser_accepts_enforce_sim_mode_override() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "analyze",
            "program.mxprog",
            "--config",
            "config.yaml",
            "--enforce-sim-mode",
        ]
    )

    assert args.enforce_sim_mode is True
    assert args.no_enforce_sim_mode is False


def test_analyze_parser_accepts_no_enforce_sim_mode_override() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "analyze",
            "program.mxprog",
            "--config",
            "config.yaml",
            "--no-enforce-sim-mode",
        ]
    )

    assert args.enforce_sim_mode is False
    assert args.no_enforce_sim_mode is True


def test_generate_scenarios_parser_accepts_folder_and_output_dir() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "generate-scenarios",
            "programs",
            "--output-dir",
            "configs",
        ]
    )

    assert args.mxprog_dir == "programs"
    assert args.output_dir == "configs"


def test_derive_generated_analysis_subdir_drops_configs_prefix() -> None:
    assert _derive_generated_analysis_subdir(Path("configs/generated")) == "generated"
    assert _derive_generated_analysis_subdir(Path("generated-scenarios")) == "generated-scenarios"
    assert _derive_generated_analysis_subdir(Path("configs")) == ""


def test_generate_scenarios_writes_one_config_per_program(tmp_path: Path) -> None:
    programs_dir = tmp_path / "programs"
    output_dir = tmp_path / "configs" / "generated"
    programs_dir.mkdir()
    output_dir.mkdir(parents=True)
    (programs_dir / "alpha.mxprog").write_text(
        "SetCheckpoint(1)\nMovePose(vars.PICK_X, vars.PICK_Y, 0, 0, 0, 0)\nSetCheckpoint(2)\n",
        encoding="utf-8",
    )
    (programs_dir / "beta.mxprog").write_text(
        "SetCheckpoint(10)\nSetCartLinVel(vars.SPD_INSERT)\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "generate-scenarios",
            str(programs_dir),
            "--output-dir",
            str(output_dir),
            "--robot-address",
            "10.0.0.50",
            "--no-enforce-sim-mode",
            "--analysis-output-root",
            "artifacts/generated",
        ]
    )

    assert exit_code == 0
    alpha_payload = yaml.safe_load((output_dir / "alpha.scenarios.yaml").read_text(encoding="utf-8"))
    beta_payload = yaml.safe_load((output_dir / "beta.scenarios.yaml").read_text(encoding="utf-8"))

    assert alpha_payload["robot"] == {"address": "10.0.0.50", "enforce_sim_mode": False}
    assert alpha_payload["analysis"]["output_dir"] == "artifacts/generated/alpha"
    assert [item["checkpoint_id"] for item in alpha_payload["checkpoints"]] == [1, 2]
    assert alpha_payload["scenarios"]["profiles"][0]["variables"] == {
        "PICK_X": "__TODO__",
        "PICK_Y": "__TODO__",
    }

    assert beta_payload["analysis"]["output_dir"] == "artifacts/generated/beta"
    assert [item["checkpoint_id"] for item in beta_payload["checkpoints"]] == [10]
    assert beta_payload["scenarios"]["profiles"][0]["variables"] == {
        "SPD_INSERT": "__TODO__",
    }


@pytest.mark.parametrize(
    ("flag", "initial_value", "expected_value"),
    [
        ("--enforce-sim-mode", False, True),
        ("--no-enforce-sim-mode", True, False),
    ],
)
def test_analyze_main_overrides_enforce_sim_mode(monkeypatch: pytest.MonkeyPatch, flag: str, initial_value: bool, expected_value: bool) -> None:
    base_config = AppConfig(
        robot=RobotSettings(address="192.168.0.10", enforce_sim_mode=initial_value),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, output_dir="artifacts/test-output"),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    captured: dict[str, object] = {}

    class FakeRobotClient:
        def get_runtime_details(self) -> dict[str, str]:
            return {"mode": "fake"}

    class FakeRunner:
        def __init__(self, config: AppConfig, robot_client: FakeRobotClient) -> None:
            captured["runner_config"] = config
            self.robot_client = robot_client

        def execute(self, mxprog_path: Path) -> list[object]:
            captured["mxprog_path"] = mxprog_path
            return []

    def fake_create_robot_client(address: str, dry_run: bool, enforce_sim_mode: bool) -> FakeRobotClient:
        captured["create_robot_client"] = {
            "address": address,
            "dry_run": dry_run,
            "enforce_sim_mode": enforce_sim_mode,
        }
        return FakeRobotClient()

    monkeypatch.setattr("mecademic_cycle_report.cli.load_config", lambda path: base_config)
    monkeypatch.setattr("mecademic_cycle_report.cli.create_robot_client", fake_create_robot_client)
    monkeypatch.setattr("mecademic_cycle_report.cli.CycleRunner", FakeRunner)
    monkeypatch.setattr("mecademic_cycle_report.cli.extract_program_variables", lambda path: set())
    monkeypatch.setattr("mecademic_cycle_report.cli.find_missing_scenario_variables", lambda variables, scenarios: {})
    monkeypatch.setattr(
        "mecademic_cycle_report.cli.build_report_payload",
        lambda config, records, program_path, referenced_program_variables, warnings, robot_runtime: {
            "config_enforce_sim_mode": config.robot.enforce_sim_mode,
            "warnings": warnings,
            "robot_runtime": robot_runtime,
        },
    )
    monkeypatch.setattr(
        "mecademic_cycle_report.cli.write_report_artifacts",
        lambda payload, output_dir: {"json": "report.json", "markdown": "report.md"},
    )
    monkeypatch.setattr("mecademic_cycle_report.cli.render_terminal_summary", lambda payload: "ok")

    exit_code = main(["analyze", "program.mxprog", "--config", "config.yaml", flag])

    assert exit_code == 0
    assert captured["create_robot_client"] == {
        "address": "192.168.0.10",
        "dry_run": False,
        "enforce_sim_mode": expected_value,
    }
    runner_config = captured["runner_config"]
    assert isinstance(runner_config, AppConfig)
    assert runner_config.robot.enforce_sim_mode is expected_value
    assert captured["mxprog_path"] == Path("program.mxprog")


def test_analyze_main_dry_run_preserves_alignment_run(monkeypatch: pytest.MonkeyPatch) -> None:
    base_config = AppConfig(
        robot=RobotSettings(address="192.168.0.10", enforce_sim_mode=True),
        analysis=AnalysisSettings(
            runs=1,
            warmup_runs=0,
            alignment_run=False,
            output_dir="artifacts/test-output",
            dry_run=False,
        ),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    captured: dict[str, object] = {}

    class FakeRobotClient:
        def get_runtime_details(self) -> dict[str, str]:
            return {"mode": "fake"}

    class FakeRunner:
        def __init__(self, config: AppConfig, robot_client: FakeRobotClient) -> None:
            captured["runner_config"] = config
            self.robot_client = robot_client

        def execute(self, mxprog_path: Path) -> list[object]:
            return []

    monkeypatch.setattr("mecademic_cycle_report.cli.load_config", lambda path: base_config)
    monkeypatch.setattr(
        "mecademic_cycle_report.cli.create_robot_client",
        lambda address, dry_run, enforce_sim_mode: FakeRobotClient(),
    )
    monkeypatch.setattr("mecademic_cycle_report.cli.CycleRunner", FakeRunner)
    monkeypatch.setattr("mecademic_cycle_report.cli.extract_program_variables", lambda path: set())
    monkeypatch.setattr("mecademic_cycle_report.cli.find_missing_scenario_variables", lambda variables, scenarios: {})
    monkeypatch.setattr(
        "mecademic_cycle_report.cli.build_report_payload",
        lambda config, records, program_path, referenced_program_variables, warnings, robot_runtime: {},
    )
    monkeypatch.setattr(
        "mecademic_cycle_report.cli.write_report_artifacts",
        lambda payload, output_dir: {"json": "report.json", "markdown": "report.md"},
    )
    monkeypatch.setattr("mecademic_cycle_report.cli.render_terminal_summary", lambda payload: "ok")

    exit_code = main(["analyze", "program.mxprog", "--config", "config.yaml", "--dry-run"])

    assert exit_code == 0
    runner_config = captured["runner_config"]
    assert isinstance(runner_config, AppConfig)
    assert runner_config.analysis.dry_run is True
    assert runner_config.analysis.alignment_run is False
