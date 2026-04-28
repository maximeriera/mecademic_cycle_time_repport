from pathlib import Path

import yaml

from mecademic_cycle_report.cli import build_parser, main


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


def test_generate_scenarios_writes_one_config_per_program(tmp_path: Path) -> None:
    programs_dir = tmp_path / "programs"
    output_dir = tmp_path / "configs"
    programs_dir.mkdir()
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