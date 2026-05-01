from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean
from typing import Any


@dataclass(frozen=True, slots=True)
class SegmentStat:
    label: str
    duration_s: float


@dataclass(frozen=True, slots=True)
class RunMetrics:
    scenario_name: str
    run_index: int
    total_cycle_s: float
    checkpoint_segments: list[SegmentStat]
    measurement_phase: str = "steady_state"
    failed: bool = False
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SummaryStat:
    minimum_s: float
    average_s: float
    maximum_s: float
    std_dev_s: float
    contingency_adjusted_average_s: float


class AnalysisError(ValueError):
    """Raised when analysis input is inconsistent."""


def build_run_metrics(
    scenario_name: str,
    run_index: int,
    checkpoint_labels: list[str],
    checkpoint_times_s: list[float],
    contingency_percent: float,
    measurement_phase: str = "steady_state",
    failed: bool = False,
    failure_reason: str | None = None,
) -> RunMetrics:
    if len(checkpoint_labels) != len(checkpoint_times_s):
        raise AnalysisError("Checkpoint labels and times must have the same length")
    if checkpoint_times_s != sorted(checkpoint_times_s):
        raise AnalysisError("Checkpoint times must be in ascending order")
    if contingency_percent < 0:
        raise AnalysisError("Contingency percent cannot be negative")

    previous = 0.0
    segments: list[SegmentStat] = []
    for label, checkpoint_time in zip(checkpoint_labels, checkpoint_times_s, strict=True):
        segments.append(SegmentStat(label=label, duration_s=checkpoint_time - previous))
        previous = checkpoint_time

    total_cycle_s = 0.0
    if checkpoint_times_s:
        total_cycle_s = checkpoint_times_s[-1]
        if len(checkpoint_times_s) > 1:
            total_cycle_s = checkpoint_times_s[-1] - checkpoint_times_s[0]

    return RunMetrics(
        scenario_name=scenario_name,
        run_index=run_index,
        measurement_phase=measurement_phase,
        total_cycle_s=total_cycle_s,
        checkpoint_segments=segments,
        failed=failed,
        failure_reason=failure_reason,
    )


def summarize_runs(runs: list[RunMetrics], contingency_percent: float) -> SummaryStat:
    valid_runs = [run.total_cycle_s for run in runs if not run.failed]
    if not valid_runs:
        raise AnalysisError("At least one successful run is required for summary statistics")
    if contingency_percent < 0:
        raise AnalysisError("Contingency percent cannot be negative")

    average = mean(valid_runs)
    variance = 0.0
    if len(valid_runs) > 1:
        variance = sum((value - average) ** 2 for value in valid_runs) / (len(valid_runs) - 1)

    return SummaryStat(
        minimum_s=min(valid_runs),
        average_s=average,
        maximum_s=max(valid_runs),
        std_dev_s=sqrt(variance),
        contingency_adjusted_average_s=average * (1 + contingency_percent / 100.0),
    )


def compare_scenarios(runs_by_scenario: dict[str, list[RunMetrics]], contingency_percent: float) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for scenario_name, runs in runs_by_scenario.items():
        comparison[scenario_name] = asdict(summarize_runs(runs, contingency_percent))
    return comparison
