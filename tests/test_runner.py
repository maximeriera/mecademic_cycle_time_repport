from pathlib import Path

from mecademic_cycle_report.checkpoint_spec import CheckpointObservation, ExpectedCheckpoint
from mecademic_cycle_report.config import AppConfig, AnalysisSettings, RobotSettings
from mecademic_cycle_report.runner import CycleRunner, RunFailure
from mecademic_cycle_report.scenario_matrix import ScenarioProfile


class FakeRobotClient:
    def __init__(self, observations: list[CheckpointObservation]) -> None:
        self._observations = observations.copy()
        self.connected = False
        self.started = 0
        self.armed_checkpoint_ids: list[int] = []
        self.loaded_programs: list[str] = []
        self.applied_scenarios: list[str] = []
        self.idle_waits = 0

    def connect(self) -> None:
        self.connected = True

    def ensure_ready(self) -> None:
        return None

    def load_program(self, mxprog_path: Path) -> None:
        assert mxprog_path.name.endswith(".mxprog")
        self.loaded_programs.append(mxprog_path.name)

    def apply_scenario(self, scenario: ScenarioProfile) -> None:
        assert scenario.name
        self.applied_scenarios.append(scenario.name)

    def arm_checkpoints(self, checkpoints: list[ExpectedCheckpoint]) -> None:
        self.armed_checkpoint_ids = [checkpoint.checkpoint_id for checkpoint in checkpoints]

    def start_program(
        self,
        start_checkpoint_id: int | None = None,
        end_checkpoint_id: int | None = None,
    ) -> None:
        self.started += 1

    def wait_until_idle(self) -> None:
        self.idle_waits += 1

    def wait_for_checkpoint(self, checkpoint: ExpectedCheckpoint) -> CheckpointObservation:
        observation = self._observations.pop(0)
        assert observation.checkpoint_id == checkpoint.checkpoint_id
        if observation.label is None:
            return CheckpointObservation(
                checkpoint_id=observation.checkpoint_id,
                status=observation.status,
                elapsed_s=observation.elapsed_s,
                label=checkpoint.label,
                detail=observation.detail,
            )
        return observation

    def disconnect(self) -> None:
        self.connected = False


def test_cycle_runner_builds_run_record(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[
            ExpectedCheckpoint(checkpoint_id=10, label="start"),
            ExpectedCheckpoint(checkpoint_id=20, label="end"),
        ],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.5),
            CheckpointObservation(checkpoint_id=21, status="reached", elapsed_s=1.3),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=1.4),
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=34, status="reached", elapsed_s=0.5),
            CheckpointObservation(checkpoint_id=44, status="reached", elapsed_s=1.3),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=1.4),
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=57, status="reached", elapsed_s=0.5),
            CheckpointObservation(checkpoint_id=67, status="reached", elapsed_s=1.3),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=1.4),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\nSetCheckpoint(20)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 3
    assert [record.metrics.measurement_phase for record in records] == [
        "accel_only",
        "steady_state",
        "decel_only",
    ]
    assert 0.0 <= records[1].observations[0].elapsed_s <= records[1].observations[1].elapsed_s
    assert records[1].metrics.total_cycle_s == records[1].observations[-1].elapsed_s - records[1].observations[0].elapsed_s
    assert robot.armed_checkpoint_ids == [7000, 11, 21, 7001, 7002, 34, 44, 7003, 7004, 57, 67, 7005]
    assert robot.started == 1
    assert records[1].rendered_program_path.endswith("program__runtime__steady_state.mxprog")


def test_cycle_runner_alignment_mode_records_single_accel_decel_and_steady_state_runs(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=2, warmup_runs=0, alignment_run=True, contingency_percent=20.0),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.20),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.25),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=24, status="reached", elapsed_s=0.40),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.45),
            CheckpointObservation(checkpoint_id=7006, status="reached", elapsed_s=0.50),
            CheckpointObservation(checkpoint_id=37, status="reached", elapsed_s=0.55),
            CheckpointObservation(checkpoint_id=7007, status="reached", elapsed_s=0.60),
            CheckpointObservation(checkpoint_id=7008, status="reached", elapsed_s=0.65),
            CheckpointObservation(checkpoint_id=50, status="reached", elapsed_s=0.70),
            CheckpointObservation(checkpoint_id=7009, status="reached", elapsed_s=0.75),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 5
    assert [record.metrics.measurement_phase for record in records] == [
        "single_run",
        "accel_only",
        "steady_state",
        "steady_state",
        "decel_only",
    ]
    assert [record.include_in_summary for record in records] == [False, False, True, True, False]
    assert [record.metrics.run_index for record in records] == [0, 0, 1, 2, 0]
    assert records[2].metrics.total_cycle_s == records[2].observations[-1].elapsed_s
    assert robot.started == 2
    assert records[0].rendered_program_path.endswith("program__runtime.mxprog")
    assert records[1].rendered_program_path.endswith("program__runtime__steady_state.mxprog")
    assert records[4].rendered_program_path.endswith("program__runtime__steady_state.mxprog")


def test_cycle_runner_without_alignment_still_records_accel_decel_and_steady_state_runs(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.20),
            CheckpointObservation(checkpoint_id=24, status="reached", elapsed_s=0.25),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=37, status="reached", elapsed_s=0.40),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.45),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 3
    assert [record.metrics.measurement_phase for record in records] == [
        "accel_only",
        "steady_state",
        "decel_only",
    ]
    assert [record.include_in_summary for record in records] == [False, True, False]
    assert [record.metrics.run_index for record in records] == [0, 1, 0]
    assert robot.started == 1
    assert records[0].rendered_program_path.endswith("program__runtime__steady_state.mxprog")
    assert records[1].rendered_program_path.endswith("program__runtime__steady_state.mxprog")
    assert records[2].rendered_program_path.endswith("program__runtime__steady_state.mxprog")


def test_cycle_runner_fails_on_discarded_checkpoint(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=11, status="discarded", elapsed_s=0.5),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\n", encoding="utf-8")

    try:
        CycleRunner(config=config, robot_client=robot).execute(program_path)
    except RunFailure as exc:
        assert "discarded" in str(exc)
    else:
        raise AssertionError("Expected a discarded checkpoint to fail the run")


def test_cycle_runner_uses_analysis_name_for_metrics(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[
            ExpectedCheckpoint(checkpoint_id=10, label="start"),
            ExpectedCheckpoint(checkpoint_id=20, label="end"),
        ],
        scenarios=[ScenarioProfile(name="baseline-pick-random-1", analysis_name="baseline-pick-random")],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.2),
            CheckpointObservation(checkpoint_id=21, status="reached", elapsed_s=0.8),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.9),
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=34, status="reached", elapsed_s=0.2),
            CheckpointObservation(checkpoint_id=44, status="reached", elapsed_s=0.8),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.9),
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=57, status="reached", elapsed_s=0.2),
            CheckpointObservation(checkpoint_id=67, status="reached", elapsed_s=0.8),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.9),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\nSetCheckpoint(20)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert [record.metrics.scenario_name for record in records] == [
        "baseline-pick-random",
        "baseline-pick-random",
        "baseline-pick-random",
    ]
    assert all(record.scenario.name == "baseline-pick-random-1" for record in records)


def test_cycle_runner_skips_repeated_pre_measurement_cycles_for_continuous_random_group(
    tmp_path: Path,
) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=1, alignment_run=True, contingency_percent=20.0),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[
            ScenarioProfile(
                name="baseline-pick-random-1",
                analysis_name="baseline-pick-random",
                pre_run_group="baseline-pick-random",
                skip_repeated_pre_run_cycles=True,
            ),
            ScenarioProfile(
                name="baseline-pick-random-2",
                analysis_name="baseline-pick-random",
                pre_run_group="baseline-pick-random",
                skip_repeated_pre_run_cycles=True,
            ),
        ],
    )
    robot = FakeRobotClient(
        [
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.20),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.25),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.40),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.45),
            CheckpointObservation(checkpoint_id=7006, status="reached", elapsed_s=0.50),
            CheckpointObservation(checkpoint_id=24, status="reached", elapsed_s=0.55),
            CheckpointObservation(checkpoint_id=7007, status="reached", elapsed_s=0.60),
            CheckpointObservation(checkpoint_id=7008, status="reached", elapsed_s=0.65),
            CheckpointObservation(checkpoint_id=37, status="reached", elapsed_s=0.70),
            CheckpointObservation(checkpoint_id=7009, status="reached", elapsed_s=0.75),
            CheckpointObservation(checkpoint_id=7010, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=7011, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=7012, status="reached", elapsed_s=0.20),
            CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.25),
            CheckpointObservation(checkpoint_id=7013, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=7014, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=24, status="reached", elapsed_s=0.40),
            CheckpointObservation(checkpoint_id=7015, status="reached", elapsed_s=0.45),
            CheckpointObservation(checkpoint_id=7016, status="reached", elapsed_s=0.50),
            CheckpointObservation(checkpoint_id=37, status="reached", elapsed_s=0.55),
            CheckpointObservation(checkpoint_id=7017, status="reached", elapsed_s=0.60),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 8
    assert [record.scenario.name for record in records] == [
        "baseline-pick-random-1",
        "baseline-pick-random-1",
        "baseline-pick-random-1",
        "baseline-pick-random-1",
        "baseline-pick-random-2",
        "baseline-pick-random-2",
        "baseline-pick-random-2",
        "baseline-pick-random-2",
    ]
    assert [record.metrics.measurement_phase for record in records] == [
        "single_run",
        "accel_only",
        "steady_state",
        "decel_only",
        "single_run",
        "accel_only",
        "steady_state",
        "decel_only",
    ]
    assert [record.include_in_summary for record in records] == [
        False,
        False,
        True,
        False,
        False,
        False,
        True,
        False,
    ]
    assert [record.metrics.run_index for record in records] == [0, 0, 1, 0, 0, 0, 1, 0]
    assert robot.started == 5
    assert records[2].rendered_program_path.endswith("program__runtime__steady_state.mxprog")
    assert records[6].rendered_program_path.endswith("program__runtime__steady_state.mxprog")
    assert robot.applied_scenarios == [
        "baseline-pick-random-1",
        "baseline-pick-random-2",
    ]


def test_cycle_runner_queues_next_program_start_at_handoff_checkpoint(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[
            ExpectedCheckpoint(checkpoint_id=1, label="station_1_start"),
            ExpectedCheckpoint(checkpoint_id=2, label="planner_handoff", queue_next_run=True),
            ExpectedCheckpoint(checkpoint_id=3, label="cycle_complete"),
        ],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            # Cycle 1 (accel): program_start (7000) + handoff checkpoints (1,2) + cycle_end (7001)
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.20),
            # Cycle 2 (steady_state): cycle_start (7002) + handoff checkpoints (1,2) + cycle_end (7003)
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.25),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.40),
            # Cycle 3 (decel): cycle_start (7004) + all checkpoints (1,2,3) + program_end (7005)
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.45),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.50),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.55),
            CheckpointObservation(checkpoint_id=3, status="reached", elapsed_s=0.60),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.65),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text(
        "SetCheckpoint(1)\nSetCheckpoint(2)\nSetCheckpoint(3)\n",
        encoding="utf-8",
    )

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 3
    assert [record.metrics.measurement_phase for record in records] == [
        "accel_only",
        "steady_state",
        "decel_only",
    ]
    assert [record.metrics.run_index for record in records] == [0, 1, 0]
    assert [record.include_in_summary for record in records] == [False, True, False]
    assert robot.started == 1
    assert robot.armed_checkpoint_ids == [7000, 1, 2, 7001, 7002, 1, 2, 7003, 7004, 1, 2, 3, 7005]
    assert robot.loaded_programs == ["program__runtime.mxprog", "program__runtime__queued.mxprog"]
    assert robot.applied_scenarios == ["baseline"]
    assert records[0].observations[0].label == "program_start"
    assert records[1].observations[0].label == "cycle_start"
    assert records[2].observations[0].label == "cycle_start"
    assert records[0].rendered_program_path.endswith("program__runtime__queued.mxprog")


def test_cycle_runner_queue_mode_keeps_single_run_probe_when_alignment_enabled(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=True, contingency_percent=20.0),
        checkpoints=[
            ExpectedCheckpoint(checkpoint_id=1, label="station_1_start"),
            ExpectedCheckpoint(checkpoint_id=2, label="planner_handoff", queue_next_run=True),
            ExpectedCheckpoint(checkpoint_id=3, label="cycle_complete"),
        ],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [
            # Alignment run: single_run with full checkpoints
            CheckpointObservation(checkpoint_id=7000, status="reached", elapsed_s=0.05),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.10),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.15),
            CheckpointObservation(checkpoint_id=3, status="reached", elapsed_s=0.20),
            CheckpointObservation(checkpoint_id=7001, status="reached", elapsed_s=0.25),
            # Queued cycle 1 (accel): handoff checkpoints only (1,2)
            CheckpointObservation(checkpoint_id=7002, status="reached", elapsed_s=0.30),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.35),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.40),
            CheckpointObservation(checkpoint_id=7003, status="reached", elapsed_s=0.45),
            # Queued cycle 2 (steady_state): handoff checkpoints only (1,2)
            CheckpointObservation(checkpoint_id=7004, status="reached", elapsed_s=0.50),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.55),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.60),
            CheckpointObservation(checkpoint_id=7005, status="reached", elapsed_s=0.65),
            # Queued cycle 3 (decel): all checkpoints (1,2,3)
            CheckpointObservation(checkpoint_id=7006, status="reached", elapsed_s=0.70),
            CheckpointObservation(checkpoint_id=1, status="reached", elapsed_s=0.75),
            CheckpointObservation(checkpoint_id=2, status="reached", elapsed_s=0.80),
            CheckpointObservation(checkpoint_id=3, status="reached", elapsed_s=0.85),
            CheckpointObservation(checkpoint_id=7007, status="reached", elapsed_s=0.90),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text(
        "SetCheckpoint(1)\nSetCheckpoint(2)\nSetCheckpoint(3)\n",
        encoding="utf-8",
    )

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 4
    assert [record.metrics.measurement_phase for record in records] == [
        "single_run",
        "accel_only",
        "steady_state",
        "decel_only",
    ]
    assert robot.started == 2
    assert records[0].rendered_program_path.endswith("program__runtime.mxprog")
    assert records[1].rendered_program_path.endswith("program__runtime__queued.mxprog")
    assert records[2].rendered_program_path.endswith("program__runtime__queued.mxprog")
    assert records[3].rendered_program_path.endswith("program__runtime__queued.mxprog")
