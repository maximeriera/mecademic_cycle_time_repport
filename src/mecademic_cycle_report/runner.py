from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from .analysis import RunMetrics, build_run_metrics
from .checkpoint_spec import (
    CheckpointObservation,
    ExpectedCheckpoint,
    boundary_checkpoint_ids,
    validate_observation,
)
from .config import AppConfig
from .program_template import (
    render_runtime_program_file,
    render_runtime_queued_program_file,
    render_runtime_repeated_program_file,
)
from .robot_client import RobotClient
from .scenario_matrix import ScenarioProfile


@dataclass(frozen=True, slots=True)
class RunRecord:
    scenario: ScenarioProfile
    metrics: RunMetrics
    observations: list[CheckpointObservation]
    rendered_program_path: str
    include_in_summary: bool = True


class RunFailure(RuntimeError):
    """Raised when a run cannot satisfy the expected checkpoint sequence."""


@dataclass(slots=True)
class CycleRunner:
    config: AppConfig
    robot_client: RobotClient

    @staticmethod
    def _build_run_checkpoints(configured_checkpoints, boundary_pair_index: int):
        configured = list(configured_checkpoints)
        if not configured:
            return []
        start_checkpoint_id, end_checkpoint_id = boundary_checkpoint_ids(boundary_pair_index)
        start_checkpoint = configured[0].__class__(
            checkpoint_id=start_checkpoint_id,
            label="program_start",
        )
        end_checkpoint = configured[0].__class__(
            checkpoint_id=end_checkpoint_id,
            label="program_end",
        )
        return [start_checkpoint, *configured, end_checkpoint]

    @staticmethod
    def _analysis_name(scenario: ScenarioProfile) -> str:
        return scenario.analysis_name or scenario.name

    def _queue_handoff_index(self) -> int | None:
        for index, checkpoint in enumerate(self.config.checkpoints):
            if checkpoint.queue_next_run:
                return index
        return None

    def _uses_queued_program_starts(self) -> bool:
        return self._queue_handoff_index() is not None

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
        rendered_program_path = render_runtime_program_file(
            path,
            Path(self.config.analysis.output_dir),
        )
        if self.config.analysis.dry_run:
            return self._build_dry_run_records(path, rendered_program_path)

        self.robot_client.connect()
        try:
            self.robot_client.ensure_ready()
            completed_pre_run_groups: set[str] = set()
            next_boundary_pair_index = 0
            loaded_program_path: Path | None = None

            def ensure_program_loaded(program_path: Path) -> None:
                nonlocal loaded_program_path
                if loaded_program_path == program_path:
                    return
                self.robot_client.load_program(program_path)
                loaded_program_path = program_path

            for scenario in self.config.scenarios:
                self.robot_client.apply_scenario(scenario)
                should_run_pre_measurement_cycles = self._should_run_pre_measurement_cycles(
                    scenario,
                    completed_pre_run_groups,
                )
                if self.config.analysis.alignment_run:
                    ensure_program_loaded(rendered_program_path)
                    single_run_checkpoints = self._build_run_checkpoints(
                        self.config.checkpoints,
                        next_boundary_pair_index,
                    )
                    next_boundary_pair_index += 1
                    records.append(
                        self._execute_single_run(
                            scenario=scenario,
                            run_index=0,
                            rendered_program_path=rendered_program_path,
                            checkpoints=single_run_checkpoints,
                            measurement_phase="single_run",
                            include_in_summary=False,
                        )
                    )
                if should_run_pre_measurement_cycles:
                    for _ in range(self.config.analysis.warmup_runs):
                        ensure_program_loaded(rendered_program_path)
                        warmup_checkpoints = self._build_run_checkpoints(
                            self.config.checkpoints,
                            next_boundary_pair_index,
                        )
                        next_boundary_pair_index += 1
                        self._execute_single_run(
                            scenario=scenario,
                            run_index=0,
                            rendered_program_path=rendered_program_path,
                            checkpoints=warmup_checkpoints,
                        )
                if self._uses_queued_program_starts():
                    # Ensure reference program is loaded before queued program,
                    # since the queued program will invoke it via StartProgram()
                    ensure_program_loaded(rendered_program_path)
                    
                    queued_program_path, queued_cycle_checkpoints = render_runtime_queued_program_file(
                        path,
                        Path(self.config.analysis.output_dir),
                        self.config.checkpoints,
                        self.config.analysis.runs,
                        boundary_pair_start_index=next_boundary_pair_index,
                    )
                    ensure_program_loaded(queued_program_path)
                    queued_records, consumed_boundary_pairs = self._execute_queued_measurement_runs(
                        scenario,
                        queued_program_path,
                        queued_cycle_checkpoints,
                    )
                    next_boundary_pair_index += consumed_boundary_pairs
                    records.extend(queued_records)
                else:
                    steady_state_program_path, cycle_checkpoints = render_runtime_repeated_program_file(
                        path,
                        Path(self.config.analysis.output_dir),
                        self.config.checkpoints,
                        self._build_chained_program_cycle_count(),
                        name_suffix="steady_state",
                        boundary_pair_start_index=next_boundary_pair_index,
                    )
                    ensure_program_loaded(steady_state_program_path)
                    chained_records, chained_cycle_count = self._execute_chained_measurement_runs(
                        scenario,
                        steady_state_program_path,
                        cycle_checkpoints,
                        next_boundary_pair_index,
                    )
                    next_boundary_pair_index += chained_cycle_count
                    records.extend(chained_records)
        finally:
            self.robot_client.disconnect()

        return records

    def _execute_single_run(
        self,
        scenario: ScenarioProfile,
        run_index: int,
        rendered_program_path: Path,
        checkpoints,
        measurement_phase: str = "steady_state",
        include_in_summary: bool = True,
    ) -> RunRecord:
        self.robot_client.arm_checkpoints(checkpoints)
        run_start_time = monotonic()
        start_checkpoint_id = checkpoints[0].checkpoint_id if checkpoints else None
        end_checkpoint_id = checkpoints[-1].checkpoint_id if checkpoints else None
        self.robot_client.start_program(start_checkpoint_id, end_checkpoint_id)
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

        self.robot_client.wait_until_idle()

        metrics = build_run_metrics(
            scenario_name=self._analysis_name(scenario),
            run_index=run_index,
            checkpoint_labels=labels,
            checkpoint_times_s=elapsed,
            contingency_percent=self.config.analysis.contingency_percent,
            measurement_phase=measurement_phase,
        )
        return RunRecord(
            scenario=scenario,
            metrics=metrics,
            observations=observations,
            rendered_program_path=str(rendered_program_path),
            include_in_summary=include_in_summary,
        )

    def _wait_for_checkpoint_sequence(
        self,
        checkpoints: list[ExpectedCheckpoint],
        *,
        run_start_time: float,
    ) -> list[CheckpointObservation]:
        observations: list[CheckpointObservation] = []
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
            if observation.status != "reached":
                raise RunFailure(
                    f"Checkpoint {checkpoint.checkpoint_id} failed with status {observation.status}"
                )
        return observations

    def _build_record_from_observations(
        self,
        scenario: ScenarioProfile,
        run_index: int,
        measurement_phase: str,
        observations: list[CheckpointObservation],
        rendered_program_path: Path,
        *,
        include_in_summary: bool,
    ) -> RunRecord:
        metrics = build_run_metrics(
            scenario_name=self._analysis_name(scenario),
            run_index=run_index,
            checkpoint_labels=[observation.label or str(observation.checkpoint_id) for observation in observations],
            checkpoint_times_s=[observation.elapsed_s for observation in observations],
            contingency_percent=self.config.analysis.contingency_percent,
            measurement_phase=measurement_phase,
        )
        return RunRecord(
            scenario=scenario,
            metrics=metrics,
            observations=observations,
            rendered_program_path=str(rendered_program_path),
            include_in_summary=include_in_summary,
        )

    def _execute_continuous_program(
        self,
        scenario: ScenarioProfile,
        rendered_program_path: Path,
        cycle_checkpoints: list[list],
    ) -> list[list[CheckpointObservation]]:
        flattened_checkpoints = [checkpoint for cycle in cycle_checkpoints for checkpoint in cycle]
        self.robot_client.arm_checkpoints(flattened_checkpoints)
        run_start_time = monotonic()
        self.robot_client.start_program()

        all_observations: list[CheckpointObservation] = []
        for checkpoint in flattened_checkpoints:
            observation = validate_observation(self.robot_client.wait_for_checkpoint(checkpoint))
            all_observations.append(
                CheckpointObservation(
                    checkpoint_id=observation.checkpoint_id,
                    status=observation.status,
                    elapsed_s=monotonic() - run_start_time,
                    label=observation.label,
                    detail=observation.detail,
                )
            )
            if observation.status != "reached":
                raise RunFailure(
                    f"Checkpoint {checkpoint.checkpoint_id} failed with status {observation.status}"
                )

        self.robot_client.wait_until_idle()

        # Group observations by cycle using sequential matching.
        # This handles both traditional (remapped checkpoint IDs per cycle) and
        # StartProgram (repeated checkpoint IDs across cycles) execution models.
        observations_by_cycle: list[list[CheckpointObservation]] = []
        observation_index = 0
        
        for cycle in cycle_checkpoints:
            cycle_observations: list[CheckpointObservation] = []
            for checkpoint in cycle:
                if observation_index < len(all_observations):
                    cycle_observations.append(all_observations[observation_index])
                    observation_index += 1
            observations_by_cycle.append(cycle_observations)
        
        return observations_by_cycle

    @staticmethod
    def _normalize_cycle_observations(
        cycle_observations: list[CheckpointObservation],
    ) -> list[CheckpointObservation]:
        cycle_start_time = cycle_observations[0].elapsed_s
        return [
            CheckpointObservation(
                checkpoint_id=observation.checkpoint_id,
                status=observation.status,
                elapsed_s=observation.elapsed_s - cycle_start_time,
                label=observation.label,
                detail=observation.detail,
            )
            for observation in cycle_observations
        ]

    def _build_cycle_record(
        self,
        scenario: ScenarioProfile,
        run_index: int,
        measurement_phase: str,
        normalized_observations: list[CheckpointObservation],
        cycle,
        rendered_program_path: Path,
        *,
        include_in_summary: bool,
    ) -> RunRecord:
        metrics = build_run_metrics(
            scenario_name=self._analysis_name(scenario),
            run_index=run_index,
            checkpoint_labels=[checkpoint.label for checkpoint in cycle],
            checkpoint_times_s=[observation.elapsed_s for observation in normalized_observations],
            contingency_percent=self.config.analysis.contingency_percent,
            measurement_phase=measurement_phase,
        )
        return RunRecord(
            scenario=scenario,
            metrics=metrics,
            observations=normalized_observations,
            rendered_program_path=str(rendered_program_path),
            include_in_summary=include_in_summary,
        )

    def _build_chained_program_cycle_count(self) -> int:
        return self.config.analysis.runs + 2

    def _build_queued_program_cycle_count(self) -> int:
        return self.config.analysis.runs + 2

    def _execute_queued_measurement_runs(
        self,
        scenario: ScenarioProfile,
        rendered_program_path: Path,
        cycle_checkpoints: list[list],
    ) -> tuple[list[RunRecord], int]:
        records = self._execute_production_runs(
            scenario=scenario,
            rendered_program_path=rendered_program_path,
            cycle_checkpoints=cycle_checkpoints,
        )
        return records, self._build_queued_program_cycle_count()

    def _execute_chained_measurement_runs(
        self,
        scenario: ScenarioProfile,
        rendered_program_path: Path,
        cycle_checkpoints: list[list],
        boundary_pair_start_index: int,
    ) -> tuple[list[RunRecord], int]:
        records = self._execute_production_runs(
            scenario=scenario,
            rendered_program_path=rendered_program_path,
            cycle_checkpoints=cycle_checkpoints,
        )
        return records, self._build_chained_program_cycle_count()

    def _execute_production_runs(
        self,
        scenario: ScenarioProfile,
        rendered_program_path: Path,
        cycle_checkpoints: list[list],
    ) -> list[RunRecord]:
        cycle_observation_groups = self._execute_continuous_program(
            scenario,
            rendered_program_path,
            cycle_checkpoints,
        )
        records: list[RunRecord] = []
        for cycle_index, (cycle, cycle_observations) in enumerate(
            zip(cycle_checkpoints, cycle_observation_groups, strict=True),
            start=1,
        ):
            measurement_phase = "steady_state"
            include_in_summary = True
            run_index = cycle_index - 1
            if cycle_index == 1:
                measurement_phase = "accel_only"
                include_in_summary = False
                run_index = 0
            elif cycle_index == len(cycle_checkpoints):
                measurement_phase = "decel_only"
                include_in_summary = False
                run_index = 0
            records.append(
                self._build_cycle_record(
                    scenario,
                    run_index,
                    measurement_phase,
                    self._normalize_cycle_observations(cycle_observations),
                    cycle,
                    rendered_program_path,
                    include_in_summary=include_in_summary,
                )
            )
        return records

    def _build_dry_run_records(
        self,
        template_path: Path,
        rendered_program_path: Path,
    ) -> list[RunRecord]:
        records: list[RunRecord] = []
        next_boundary_pair_index = 0

        for scenario in self.config.scenarios:
            if self.config.analysis.alignment_run:
                startup_checkpoints = self._build_run_checkpoints(
                    self.config.checkpoints,
                    next_boundary_pair_index,
                )
                next_boundary_pair_index += 1
                checkpoint_labels = [checkpoint.label for checkpoint in startup_checkpoints]
                checkpoint_times = [float(index + 1) for index, _ in enumerate(startup_checkpoints)]
                startup_metrics = build_run_metrics(
                    scenario_name=self._analysis_name(scenario),
                    run_index=0,
                    checkpoint_labels=checkpoint_labels,
                    checkpoint_times_s=checkpoint_times,
                    contingency_percent=self.config.analysis.contingency_percent,
                    measurement_phase="single_run",
                )
                startup_observations = [
                    CheckpointObservation(
                        checkpoint_id=checkpoint.checkpoint_id,
                        status="reached",
                        elapsed_s=checkpoint_times[index],
                        label=checkpoint.label,
                    )
                    for index, checkpoint in enumerate(startup_checkpoints)
                ]
                records.append(
                    RunRecord(
                        scenario=scenario,
                        metrics=startup_metrics,
                        observations=startup_observations,
                        rendered_program_path=str(rendered_program_path),
                        include_in_summary=False,
                    )
                )

            if self._uses_queued_program_starts():
                queued_program_path, queued_cycle_checkpoints = render_runtime_queued_program_file(
                    template_path,
                    Path(self.config.analysis.output_dir),
                    self.config.checkpoints,
                    self.config.analysis.runs,
                    boundary_pair_start_index=next_boundary_pair_index,
                )
                next_boundary_pair_index += self._build_queued_program_cycle_count()

                for cycle_index, cycle in enumerate(queued_cycle_checkpoints, start=1):
                    cycle_times = [float(index) for index, _ in enumerate(cycle)]
                    measurement_phase = "steady_state"
                    include_in_summary = True
                    run_index = cycle_index - 1
                    if cycle_index == 1:
                        measurement_phase = "accel_only"
                        include_in_summary = False
                        run_index = 0
                    elif cycle_index == len(queued_cycle_checkpoints):
                        measurement_phase = "decel_only"
                        include_in_summary = False
                        run_index = 0
                    records.append(
                        self._build_cycle_record(
                            scenario,
                            run_index,
                            measurement_phase,
                            [
                                CheckpointObservation(
                                    checkpoint_id=checkpoint.checkpoint_id,
                                    status="reached",
                                    elapsed_s=cycle_times[index],
                                    label=checkpoint.label,
                                )
                                for index, checkpoint in enumerate(cycle)
                            ],
                            cycle,
                            queued_program_path,
                            include_in_summary=include_in_summary,
                        )
                    )
                continue

            for _ in range(self.config.analysis.warmup_runs):
                next_boundary_pair_index += 1

            steady_state_program_path, cycle_checkpoints = render_runtime_repeated_program_file(
                template_path,
                Path(self.config.analysis.output_dir),
                self.config.checkpoints,
                self._build_chained_program_cycle_count(),
                name_suffix="steady_state",
                boundary_pair_start_index=next_boundary_pair_index,
            )
            next_boundary_pair_index += self._build_chained_program_cycle_count()

            for cycle_index, cycle in enumerate(cycle_checkpoints, start=1):
                cycle_times = [float(index) for index, _ in enumerate(cycle)]
                measurement_phase = "steady_state"
                include_in_summary = True
                run_index = cycle_index - 1
                if cycle_index == 1:
                    measurement_phase = "accel_only"
                    include_in_summary = False
                    run_index = 0
                elif cycle_index == len(cycle_checkpoints):
                    measurement_phase = "decel_only"
                    include_in_summary = False
                    run_index = 0
                records.append(
                    self._build_cycle_record(
                        scenario,
                        run_index,
                        measurement_phase,
                        [
                            CheckpointObservation(
                                checkpoint_id=checkpoint.checkpoint_id,
                                status="reached",
                                elapsed_s=cycle_times[index],
                                label=checkpoint.label,
                            )
                            for index, checkpoint in enumerate(cycle)
                        ],
                        cycle,
                        steady_state_program_path,
                        include_in_summary=include_in_summary,
                    )
                )

        return records
