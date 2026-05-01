from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import yaml

from .checkpoint_spec import ExpectedCheckpoint, validate_expected_checkpoints
from .scenario_matrix import (
    ScenarioProfile,
    VariableCaseDefinition,
    VariableCasePlan,
    expand_scenarios,
    validate_scenario,
)


class ConfigError(ValueError):
    """Raised when configuration cannot be loaded or validated."""


@dataclass(frozen=True, slots=True)
class RobotSettings:
    address: str
    enforce_sim_mode: bool = True


@dataclass(frozen=True, slots=True)
class AnalysisSettings:
    runs: int = 5
    warmup_runs: int = 1
    alignment_run: bool = True
    contingency_percent: float = 20.0
    output_dir: str = "artifacts"
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class AppConfig:
    robot: RobotSettings
    analysis: AnalysisSettings
    checkpoints: list[ExpectedCheckpoint]
    scenarios: list[ScenarioProfile]


def _parse_variable_case_plan(item: dict[str, Any]) -> VariableCasePlan:
    variables_payload = item.get("variables")
    if not isinstance(variables_payload, dict) or not variables_payload:
        raise ConfigError("scenarios.variable_cases[].variables must be a non-empty mapping")

    variables: dict[str, VariableCaseDefinition] = {}
    for variable_name, definition in variables_payload.items():
        if not isinstance(definition, dict):
            raise ConfigError(
                "scenarios.variable_cases[].variables entries must be mappings"
            )
        variables[str(variable_name)] = VariableCaseDefinition(
            minimum=(
                int(definition["minimum"])
                if isinstance(definition.get("minimum"), int)
                else float(definition["minimum"])
                if definition.get("minimum") is not None
                else None
            ),
            maximum=(
                int(definition["maximum"])
                if isinstance(definition.get("maximum"), int)
                else float(definition["maximum"])
                if definition.get("maximum") is not None
                else None
            ),
            best=(
                int(definition["best"])
                if isinstance(definition.get("best"), int)
                else float(definition["best"])
                if definition.get("best") is not None
                else None
            ),
            worst=(
                int(definition["worst"])
                if isinstance(definition.get("worst"), int)
                else float(definition["worst"])
                if definition.get("worst") is not None
                else None
            ),
        )

    include = item.get("include", ["best", "worst"])
    if not isinstance(include, list):
        raise ConfigError("scenarios.variable_cases[].include must be a list")

    return VariableCasePlan(
        name=str(item["name"]),
        variables=variables,
        include=tuple(str(case_name) for case_name in include),
        random_runs=int(item.get("random_runs", 0)),
        random_seed=(
            int(item["random_seed"]) if item.get("random_seed") is not None else None
        ),
        continuous_random_cycle=bool(item.get("continuous_random_cycle", False)),
    )


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Configuration file does not exist: {config_path}")

    raw_text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(raw_text)
    else:
        payload = yaml.safe_load(raw_text)

    if not isinstance(payload, dict):
        raise ConfigError("Configuration root must be a mapping")

    return parse_config(payload)


def parse_config(payload: dict[str, Any]) -> AppConfig:
    try:
        robot = RobotSettings(
            address=str(payload["robot"]["address"]),
            enforce_sim_mode=bool(payload["robot"].get("enforce_sim_mode", True)),
        )
    except KeyError as exc:
        raise ConfigError(f"Missing robot configuration key: {exc}") from exc

    analysis_payload = payload.get("analysis", {})
    analysis = AnalysisSettings(
        runs=int(analysis_payload.get("runs", 5)),
        warmup_runs=int(analysis_payload.get("warmup_runs", 1)),
        alignment_run=bool(analysis_payload.get("alignment_run", True)),
        contingency_percent=float(analysis_payload.get("contingency_percent", 20.0)),
        output_dir=str(analysis_payload.get("output_dir", "artifacts")),
        dry_run=bool(analysis_payload.get("dry_run", False)),
    )
    if analysis.runs <= 0:
        raise ConfigError("analysis.runs must be greater than zero")
    if analysis.warmup_runs < 0:
        raise ConfigError("analysis.warmup_runs cannot be negative")
    if analysis.contingency_percent < 0:
        raise ConfigError("analysis.contingency_percent cannot be negative")

    checkpoint_payload = payload.get("checkpoints")
    if checkpoint_payload is None:
        checkpoint_payload = []
    if not isinstance(checkpoint_payload, list):
        raise ConfigError("checkpoints must be a list")

    checkpoints = validate_expected_checkpoints(
        ExpectedCheckpoint(
            checkpoint_id=int(item["checkpoint_id"]),
            label=str(item["label"]),
            timeout_s=float(item["timeout_s"]) if item.get("timeout_s") is not None else None,
            required=bool(item.get("required", True)),
            queue_next_run=bool(item.get("queue_next_run", False)),
        )
        for item in checkpoint_payload
    )

    scenario_entries = payload.get("scenarios", {}).get("profiles", [])
    profiles = [
        validate_scenario(
            ScenarioProfile(
                name=str(item["name"]),
                time_scaling_percent=(
                    float(item["time_scaling_percent"])
                    if item.get("time_scaling_percent") is not None
                    else None
                ),
                gripper_open_delay_s=float(item.get("gripper_open_delay_s", 0.0)),
                gripper_close_delay_s=float(item.get("gripper_close_delay_s", 0.0)),
                blending_percent=(
                    float(item["blending_percent"])
                    if item.get("blending_percent") is not None
                    else None
                ),
                variables=dict(item.get("variables", {})),
            )
        )
        for item in scenario_entries
    ]
    sweep = payload.get("scenarios", {}).get("sweep")
    perturbations = payload.get("scenarios", {}).get("perturbations")
    variable_case_entries = payload.get("scenarios", {}).get("variable_cases", [])
    if not isinstance(variable_case_entries, list):
        raise ConfigError("scenarios.variable_cases must be a list")
    variable_cases = [_parse_variable_case_plan(item) for item in variable_case_entries]

    scenarios = expand_scenarios(profiles, sweep, perturbations, variable_cases)
    if not scenarios:
        scenarios = [ScenarioProfile(name="default")]

    return AppConfig(
        robot=robot,
        analysis=analysis,
        checkpoints=checkpoints,
        scenarios=scenarios,
    )
