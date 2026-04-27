from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from .analysis import RunMetrics, build_run_metrics
from .checkpoint_spec import CheckpointObservation, validate_observation
from .config import AppConfig
from .program_template import render_program_file
from .robot_client import RobotClient
from .scenario_matrix import ScenarioProfile


@dataclass(frozen=True, slots=True)
class RunRecord:
    scenario: ScenarioProfile
    metrics: RunMetrics
    observations: list[CheckpointObservation]
    rendered_program_path: str


class RunFailure(RuntimeError):
    """Raised when a run cannot satisfy the expected checkpoint sequence."""


@dataclass(slots=True)
class CycleRunner:
    config: AppConfig
    robot_client: RobotClient

    def _effective_checkpoints(self):
        configured = self.config.checkpoints
        if not configured:
            return []
        max_id = max(checkpoint.checkpoint_id for checkpoint in configured)
        start_checkpoint = self.config.checkpoints[0].__class__(
            checkpoint_id=max_id + 1,
            label="program_start",
        )
        end_checkpoint = self.config.checkpoints[0].__class__(
            checkpoint_id=max_id + 2,
            label="program_end",
        )
        return [start_checkpoint, *configured, end_checkpoint]

    @staticmethod
    def _analysis_name(scenario: ScenarioProfile) -> str:
        return scenario.analysis_name or scenario.name

    @staticmethod
    def _should_run_pre_measurement_cycles(
        scenario: ScenarioProfile,
        completed_pre_run_groups: set[str],
    ) -> bool:
        if not scenario.skip_repeated_pre_run_cycles:
            return True
        if scenario.pre_run_group is None:
            return True
        if scenario.pre_run_group in completed_pre_run_groups:
            return False
        completed_pre_run_groups.add(scenario.pre_run_group)
        return True

    def execute(self, mxprog_path: str | Path) -> list[RunRecord]:
        path = Path(mxprog_path)
        records: list[RunRecord] = []
        effective_checkpoints = self._effective_checkpoints()
        rendered_programs = {
            scenario.name: render_program_file(
                path,
                scenario,
                Path(self.config.analysis.output_dir),
                effective_checkpoints[0].checkpoint_id if effective_checkpoints else None,
                effective_checkpoints[-1].checkpoint_id if effective_checkpoints else None,
            )
            for scenario in self.config.scenarios
        }
        if self.config.analysis.dry_run:
            return self._build_dry_run_records(rendered_programs, effective_checkpoints)

        self.robot_client.connect()
        try:
            self.robot_client.ensure_ready()
            completed_pre_run_groups: set[str] = set()
            for scenario in self.config.scenarios:
                self.robot_client.load_program(rendered_programs[scenario.name])
                self.robot_client.apply_scenario(scenario)
                should_run_pre_measurement_cycles = self._should_run_pre_measurement_cycles(
                    scenario,
                    completed_pre_run_groups,
                )
                if should_run_pre_measurement_cycles:
                    if self.config.analysis.alignment_run:
                        self._execute_single_run(
                            scenario=scenario,
                            run_index=-1,
                            rendered_program_path=rendered_programs[scenario.name],
                            checkpoints=effective_checkpoints,
                        )
                    for _ in range(self.config.analysis.warmup_runs):
                        self._execute_single_run(
                            scenario=scenario,
                            run_index=0,
                            rendered_program_path=rendered_programs[scenario.name],
                            checkpoints=effective_checkpoints,
                        )
                for run_index in range(1, self.config.analysis.runs + 1):
                    records.append(
                        self._execute_single_run(
                            scenario=scenario,
                            run_index=run_index,
                            rendered_program_path=rendered_programs[scenario.name],
                            checkpoints=effective_checkpoints,
                        )
                    )
        finally:
            self.robot_client.disconnect()

        return records

    def _execute_single_run(
        self,
        scenario: ScenarioProfile,
        run_index: int,
        rendered_program_path: Path,
        checkpoints,
    ) -> RunRecord:
        self.robot_client.arm_checkpoints(checkpoints)
        run_start_time = monotonic()
        self.robot_client.start_program()
        observations: list[CheckpointObservation] = []
        labels: list[str] = []
        elapsed: list[float] = []

        for checkpoint in checkpoints:
            observation = validate_observation(self.robot_client.wait_for_checkpoint(checkpoint))
            observation = CheckpointObservation(
                checkpoint_id=observation.checkpoint_id,
                status=observation.status,
                elapsed_s=monotonic() - run_start_time,
                label=observation.label,
                detail=observation.detail,
            )
            observations.append(observation)
            labels.append(checkpoint.label)
            elapsed.append(observation.elapsed_s)
            if observation.status != "reached":
                raise RunFailure(
                    f"Checkpoint {checkpoint.checkpoint_id} failed with status {observation.status}"
                )

        metrics = build_run_metrics(
            scenario_name=self._analysis_name(scenario),
            run_index=run_index,
            checkpoint_labels=labels,
            checkpoint_times_s=elapsed,
            contingency_percent=self.config.analysis.contingency_percent,
        )
        return RunRecord(
            scenario=scenario,
            metrics=metrics,
            observations=observations,
            rendered_program_path=str(rendered_program_path),
        )

    def _build_dry_run_records(self, rendered_programs: dict[str, Path], checkpoints) -> list[RunRecord]:
        records: list[RunRecord] = []
        checkpoint_labels = [checkpoint.label for checkpoint in checkpoints]
        checkpoint_times = [float(index + 1) for index, _ in enumerate(checkpoints)]

        for scenario in self.config.scenarios:
            for run_index in range(1, self.config.analysis.runs + 1):
                metrics = build_run_metrics(
                    scenario_name=self._analysis_name(scenario),
                    run_index=run_index,
                    checkpoint_labels=checkpoint_labels,
                    checkpoint_times_s=checkpoint_times,
                    contingency_percent=self.config.analysis.contingency_percent,
                )
                observations = [
                    CheckpointObservation(
                        checkpoint_id=checkpoint.checkpoint_id,
                        status="reached",
                        elapsed_s=checkpoint_times[index],
                        label=checkpoint.label,
                    )
                    for index, checkpoint in enumerate(checkpoints)
                ]
                records.append(
                    RunRecord(
                        scenario=scenario,
                        metrics=metrics,
                        observations=observations,
                        rendered_program_path=str(rendered_programs[scenario.name]),
                    )
                )

        return records
