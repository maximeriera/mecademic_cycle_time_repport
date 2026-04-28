from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .scenario_matrix import ScenarioProfile


VARIABLE_REFERENCE_PATTERN = re.compile(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)\b")
CHECKPOINT_PATTERN = re.compile(r"\bSetCheckpoint\(\s*(\d+)\s*\)")


def extract_program_variables(mxprog_path: str | Path) -> set[str]:
    program_text = Path(mxprog_path).read_text(encoding="utf-8")
    return set(VARIABLE_REFERENCE_PATTERN.findall(program_text))


def extract_program_checkpoint_ids(mxprog_path: str | Path) -> list[int]:
    program_text = Path(mxprog_path).read_text(encoding="utf-8")
    checkpoint_ids: list[int] = []
    seen_ids: set[int] = set()

    for checkpoint_text in CHECKPOINT_PATTERN.findall(program_text):
        checkpoint_id = int(checkpoint_text)
        if checkpoint_id in seen_ids:
            continue
        seen_ids.add(checkpoint_id)
        checkpoint_ids.append(checkpoint_id)

    return checkpoint_ids


def build_scenario_template_payload(
    mxprog_path: str | Path,
    *,
    robot_address: str = "192.168.0.100",
    enforce_sim_mode: bool = True,
    output_root: str = "artifacts",
) -> dict[str, Any]:
    program_path = Path(mxprog_path)
    checkpoint_ids = extract_program_checkpoint_ids(program_path)
    variable_names = sorted(extract_program_variables(program_path))

    checkpoints = [
        {
            "checkpoint_id": checkpoint_id,
            "label": f"checkpoint_{checkpoint_id}",
            "timeout_s": 10.0,
        }
        for checkpoint_id in checkpoint_ids
    ]
    variables = {variable_name: "__TODO__" for variable_name in variable_names}

    return {
        "robot": {
            "address": robot_address,
            "enforce_sim_mode": enforce_sim_mode,
        },
        "analysis": {
            "runs": 1,
            "warmup_runs": 0,
            "alignment_run": True,
            "contingency_percent": 20,
            "output_dir": f"{output_root}/{program_path.stem}",
        },
        "checkpoints": checkpoints,
        "scenarios": {
            "profiles": [
                {
                    "name": "baseline",
                    "variables": variables,
                }
            ]
        },
    }


def find_missing_scenario_variables(
    referenced_variables: set[str],
    scenarios: list[ScenarioProfile],
) -> dict[str, list[str]]:
    if not referenced_variables:
        return {}

    missing_by_scenario: dict[str, list[str]] = {}
    for scenario in scenarios:
        missing = sorted(name for name in referenced_variables if name not in scenario.variables)
        if missing:
            missing_by_scenario[scenario.name] = missing

    return missing_by_scenario