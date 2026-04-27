import pytest

from mecademic_cycle_report.analysis import build_run_metrics, compare_scenarios, summarize_runs


def test_build_run_metrics_creates_segment_durations() -> None:
    metrics = build_run_metrics(
        scenario_name="baseline",
        run_index=1,
        checkpoint_labels=["start", "pick", "end"],
        checkpoint_times_s=[0.4, 1.0, 1.5],
        contingency_percent=20.0,
    )

    assert metrics.total_cycle_s == 1.1
    assert [segment.duration_s for segment in metrics.checkpoint_segments] == [0.4, 0.6, 0.5]


def test_compare_scenarios_summarizes_each_group() -> None:
    baseline = [
        build_run_metrics("baseline", 1, ["start", "end"], [0.5, 1.5], 20.0),
        build_run_metrics("baseline", 2, ["start", "end"], [0.4, 1.4], 20.0),
    ]
    sweep = [build_run_metrics("slow", 1, ["start", "end"], [0.6, 1.8], 20.0)]

    comparison = compare_scenarios({"baseline": baseline, "slow": sweep}, contingency_percent=20.0)

    assert comparison["baseline"]["average_s"] == summarize_runs(baseline, 20.0).average_s
    assert comparison["slow"]["maximum_s"] == pytest.approx(1.2)
