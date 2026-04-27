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

    def start_program(self) -> None:
        self.started += 1

    def wait_for_checkpoint(self, checkpoint: ExpectedCheckpoint) -> CheckpointObservation:
        observation = self._observations.pop(0)
        assert observation.checkpoint_id == checkpoint.checkpoint_id
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
            CheckpointObservation(checkpoint_id=21, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.5),
            CheckpointObservation(checkpoint_id=20, status="reached", elapsed_s=1.3),
            CheckpointObservation(checkpoint_id=22, status="reached", elapsed_s=1.4),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\nSetCheckpoint(20)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 1
    assert 0.0 <= records[0].observations[0].elapsed_s <= records[0].observations[1].elapsed_s
    assert records[0].metrics.total_cycle_s == records[0].observations[-1].elapsed_s - records[0].observations[0].elapsed_s
    assert robot.armed_checkpoint_ids == [21, 10, 20, 22]
    assert robot.started == 1
    assert records[0].rendered_program_path.endswith("program__baseline.mxprog")


def test_cycle_runner_fails_on_discarded_checkpoint(tmp_path: Path) -> None:
    config = AppConfig(
        robot=RobotSettings(address="192.168.0.100"),
        analysis=AnalysisSettings(runs=1, warmup_runs=0, alignment_run=False, contingency_percent=20.0),
        checkpoints=[ExpectedCheckpoint(checkpoint_id=10, label="start")],
        scenarios=[ScenarioProfile(name="baseline")],
    )
    robot = FakeRobotClient(
        [CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.1), CheckpointObservation(checkpoint_id=10, status="discarded", elapsed_s=0.5)]
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
            CheckpointObservation(checkpoint_id=21, status="reached", elapsed_s=0.1),
            CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.2),
            CheckpointObservation(checkpoint_id=20, status="reached", elapsed_s=0.8),
            CheckpointObservation(checkpoint_id=22, status="reached", elapsed_s=0.9),
        ]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\nSetCheckpoint(20)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert records[0].metrics.scenario_name == "baseline-pick-random"
    assert records[0].scenario.name == "baseline-pick-random-1"


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
        [CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.05), CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.1), CheckpointObservation(checkpoint_id=12, status="reached", elapsed_s=0.15)]
        + [CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.05), CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.1), CheckpointObservation(checkpoint_id=12, status="reached", elapsed_s=0.15)]
        + [CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.05), CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.1), CheckpointObservation(checkpoint_id=12, status="reached", elapsed_s=0.15)]
        + [CheckpointObservation(checkpoint_id=11, status="reached", elapsed_s=0.05), CheckpointObservation(checkpoint_id=10, status="reached", elapsed_s=0.1), CheckpointObservation(checkpoint_id=12, status="reached", elapsed_s=0.15)]
    )
    program_path = tmp_path / "program.mxprog"
    program_path.write_text("SetCheckpoint(10)\n", encoding="utf-8")

    records = CycleRunner(config=config, robot_client=robot).execute(program_path)

    assert len(records) == 2
    assert robot.started == 4
    assert robot.applied_scenarios == ["baseline-pick-random-1", "baseline-pick-random-2"]
