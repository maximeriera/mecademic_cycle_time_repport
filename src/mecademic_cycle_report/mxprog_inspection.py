from __future__ import annotations

from pathlib import Path
import re

from .scenario_matrix import ScenarioProfile


VARIABLE_REFERENCE_PATTERN = re.compile(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)\b")


def extract_program_variables(mxprog_path: str | Path) -> set[str]:
    program_text = Path(mxprog_path).read_text(encoding="utf-8")
    return set(VARIABLE_REFERENCE_PATTERN.findall(program_text))


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