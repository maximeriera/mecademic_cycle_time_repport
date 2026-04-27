from mecademic_cycle_report.scenario_matrix import (
    ScenarioProfile,
    ScenarioValidationError,
    VariableCaseDefinition,
    VariableCasePlan,
    expand_scenarios,
)


def test_expand_scenarios_builds_cartesian_product() -> None:
    scenarios = expand_scenarios(
        profiles=[ScenarioProfile(name="baseline")],
        sweep={"gripper_open_delay_s": [0.1, 0.2], "gripper_close_delay_s": [0.3, 0.4]},
    )

    assert len(scenarios) == 5
    assert scenarios[0].name == "baseline"
    assert scenarios[-1].gripper_close_delay_s == 0.4


def test_expand_scenarios_rejects_unknown_axis() -> None:
    try:
        expand_scenarios(profiles=None, sweep={"bad_axis": [1.0]})
    except ScenarioValidationError as exc:
        assert "Unsupported sweep axes" in str(exc)
    else:
        raise AssertionError("Expected unsupported axis to fail")


def test_validate_scenario_rejects_invalid_variable_names() -> None:
    try:
        expand_scenarios(
            profiles=[ScenarioProfile(name="baseline", variables={"bad-name": 1})],
            sweep=None,
        )
    except ScenarioValidationError as exc:
        assert "vars.NAME rules" in str(exc)
    else:
        raise AssertionError("Expected invalid variable names to fail")


def test_expand_scenarios_applies_variable_sweeps_on_top_of_profiles() -> None:
    scenarios = expand_scenarios(
        profiles=[
            ScenarioProfile(name="baseline", time_scaling_percent=100, variables={"SPD_INSERT": 800})
        ],
        sweep={"variables.SPD_INSERT": [500, 700], "time_scaling_percent": [80, 100]},
    )

    assert [scenario.name for scenario in scenarios] == [
        "baseline",
        "baseline-sweep-1",
        "baseline-sweep-2",
        "baseline-sweep-3",
        "baseline-sweep-4",
    ]
    assert scenarios[1].variables["SPD_INSERT"] == 500
    assert scenarios[1].time_scaling_percent == 80
    assert scenarios[-1].variables["SPD_INSERT"] == 700
    assert scenarios[-1].time_scaling_percent == 100


def test_expand_scenarios_builds_percentage_perturbations_from_profile_values() -> None:
    scenarios = expand_scenarios(
        profiles=[
            ScenarioProfile(
                name="baseline",
                variables={"SPD_INSERT": 800, "GRP_DELAY": 0.2},
            )
        ],
        sweep=None,
        perturbations={
            "variables.SPD_INSERT": [-10, 10],
            "variables.GRP_DELAY": [-10, 10],
        },
    )

    assert [scenario.name for scenario in scenarios] == [
        "baseline",
        "baseline-variables.SPD_INSERT-minus10pct",
        "baseline-variables.SPD_INSERT-plus10pct",
        "baseline-variables.GRP_DELAY-minus10pct",
        "baseline-variables.GRP_DELAY-plus10pct",
    ]
    assert scenarios[1].variables["SPD_INSERT"] == 720
    assert scenarios[2].variables["SPD_INSERT"] == 880
    assert scenarios[3].variables["GRP_DELAY"] == 0.18
    assert scenarios[4].variables["GRP_DELAY"] == 0.22


def test_expand_scenarios_rejects_missing_perturbation_axis() -> None:
    try:
        expand_scenarios(
            profiles=[ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800})],
            sweep=None,
            perturbations={"variables.SPD_RETRACT": [-10, 10]},
        )
    except ScenarioValidationError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing perturbation axis to fail")


def test_expand_scenarios_builds_best_worst_and_grouped_random_variable_cases() -> None:
    scenarios = expand_scenarios(
        profiles=[ScenarioProfile(name="baseline", variables={"SPD_INSERT": 800})],
        sweep=None,
        variable_cases=[
            VariableCasePlan(
                name="pick_position",
                variables={
                    "PICK_X": VariableCaseDefinition(
                        minimum=10.0,
                        maximum=12.0,
                        best=10.5,
                        worst=11.5,
                    ),
                    "PICK_Y": VariableCaseDefinition(
                        minimum=-20.0,
                        maximum=-18.0,
                        best=-18.5,
                        worst=-19.5,
                    ),
                },
                random_runs=2,
                random_seed=7,
                continuous_random_cycle=True,
            )
        ],
    )

    assert [scenario.name for scenario in scenarios] == [
        "baseline",
        "baseline-pick_position-best",
        "baseline-pick_position-worst",
        "baseline-pick_position-random-1",
        "baseline-pick_position-random-2",
    ]
    assert scenarios[1].variables["PICK_X"] == 10.5
    assert scenarios[2].variables["PICK_Y"] == -19.5
    assert scenarios[3].analysis_name == "baseline-pick_position-random"
    assert scenarios[4].analysis_name == "baseline-pick_position-random"
    assert scenarios[3].pre_run_group == "baseline-pick_position-random"
    assert scenarios[4].skip_repeated_pre_run_cycles is True
    assert scenarios[3].variables == {
        "SPD_INSERT": 800,
        "PICK_X": 10.6476655297,
        "PICK_Y": -19.6983016522,
    }
    assert scenarios[4].variables == {
        "SPD_INSERT": 800,
        "PICK_X": 11.3018689461,
        "PICK_Y": -19.8551274267,
    }


def test_expand_scenarios_allows_unseeded_random_variable_cases() -> None:
    scenarios = expand_scenarios(
        profiles=[ScenarioProfile(name="baseline")],
        sweep=None,
        variable_cases=[
            VariableCasePlan(
                name="pick_position",
                variables={
                    "PICK_X": VariableCaseDefinition(
                        minimum=10.0,
                        maximum=12.0,
                        best=10.5,
                        worst=11.5,
                    ),
                    "PICK_Y": VariableCaseDefinition(
                        minimum=-20.0,
                        maximum=-18.0,
                        best=-18.5,
                        worst=-19.5,
                    ),
                },
                random_runs=2,
                random_seed=None,
            )
        ],
    )

    random_scenarios = [scenario for scenario in scenarios if scenario.analysis_name == "baseline-pick_position-random"]

    assert len(random_scenarios) == 2
    for scenario in random_scenarios:
        assert 10.0 <= float(scenario.variables["PICK_X"]) <= 12.0
        assert -20.0 <= float(scenario.variables["PICK_Y"]) <= -18.0
