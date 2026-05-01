from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
from typing import Iterable

from .checkpoint_spec import ExpectedCheckpoint, boundary_checkpoint_ids
from .scenario_matrix import ScenarioProfile


class ProgramTemplateError(ValueError):
    """Raised when mxprog template rendering fails."""


PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")
CHECKPOINT_PATTERN = re.compile(r"\bSetCheckpoint\(\s*(\d+)\s*\)")
RUNTIME_PLACEHOLDER_VARIABLE_PREFIX = "MCR_"


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


def _sanitize_runtime_variable_name(key: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_]", "_", key).strip("_")
    sanitized = re.sub(r"_+", "_", sanitized)
    if not sanitized:
        raise ProgramTemplateError(f"Cannot derive runtime variable name from placeholder: {key}")
    return f"{RUNTIME_PLACEHOLDER_VARIABLE_PREFIX}{sanitized.upper()}"


def runtime_placeholder_variable_name(key: str) -> str:
    if key.startswith("variables."):
        return key.split(".", 1)[1]
    return _sanitize_runtime_variable_name(key)


def build_runtime_parameter_variables(scenario: ScenarioProfile) -> dict[str, object]:
    context = build_template_context(scenario)
    runtime_variables = dict(scenario.variables)

    def visit(value: object, path: tuple[str, ...]) -> None:
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                visit(nested_value, (*path, nested_key))
            return
        if not path:
            return
        key = ".".join(path)
        runtime_variables.setdefault(runtime_placeholder_variable_name(key), value)

    visit(context.get("scenario"), ("scenario",))
    for key in (
        "time_scaling_percent",
        "gripper_open_delay_s",
        "gripper_close_delay_s",
        "blending_percent",
    ):
        visit(context.get(key), (key,))
    return runtime_variables


def render_runtime_program_text(template_text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return f"vars.{runtime_placeholder_variable_name(key)}"

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


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


def _remap_checkpoint_ids(rendered_text: str, checkpoint_id_map: dict[int, int]) -> str:
    def replace(match: re.Match[str]) -> str:
        checkpoint_id = int(match.group(1))
        mapped_id = checkpoint_id_map.get(checkpoint_id, checkpoint_id)
        return f"SetCheckpoint({mapped_id})"

    return CHECKPOINT_PATTERN.sub(replace, rendered_text)


def _extract_program_through_checkpoint(rendered_text: str, checkpoint_id: int) -> str:
    checkpoint_match = re.search(
        rf"^.*\bSetCheckpoint\(\s*{checkpoint_id}\s*\).*$",
        rendered_text,
        flags=re.MULTILINE,
    )
    if checkpoint_match is None:
        raise ProgramTemplateError(
            f"Cannot build queued program because checkpoint {checkpoint_id} is missing from the template"
        )
    return rendered_text[: checkpoint_match.end()].rstrip("\n")


def render_repeated_program_file(
    template_path: Path,
    scenario: ScenarioProfile,
    output_dir: Path,
    checkpoints: Iterable[ExpectedCheckpoint],
    cycle_count: int,
    name_suffix: str = "steady_state",
    boundary_pair_start_index: int = 0,
) -> tuple[Path, list[list[ExpectedCheckpoint]]]:
    if cycle_count <= 0:
        raise ProgramTemplateError("cycle_count must be greater than zero")

    configured_checkpoints = list(checkpoints)
    rendered_text = render_program_text(template_path.read_text(encoding="utf-8"), scenario).rstrip("\n")
    max_checkpoint_id = max((checkpoint.checkpoint_id for checkpoint in configured_checkpoints), default=0)
    block_size = max_checkpoint_id + 3

    lines = build_variable_assignment_lines(scenario)
    cycle_checkpoints: list[list[ExpectedCheckpoint]] = []
    for cycle_index in range(1, cycle_count + 1):
        block_offset = (cycle_index - 1) * block_size
        cycle_start_id, cycle_end_id = boundary_checkpoint_ids(
            boundary_pair_start_index + cycle_index - 1
        )
        cycle_start = ExpectedCheckpoint(
            checkpoint_id=cycle_start_id,
            label=f"cycle_{cycle_index}_start",
        )
        mapped_checkpoints = [
            ExpectedCheckpoint(
                checkpoint_id=block_offset + checkpoint.checkpoint_id + 1,
                label=f"cycle_{cycle_index}_{checkpoint.label}",
                timeout_s=checkpoint.timeout_s,
                required=checkpoint.required,
            )
            for checkpoint in configured_checkpoints
        ]
        cycle_end = ExpectedCheckpoint(
            checkpoint_id=cycle_end_id,
            label=f"cycle_{cycle_index}_end",
        )
        checkpoint_id_map = {
            checkpoint.checkpoint_id: mapped_checkpoint.checkpoint_id
            for checkpoint, mapped_checkpoint in zip(
                configured_checkpoints, mapped_checkpoints, strict=True
            )
        }
        lines.append(f"SetCheckpoint({cycle_start.checkpoint_id})")
        if rendered_text:
            lines.append(_remap_checkpoint_ids(rendered_text, checkpoint_id_map))
        lines.append(f"SetCheckpoint({cycle_end.checkpoint_id})")
        cycle_checkpoints.append([cycle_start, *mapped_checkpoints, cycle_end])

    rendered_dir = output_dir / "rendered_programs"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = rendered_dir / f"{template_path.stem}__{scenario.name}__{name_suffix}{template_path.suffix}"
    rendered_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rendered_path, cycle_checkpoints


def render_runtime_repeated_program_file(
    template_path: Path,
    output_dir: Path,
    checkpoints: Iterable[ExpectedCheckpoint],
    cycle_count: int,
    name_suffix: str = "steady_state",
    boundary_pair_start_index: int = 0,
) -> tuple[Path, list[list[ExpectedCheckpoint]]]:
    if cycle_count <= 0:
        raise ProgramTemplateError("cycle_count must be greater than zero")

    configured_checkpoints = list(checkpoints)
    rendered_text = render_runtime_program_text(template_path.read_text(encoding="utf-8")).rstrip("\n")
    max_checkpoint_id = max((checkpoint.checkpoint_id for checkpoint in configured_checkpoints), default=0)
    block_size = max_checkpoint_id + 3

    lines: list[str] = []
    cycle_checkpoints: list[list[ExpectedCheckpoint]] = []
    for cycle_index in range(1, cycle_count + 1):
        block_offset = (cycle_index - 1) * block_size
        cycle_start_id, cycle_end_id = boundary_checkpoint_ids(
            boundary_pair_start_index + cycle_index - 1
        )
        cycle_start = ExpectedCheckpoint(
            checkpoint_id=cycle_start_id,
            label=f"cycle_{cycle_index}_start",
        )
        mapped_checkpoints = [
            ExpectedCheckpoint(
                checkpoint_id=block_offset + checkpoint.checkpoint_id + 1,
                label=f"cycle_{cycle_index}_{checkpoint.label}",
                timeout_s=checkpoint.timeout_s,
                required=checkpoint.required,
            )
            for checkpoint in configured_checkpoints
        ]
        cycle_end = ExpectedCheckpoint(
            checkpoint_id=cycle_end_id,
            label=f"cycle_{cycle_index}_end",
        )
        checkpoint_id_map = {
            checkpoint.checkpoint_id: mapped_checkpoint.checkpoint_id
            for checkpoint, mapped_checkpoint in zip(
                configured_checkpoints, mapped_checkpoints, strict=True
            )
        }
        lines.append(f"SetCheckpoint({cycle_start.checkpoint_id})")
        if rendered_text:
            lines.append(_remap_checkpoint_ids(rendered_text, checkpoint_id_map))
        lines.append(f"SetCheckpoint({cycle_end.checkpoint_id})")
        cycle_checkpoints.append([cycle_start, *mapped_checkpoints, cycle_end])

    rendered_dir = output_dir / "rendered_programs"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = rendered_dir / f"{template_path.stem}__runtime__{name_suffix}{template_path.suffix}"
    rendered_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rendered_path, cycle_checkpoints


def render_runtime_queued_program_file(
    template_path: Path,
    output_dir: Path,
    checkpoints: Iterable[ExpectedCheckpoint],
    steady_state_run_count: int,
    boundary_pair_start_index: int = 0,
) -> tuple[Path, list[list[ExpectedCheckpoint]]]:
    """Render a queued program using StartProgram to invoke the reference program.
    
    This approach avoids duplicating program text and maintains the integrity of
    the reference program by invoking it multiple times via StartProgram().
    """
    if steady_state_run_count <= 0:
        raise ProgramTemplateError("steady_state_run_count must be greater than zero")

    configured_checkpoints = list(checkpoints)
    handoff_index = next(
        (index for index, checkpoint in enumerate(configured_checkpoints) if checkpoint.queue_next_run),
        None,
    )
    if handoff_index is None:
        raise ProgramTemplateError("Queued runtime rendering requires a queue_next_run checkpoint")

    # Reference program that will be invoked via StartProgram
    reference_program_name = f"{template_path.stem}__runtime{template_path.suffix}"
    handoff_checkpoints = configured_checkpoints[: handoff_index + 1]

    lines: list[str] = ["Delay(1.0)"]
    cycle_checkpoints: list[list[ExpectedCheckpoint]] = []
    total_cycle_count = steady_state_run_count + 2
    
    for cycle_index in range(total_cycle_count):
        boundary_start_id, boundary_end_id = boundary_checkpoint_ids(
            boundary_pair_start_index + cycle_index
        )
        is_first_cycle = cycle_index == 0
        is_final_cycle = cycle_index == total_cycle_count - 1
        
        # For non-final cycles, only track checkpoints up to the handoff
        # For final cycle, track all configured checkpoints
        active_checkpoints = configured_checkpoints if is_final_cycle else handoff_checkpoints
        
        cycle_start_label = "program_start" if is_first_cycle else "cycle_start"
        cycle_end_label = "program_end" if is_final_cycle else "cycle_end"
        
        cycle_start_checkpoint = ExpectedCheckpoint(
            checkpoint_id=boundary_start_id,
            label=cycle_start_label,
        )
        cycle_end_checkpoint = ExpectedCheckpoint(
            checkpoint_id=boundary_end_id,
            label=cycle_end_label,
        )
        
        # Reference program checkpoints are not remapped - they appear as-is
        reference_checkpoints = list(active_checkpoints)
        
        # Build program: boundary start -> StartProgram -> boundary end
        lines.append(f"SetCheckpoint({cycle_start_checkpoint.checkpoint_id})")
        lines.append(f"StartProgram({reference_program_name})")
        lines.append(f"SetCheckpoint({cycle_end_checkpoint.checkpoint_id})")
        
        # Track expected checkpoints: boundary markers + reference program's checkpoints
        cycle_checkpoint_list = [cycle_start_checkpoint, *reference_checkpoints, cycle_end_checkpoint]
        cycle_checkpoints.append(cycle_checkpoint_list)

    rendered_dir = output_dir / "rendered_programs"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = rendered_dir / f"{template_path.stem}__runtime__queued{template_path.suffix}"
    rendered_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rendered_path, cycle_checkpoints


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


def render_runtime_program_file(
    template_path: Path,
    output_dir: Path,
    start_checkpoint_id: int | None = None,
    end_checkpoint_id: int | None = None,
) -> Path:
    rendered_text = render_runtime_program_text(template_path.read_text(encoding="utf-8"))
    rendered_text = wrap_program_text(rendered_text, None, start_checkpoint_id, end_checkpoint_id)
    rendered_dir = output_dir / "rendered_programs"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = rendered_dir / f"{template_path.stem}__runtime{template_path.suffix}"
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