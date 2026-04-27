from __future__ import annotations

from dataclasses import dataclass, field, replace
from itertools import product
import random
import re
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ScenarioProfile:
    """Runtime parameters applied before a program run."""

    name: str
    analysis_name: str | None = None
    pre_run_group: str | None = None
    skip_repeated_pre_run_cycles: bool = False
    time_scaling_percent: float | None = None
    gripper_open_delay_s: float = 0.0
    gripper_close_delay_s: float = 0.0
    blending_percent: float | None = None
    variables: dict[str, float | int | str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VariableCaseDefinition:
    minimum: float | int | None = None
    maximum: float | int | None = None
    best: float | int | None = None
    worst: float | int | None = None


@dataclass(frozen=True, slots=True)
class VariableCasePlan:
    name: str
    variables: dict[str, VariableCaseDefinition]
    include: tuple[str, ...] = ("best", "worst")
    random_runs: int = 0
    random_seed: int | None = None
    continuous_random_cycle: bool = False


class ScenarioValidationError(ValueError):
    """Raised when a scenario profile or sweep is invalid."""


SUPPORTED_AXES = {
    "time_scaling_percent",
    "gripper_open_delay_s",
    "gripper_close_delay_s",
    "blending_percent",
}

VARIABLE_AXIS_PREFIX = "variables."

VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_scenario(profile: ScenarioProfile) -> ScenarioProfile:
    if not profile.name.strip():
        raise ScenarioValidationError("Scenario name cannot be empty")
    if profile.time_scaling_percent is not None and not 0 < profile.time_scaling_percent <= 100:
        raise ScenarioValidationError("time_scaling_percent must be within (0, 100]")
    if profile.blending_percent is not None and not 0 <= profile.blending_percent <= 100:
        raise ScenarioValidationError("blending_percent must be within [0, 100]")
    if profile.gripper_open_delay_s < 0 or profile.gripper_close_delay_s < 0:
        raise ScenarioValidationError("Gripper delay values cannot be negative")
    invalid_variable_names = [
        name for name in profile.variables if not VARIABLE_NAME_PATTERN.match(name)
    ]
    if invalid_variable_names:
        raise ScenarioValidationError(
            "Scenario variable names must match Mecademic vars.NAME rules: "
            + ", ".join(sorted(invalid_variable_names))
        )
    return profile


def validate_variable_case_plan(plan: VariableCasePlan) -> VariableCasePlan:
    if not plan.name.strip():
        raise ScenarioValidationError("Variable case plan name cannot be empty")
    if not plan.variables:
        raise ScenarioValidationError("Variable case plan must define at least one variable")
    invalid_case_names = [name for name in plan.variables if not VARIABLE_NAME_PATTERN.match(name)]
    if invalid_case_names:
        raise ScenarioValidationError(
            "Scenario variable names must match Mecademic vars.NAME rules: "
            + ", ".join(sorted(invalid_case_names))
        )
    invalid_include = sorted(set(plan.include) - {"best", "worst"})
    if invalid_include:
        raise ScenarioValidationError(
            f"Unsupported variable case include values: {', '.join(invalid_include)}"
        )
    if plan.random_runs < 0:
        raise ScenarioValidationError("Variable case random_runs cannot be negative")
    for variable_name, case_definition in plan.variables.items():
        if case_definition.minimum is not None and case_definition.maximum is not None:
            if float(case_definition.minimum) > float(case_definition.maximum):
                raise ScenarioValidationError(
                    f"Variable case {variable_name} minimum cannot exceed maximum"
                )
        for case_name in plan.include:
            case_value = getattr(case_definition, case_name)
            if case_value is None:
                raise ScenarioValidationError(
                    f"Variable case {variable_name} must define {case_name}"
                )
        if plan.random_runs > 0 and (
            case_definition.minimum is None or case_definition.maximum is None
        ):
            raise ScenarioValidationError(
                f"Variable case {variable_name} must define minimum and maximum for random runs"
            )
    return plan


def scenario_runtime_inputs(profile: ScenarioProfile) -> dict[str, object]:
    return {
        "analysis_name": profile.analysis_name or profile.name,
        "pre_run_group": profile.pre_run_group,
        "skip_repeated_pre_run_cycles": profile.skip_repeated_pre_run_cycles,
        "time_scaling_percent": profile.time_scaling_percent,
        "gripper_open_delay_s": profile.gripper_open_delay_s,
        "gripper_close_delay_s": profile.gripper_close_delay_s,
        "blending_percent": profile.blending_percent,
        "variables": dict(sorted(profile.variables.items())),
    }


def _validate_variable_name(variable_name: str) -> str:
    if not VARIABLE_NAME_PATTERN.match(variable_name):
        raise ScenarioValidationError(
            f"Scenario variable names must match Mecademic vars.NAME rules: {variable_name}"
        )
    return variable_name


def _split_sweep_axes(
    sweep: dict[str, list[float | int | str]],
) -> tuple[list[tuple[str, list[float | int | str]]], list[tuple[str, list[float | int | str]]]]:
    top_level_axes: list[tuple[str, list[float | int | str]]] = []
    variable_axes: list[tuple[str, list[float | int | str]]] = []
    invalid_axes: list[str] = []

    for axis_name, values in sweep.items():
        if axis_name in SUPPORTED_AXES:
            top_level_axes.append((axis_name, values))
            continue
        if axis_name.startswith(VARIABLE_AXIS_PREFIX):
            variable_name = _validate_variable_name(axis_name[len(VARIABLE_AXIS_PREFIX) :])
            variable_axes.append((variable_name, values))
            continue
        invalid_axes.append(axis_name)

    if invalid_axes:
        raise ScenarioValidationError(
            f"Unsupported sweep axes: {', '.join(sorted(invalid_axes))}"
        )

    return top_level_axes, variable_axes


def _apply_sweep_overrides(
    base_profile: ScenarioProfile,
    top_level_overrides: dict[str, float | int | str],
    variable_overrides: dict[str, float | int | str],
    scenario_name: str,
) -> ScenarioProfile:
    return validate_scenario(
        replace(
            base_profile,
            name=scenario_name,
            analysis_name=base_profile.analysis_name,
            time_scaling_percent=top_level_overrides.get(
                "time_scaling_percent", base_profile.time_scaling_percent
            ),
            gripper_open_delay_s=float(
                top_level_overrides.get(
                    "gripper_open_delay_s", base_profile.gripper_open_delay_s
                )
            ),
            gripper_close_delay_s=float(
                top_level_overrides.get(
                    "gripper_close_delay_s", base_profile.gripper_close_delay_s
                )
            ),
            blending_percent=top_level_overrides.get(
                "blending_percent", base_profile.blending_percent
            ),
            variables={**base_profile.variables, **variable_overrides},
        )
    )


def _resolve_axis_value(profile: ScenarioProfile, axis_name: str) -> float | int | str | None:
    if axis_name.startswith(VARIABLE_AXIS_PREFIX):
        return profile.variables.get(axis_name[len(VARIABLE_AXIS_PREFIX) :])
    return getattr(profile, axis_name)


def _coerce_perturbed_value(original: float | int, delta_percent: float) -> float | int:
    updated_value = original * (1 + delta_percent / 100.0)
    if isinstance(original, int):
        return int(round(updated_value))
    return round(float(updated_value), 10)


def _coerce_case_value(value: float | int | None) -> float | int:
    if value is None:
        raise ScenarioValidationError("Variable case value cannot be None")
    return int(value) if isinstance(value, int) else round(float(value), 10)


def _variation_suffix(delta_percent: float) -> str:
    direction = "plus" if delta_percent >= 0 else "minus"
    magnitude = abs(delta_percent)
    magnitude_str = str(int(magnitude)) if float(magnitude).is_integer() else str(magnitude)
    return f"{direction}{magnitude_str}pct"


def _sample_random_case_value(
    definition: VariableCaseDefinition,
    rng: random.Random,
) -> float | int:
    minimum = definition.minimum
    maximum = definition.maximum
    if minimum is None or maximum is None:
        raise ScenarioValidationError("Random variable cases require minimum and maximum")
    if isinstance(minimum, int) and isinstance(maximum, int):
        return rng.randint(minimum, maximum)
    return round(rng.uniform(float(minimum), float(maximum)), 10)


def expand_variable_case_scenarios(
    profiles: Iterable[ScenarioProfile] | None,
    variable_cases: Iterable[VariableCasePlan] | None,
) -> list[ScenarioProfile]:
    if not variable_cases:
        return []

    base_profiles = [validate_scenario(profile) for profile in profiles or [ScenarioProfile(name="default")]]
    validated_plans = [validate_variable_case_plan(plan) for plan in variable_cases]
    expanded: list[ScenarioProfile] = []

    for base_profile in base_profiles:
        for plan in validated_plans:
            for case_name in plan.include:
                case_values = {
                    variable_name: _coerce_case_value(getattr(definition, case_name))
                    for variable_name, definition in plan.variables.items()
                }
                expanded.append(
                    validate_scenario(
                        replace(
                            base_profile,
                            name=f"{base_profile.name}-{plan.name}-{case_name}",
                            analysis_name=f"{base_profile.name}-{plan.name}-{case_name}",
                            variables={**base_profile.variables, **case_values},
                        )
                    )
                )

            if plan.random_runs > 0:
                rng = random.Random(plan.random_seed)
                analysis_name = f"{base_profile.name}-{plan.name}-random"
                for run_index in range(1, plan.random_runs + 1):
                    sampled_values = {
                        variable_name: _sample_random_case_value(definition, rng)
                        for variable_name, definition in plan.variables.items()
                    }
                    expanded.append(
                        validate_scenario(
                            replace(
                                base_profile,
                                name=f"{analysis_name}-{run_index}",
                                analysis_name=analysis_name,
                                pre_run_group=(analysis_name if plan.continuous_random_cycle else None),
                                skip_repeated_pre_run_cycles=plan.continuous_random_cycle,
                                variables={**base_profile.variables, **sampled_values},
                            )
                        )
                    )

    return expanded


def expand_perturbation_scenarios(
    profiles: Iterable[ScenarioProfile] | None,
    perturbations: dict[str, list[float | int]] | None,
) -> list[ScenarioProfile]:
    if not perturbations:
        return []

    base_profiles = [validate_scenario(profile) for profile in profiles or [ScenarioProfile(name="default")]]
    top_level_axes, variable_axes = _split_sweep_axes(perturbations)
    axes = [
        *(axis_name for axis_name, _ in top_level_axes),
        *(f"{VARIABLE_AXIS_PREFIX}{variable_name}" for variable_name, _ in variable_axes),
    ]
    values_by_axis = {
        axis_name: values
        for axis_name, values in [
            *top_level_axes,
            *[(f"{VARIABLE_AXIS_PREFIX}{name}", values) for name, values in variable_axes],
        ]
    }

    expanded: list[ScenarioProfile] = []
    for axis_name in axes:
        deltas = values_by_axis[axis_name]
        if not deltas:
            raise ScenarioValidationError(f"Perturbation axis {axis_name} must contain values")

    for base_profile in base_profiles:
        for axis_name in axes:
            original_value = _resolve_axis_value(base_profile, axis_name)
            if original_value is None:
                raise ScenarioValidationError(
                    f"Perturbation axis {axis_name} does not exist on scenario {base_profile.name}"
                )
            if not isinstance(original_value, (int, float)):
                raise ScenarioValidationError(
                    f"Perturbation axis {axis_name} on scenario {base_profile.name} must be numeric"
                )
            for delta_percent in values_by_axis[axis_name]:
                perturbed_value = _coerce_perturbed_value(original_value, float(delta_percent))
                scenario_name = f"{base_profile.name}-{axis_name}-{_variation_suffix(float(delta_percent))}"
                if axis_name.startswith(VARIABLE_AXIS_PREFIX):
                    variable_name = axis_name[len(VARIABLE_AXIS_PREFIX) :]
                    expanded.append(
                        _apply_sweep_overrides(
                            base_profile,
                            {},
                            {variable_name: perturbed_value},
                            scenario_name,
                        )
                    )
                else:
                    expanded.append(
                        _apply_sweep_overrides(
                            base_profile,
                            {axis_name: perturbed_value},
                            {},
                            scenario_name,
                        )
                    )

    return expanded


def expand_scenarios(
    profiles: Iterable[ScenarioProfile] | None,
    sweep: dict[str, list[float | int | str]] | None,
    perturbations: dict[str, list[float | int]] | None = None,
    variable_cases: Iterable[VariableCasePlan] | None = None,
) -> list[ScenarioProfile]:
    base_profiles = [validate_scenario(profile) for profile in profiles or []]
    expanded: list[ScenarioProfile] = list(base_profiles)

    expanded.extend(expand_perturbation_scenarios(base_profiles, perturbations))
    expanded.extend(expand_variable_case_scenarios(base_profiles, variable_cases))

    if not sweep:
        return expanded

    top_level_axes, variable_axes = _split_sweep_axes(sweep)
    axes: list[tuple[str, list[float | int | str]]] = [
        *top_level_axes,
        *[(f"{VARIABLE_AXIS_PREFIX}{name}", values) for name, values in variable_axes],
    ]

    for axis_name, values in axes:
        if not values:
            raise ScenarioValidationError(f"Sweep axis {axis_name} must contain values")

    base_profiles = list(expanded) or [ScenarioProfile(name="default")]
    combinations = list(product(*(values for _, values in axes)))

    for base_profile in base_profiles:
        for index, combination in enumerate(combinations, start=1):
            top_level_overrides: dict[str, float | int | str] = {}
            variable_overrides: dict[str, float | int | str] = {}
            for (axis_name, _), value in zip(axes, combination, strict=True):
                if axis_name.startswith(VARIABLE_AXIS_PREFIX):
                    variable_overrides[axis_name[len(VARIABLE_AXIS_PREFIX) :]] = value
                else:
                    top_level_overrides[axis_name] = value
            scenario_name = (
                f"sweep-{index}"
                if base_profile.name == "default"
                else f"{base_profile.name}-sweep-{index}"
            )
            expanded.append(
                _apply_sweep_overrides(
                    base_profile,
                    top_level_overrides,
                    variable_overrides,
                    scenario_name,
                )
            )

    return expanded
