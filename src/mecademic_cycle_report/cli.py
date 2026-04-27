from __future__ import annotations

from dataclasses import replace
import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import ConfigError, load_config
from .mxprog_inspection import extract_program_variables, find_missing_scenario_variables
from .program_template import ProgramTemplateError
from .reporting import build_report_payload, render_terminal_summary, write_report_artifacts
from .runner import CycleRunner, RunFailure
from .robot_client import RobotClientError, create_robot_client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mecademic-cycle-report")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-config", help="Validate a config file")
    validate_parser.add_argument("config", help="Path to the YAML or JSON config file")

    analyze_parser = subparsers.add_parser("analyze", help="Run analysis or a dry run")
    analyze_parser.add_argument("mxprog", help="Path to the mxprog program")
    analyze_parser.add_argument("--config", required=True, help="Path to the YAML or JSON config file")
    analyze_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build report data without talking to a robot",
    )
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report payload as JSON",
    )
    sim_override = analyze_parser.add_mutually_exclusive_group()
    sim_override.add_argument(
        "--enforce-sim-mode",
        action="store_true",
        help="Force Mecademic simulation mode before homing and execution, overriding config",
    )
    sim_override.add_argument(
        "--no-enforce-sim-mode",
        action="store_true",
        help="Disable Mecademic simulation mode enforcement for this run, overriding config",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate-config":
            config = load_config(args.config)
            print(
                f"Config valid: {len(config.checkpoints)} checkpoints, {len(config.scenarios)} scenarios"
            )
            return 0

        config = load_config(args.config)
        if args.enforce_sim_mode:
            config = replace(config, robot=replace(config.robot, enforce_sim_mode=True))
        elif args.no_enforce_sim_mode:
            config = replace(config, robot=replace(config.robot, enforce_sim_mode=False))
        if args.dry_run:
            config = config.__class__(
                robot=config.robot,
                analysis=config.analysis.__class__(
                    runs=config.analysis.runs,
                    warmup_runs=config.analysis.warmup_runs,
                    contingency_percent=config.analysis.contingency_percent,
                    output_dir=config.analysis.output_dir,
                    dry_run=True,
                ),
                checkpoints=config.checkpoints,
                scenarios=config.scenarios,
            )

        runner = CycleRunner(
            config=config,
            robot_client=create_robot_client(
                config.robot.address,
                dry_run=config.analysis.dry_run,
                enforce_sim_mode=config.robot.enforce_sim_mode,
            ),
        )
        referenced_program_variables = extract_program_variables(args.mxprog)
        missing_variables = find_missing_scenario_variables(
            referenced_program_variables,
            config.scenarios,
        )
        warnings = [
            (
                f"Scenario {scenario_name} does not define program variables: "
                + ", ".join(variable_names)
            )
            for scenario_name, variable_names in sorted(missing_variables.items())
        ]
        records = runner.execute(Path(args.mxprog))
        payload = build_report_payload(
            config,
            records,
            referenced_program_variables=referenced_program_variables,
            warnings=warnings,
            robot_runtime=runner.robot_client.get_runtime_details(),
        )
        artifact_paths = write_report_artifacts(payload, config.analysis.output_dir)

        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                f"{render_terminal_summary(payload)}\n"
                f"Artifacts: json={artifact_paths['json']}, markdown={artifact_paths['markdown']}"
            )
        return 0
    except (ConfigError, ProgramTemplateError, RobotClientError, RunFailure, FileNotFoundError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
