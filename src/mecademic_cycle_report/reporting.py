from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .analysis import compare_scenarios
from .config import AppConfig
from .runner import RunRecord
from .scenario_matrix import scenario_runtime_inputs


REPORT_LOGO_FILENAME = "logo.png"
REPORT_LOGO_SOURCE = Path(__file__).resolve().parent / "assets" / REPORT_LOGO_FILENAME


def _format_scalar_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _group_scenarios_by_analysis_name(payload: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for scenario in payload["scenarios"]:
        grouped.setdefault(scenario["applied_inputs"]["analysis_name"], []).append(scenario)
    return list(grouped.items())


def _append_grouped_variable_inputs(lines: list[str], scenarios: list[dict[str, Any]]) -> None:
    variable_names = sorted(
        {
            variable_name
            for scenario in scenarios
            for variable_name in scenario["applied_inputs"]["variables"]
        }
    )
    if not variable_names:
        lines.append("- Variables: none")
        return

    lines.append("- Variables:")
    for variable_name in variable_names:
        values = [
            scenario["applied_inputs"]["variables"][variable_name]
            for scenario in scenarios
            if variable_name in scenario["applied_inputs"]["variables"]
        ]
        unique_values = list(dict.fromkeys(values))
        if len(unique_values) == 1:
            lines.append(f"  - `{variable_name}` = `{_format_scalar_value(unique_values[0])}`")
            continue
        if all(isinstance(value, (int, float)) for value in values):
            minimum = min(values)
            maximum = max(values)
            mean = sum(float(value) for value in values) / len(values)
            lines.append(
                "  - "
                f"`{variable_name}` sampled over `{_format_scalar_value(minimum)}` to `{_format_scalar_value(maximum)}` "
                f"(mean `{_format_scalar_value(mean)}`)"
            )
            continue
        formatted_values = ", ".join(f"`{_format_scalar_value(value)}`" for value in unique_values)
        lines.append(f"  - `{variable_name}` sampled values: {formatted_values}")


def _effective_time_scaling_percent(applied_inputs: dict[str, Any]) -> float:
    time_scaling = applied_inputs.get("time_scaling_percent")
    return 100.0 if time_scaling is None else float(time_scaling)


def build_report_payload(
    config: AppConfig,
    records: list[RunRecord],
    *,
    program_path: str | None = None,
    referenced_program_variables: set[str] | None = None,
    warnings: list[str] | None = None,
    robot_runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runs_by_scenario: dict[str, list] = {}
    for record in records:
        runs_by_scenario.setdefault(record.metrics.scenario_name, []).append(record.metrics)

    scenario_inputs = {
        scenario.name: scenario_runtime_inputs(scenario) for scenario in config.scenarios
    }
    for record in records:
        scenario_inputs.setdefault(record.scenario.name, scenario_runtime_inputs(record.scenario))

    return {
        "analysis": {
            "runs": config.analysis.runs,
            "warmup_runs": config.analysis.warmup_runs,
            "alignment_run": config.analysis.alignment_run,
            "contingency_percent": config.analysis.contingency_percent,
            "dry_run": config.analysis.dry_run,
        },
        "robot": {
            "address": config.robot.address,
            "enforce_sim_mode": config.robot.enforce_sim_mode,
            "runtime": robot_runtime or {},
        },
        "checkpoints": [asdict(checkpoint) for checkpoint in config.checkpoints],
        "scenarios": [
            {
                **asdict(scenario),
                "applied_inputs": scenario_inputs[scenario.name],
            }
            for scenario in config.scenarios
        ],
        "program": {
            "path": program_path,
            "name": Path(program_path).name if program_path else None,
            "referenced_variables": sorted(referenced_program_variables or []),
        },
        "warnings": warnings or [],
        "records": [
            {
                "scenario_name": record.scenario.name,
                "scenario": asdict(record.scenario),
                "applied_inputs": scenario_inputs[record.scenario.name],
                "metrics": asdict(record.metrics),
                "observations": [asdict(observation) for observation in record.observations],
                "rendered_program_path": record.rendered_program_path,
            }
            for record in records
        ],
        "scenario_comparison": compare_scenarios(
            runs_by_scenario, config.analysis.contingency_percent
        ),
    }


def render_terminal_summary(payload: dict[str, Any]) -> str:
    lines = [
        "Mecademic Cycle Report",
        f"Robot: {payload['robot']['address']}",
        f"Configured scenarios: {len(payload['scenarios'])}",
        f"Measured records: {len(payload['records'])}",
    ]

    runtime = payload["robot"].get("runtime", {})
    if runtime.get("program_load_method"):
        lines.append(f"Program load method: {runtime['program_load_method']}")
    if runtime.get("ready_status") is not None:
        ready_status = runtime["ready_status"]
        lines.append(
            "Robot ready state: "
            f"sim={ready_status['simulation_mode']}, homed={ready_status['homing_state']}, "
            f"paused={ready_status['pause_motion_status']}"
        )
    if payload["analysis"].get("alignment_run"):
        lines.append("Alignment run: enabled")

    if payload["program"].get("referenced_variables"):
        lines.append(
            "Program variables: " + ", ".join(payload["program"]["referenced_variables"])
        )

    if payload.get("warnings"):
        lines.append("Warnings:")
        for warning in payload["warnings"]:
            lines.append(f"- {warning}")

    for scenario_name, stats in payload["scenario_comparison"].items():
        lines.append(
            (
                f"- {scenario_name}: avg={stats['average_s']:.3f}s, min={stats['minimum_s']:.3f}s, "
                f"max={stats['maximum_s']:.3f}s, contingency={stats['contingency_adjusted_average_s']:.3f}s"
            )
        )

    return "\n".join(lines)


def render_markdown_report(payload: dict[str, Any]) -> str:
    program_name = payload["program"].get("name")
    lines = [
        f"![Mecademic logo]({REPORT_LOGO_FILENAME})",
        "",
        "# Mecademic Cycle Time Report"
        + (f" - {program_name}" if program_name else ""),
        "",
        "## Overview",
        "",
        f"- Robot address: `{payload['robot']['address']}`",
        f"- Dry run: `{payload['analysis']['dry_run']}`",
        f"- Alignment run before measurement: `{payload['analysis']['alignment_run']}`",
        f"- Warmup runs per scenario: `{payload['analysis']['warmup_runs']}`",
        f"- Measured runs per scenario: `{payload['analysis']['runs']}`",
        f"- Contingency percent: `{payload['analysis']['contingency_percent']}`",
    ]

    runtime = payload["robot"].get("runtime", {})
    if runtime:
        lines.extend(
            [
                "",
                "## Robot Runtime",
                "",
                f"- Enforce sim mode: `{payload['robot']['enforce_sim_mode']}`",
                f"- Program load method: `{runtime.get('program_load_method', 'n/a')}`",
                f"- Deactivated for sim: `{runtime.get('deactivated_for_sim', False)}`",
            ]
        )
        ready_status = runtime.get("ready_status")
        if ready_status:
            lines.extend(
                [
                    f"- Ready status: sim=`{ready_status['simulation_mode']}`, homed=`{ready_status['homing_state']}`, paused=`{ready_status['pause_motion_status']}`",
                ]
            )

    if payload["program"].get("referenced_variables"):
        lines.extend(
            [
                "",
                "## Program Variables",
                "",
                ", ".join(f"`{name}`" for name in payload["program"]["referenced_variables"]),
            ]
        )

    if payload.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for warning in payload["warnings"]:
            lines.append(f"- {warning}")

    lines.extend(["", "## Scenario Summary", "", "| Scenario | Avg (s) | Min (s) | Max (s) | Std Dev (s) | Contingency Avg (s) |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for scenario_name, stats in payload["scenario_comparison"].items():
        lines.append(
            f"| {scenario_name} | {stats['average_s']:.3f} | {stats['minimum_s']:.3f} | {stats['maximum_s']:.3f} | {stats['std_dev_s']:.3f} | {stats['contingency_adjusted_average_s']:.3f} |"
        )

    if "baseline" in payload["scenario_comparison"]:
        baseline_avg = payload["scenario_comparison"]["baseline"]["average_s"]
        insight_lines: list[str] = []
        for scenario_name, stats in payload["scenario_comparison"].items():
            if scenario_name == "baseline":
                continue
            delta_s = stats["average_s"] - baseline_avg
            delta_pct = 0.0 if baseline_avg == 0 else (delta_s / baseline_avg) * 100.0
            direction = "increase" if delta_s >= 0 else "decrease"
            insight_lines.append(
                f"- `{scenario_name}` shifts average cycle time by `{abs(delta_s):.3f}s` ({abs(delta_pct):.1f}% {direction}) relative to `baseline`."
            )
        if insight_lines:
            lines.extend(["", "## Impact Insights", "", *insight_lines])

    lines.extend(["", "## Scenario Inputs", ""])
    for analysis_name, scenarios in _group_scenarios_by_analysis_name(payload):
        representative = scenarios[0]
        lines.append(f"### {analysis_name}")
        lines.append("")
        if len(scenarios) > 1:
            lines.append(f"- Random samples summarized: `{len(scenarios)}`")
        lines.append(
            f"- Applied time scaling: `{_format_scalar_value(_effective_time_scaling_percent(representative['applied_inputs']))}%`"
        )
        _append_grouped_variable_inputs(lines, scenarios)
        lines.append("")

    lines.extend(["## Measured Runs", ""])
    for record in payload["records"]:
        if record["scenario_name"] != record["metrics"]["scenario_name"]:
            continue
        heading = f"### {record['metrics']['scenario_name']} run {record['metrics']['run_index']}"
        lines.append(heading)
        lines.append("")
        lines.append(f"- Total cycle time: `{record['metrics']['total_cycle_s']:.3f}s`")
        rendered_program = Path(record["rendered_program_path"])
        lines.append(f"- Rendered program file: `{rendered_program.name}`")
        lines.append(f"- Rendered program path: `{record['rendered_program_path']}`")
        lines.append("")
        lines.append("| Checkpoint | Elapsed (s) | Status |")
        lines.append("| --- | ---: | --- |")
        for observation in record["observations"]:
            lines.append(
                f"| {observation['label'] or observation['checkpoint_id']} | {observation['elapsed_s']:.3f} | {observation['status']} |"
            )
        lines.append("")

    return "\n".join(lines)


def write_report_artifacts(payload: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    if REPORT_LOGO_SOURCE.exists():
        (base_dir / REPORT_LOGO_FILENAME).write_bytes(REPORT_LOGO_SOURCE.read_bytes())

    json_path = base_dir / "report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown_path = base_dir / "report.md"
    markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")

    records_csv_path = base_dir / "records.csv"
    with records_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_name",
                "run_index",
                "total_cycle_s",
                "failed",
                "failure_reason",
                "applied_variables_json",
                "rendered_program_path",
            ],
        )
        writer.writeheader()
        for record in payload["records"]:
            writer.writerow(
                {
                    "scenario_name": record["metrics"]["scenario_name"],
                    "run_index": record["metrics"]["run_index"],
                    "total_cycle_s": record["metrics"]["total_cycle_s"],
                    "failed": record["metrics"]["failed"],
                    "failure_reason": record["metrics"]["failure_reason"],
                    "applied_variables_json": json.dumps(
                        record["applied_inputs"]["variables"], sort_keys=True
                    ),
                    "rendered_program_path": record["rendered_program_path"],
                }
            )

    summary_csv_path = base_dir / "scenario_summary.csv"
    with summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_name",
                "applied_variables_json",
                "minimum_s",
                "average_s",
                "maximum_s",
                "std_dev_s",
                "contingency_adjusted_average_s",
            ],
        )
        writer.writeheader()
        for scenario_name, stats in payload["scenario_comparison"].items():
            scenario_entry = next(
                (
                    scenario
                    for scenario in payload["scenarios"]
                    if scenario["name"] == scenario_name
                ),
                next(
                    record
                    for record in payload["records"]
                    if record["metrics"]["scenario_name"] == scenario_name
                ),
            )
            writer.writerow(
                {
                    "scenario_name": scenario_name,
                    "applied_variables_json": json.dumps(
                        scenario_entry["applied_inputs"]["variables"], sort_keys=True
                    ),
                    **stats,
                }
            )

    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "records_csv": str(records_csv_path),
        "summary_csv": str(summary_csv_path),
    }
