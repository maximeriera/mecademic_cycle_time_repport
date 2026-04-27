from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re

from .scenario_matrix import ScenarioProfile


class ProgramTemplateError(ValueError):
    """Raised when mxprog template rendering fails."""


PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def build_template_context(scenario: ScenarioProfile) -> dict[str, object]:
    scenario_dict = asdict(scenario)
    variables = dict(scenario.variables)
    context = {
        "scenario": scenario_dict,
        "time_scaling_percent": 100.0 if scenario.time_scaling_percent is None else scenario.time_scaling_percent,
        "gripper_open_delay_s": scenario.gripper_open_delay_s,
        "gripper_close_delay_s": scenario.gripper_close_delay_s,
        "blending_percent": scenario.blending_percent,
        "variables": variables,
    }
    context.update(variables)
    return context


def render_program_text(template_text: str, scenario: ScenarioProfile) -> str:
    context = build_template_context(scenario)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = resolve_placeholder(context, key)
        return stringify_placeholder(value, key)

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def build_variable_assignment_lines(scenario: ScenarioProfile) -> list[str]:
    return [
        f"SetVariable({variable_name}, {json.dumps(value)})"
        for variable_name, value in scenario.variables.items()
    ]


def wrap_program_text(
    rendered_text: str,
    scenario: ScenarioProfile | None = None,
    start_checkpoint_id: int | None = None,
    end_checkpoint_id: int | None = None,
) -> str:
    lines: list[str] = []
    if scenario is not None:
        lines.extend(build_variable_assignment_lines(scenario))
    if start_checkpoint_id is not None:
        lines.append(f"SetCheckpoint({start_checkpoint_id})")
    if rendered_text:
        lines.append(rendered_text.rstrip("\n"))
    if end_checkpoint_id is not None:
        lines.append(f"SetCheckpoint({end_checkpoint_id})")
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def render_program_file(
    template_path: Path,
    scenario: ScenarioProfile,
    output_dir: Path,
    start_checkpoint_id: int | None = None,
    end_checkpoint_id: int | None = None,
) -> Path:
    rendered_text = render_program_text(template_path.read_text(encoding="utf-8"), scenario)
    rendered_text = wrap_program_text(rendered_text, scenario, start_checkpoint_id, end_checkpoint_id)
    rendered_dir = output_dir / "rendered_programs"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = rendered_dir / f"{template_path.stem}__{scenario.name}{template_path.suffix}"
    rendered_path.write_text(rendered_text, encoding="utf-8")
    return rendered_path


def resolve_placeholder(context: dict[str, object], key: str) -> object:
    current: object = context
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise ProgramTemplateError(f"Unknown template placeholder: {key}")
    return current


def stringify_placeholder(value: object, key: str) -> str:
    if value is None:
        raise ProgramTemplateError(f"Template placeholder resolved to None: {key}")
    return str(value)