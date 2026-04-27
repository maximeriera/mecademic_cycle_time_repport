from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any, Protocol

from .checkpoint_spec import CheckpointObservation, ExpectedCheckpoint
from .scenario_matrix import ScenarioProfile

try:
    import mecademicpy.robot as mdr
    import mecademicpy.robot_initializer as initializer
except ImportError:  # pragma: no cover - exercised when dependency is absent
    mdr = None
    initializer = None


class RobotClientError(RuntimeError):
    """Raised when the robot adapter cannot complete an operation."""


class RobotClient(Protocol):
    def connect(self) -> None: ...

    def ensure_ready(self) -> None: ...

    def load_program(self, mxprog_path: Path) -> None: ...

    def apply_scenario(self, scenario: ScenarioProfile) -> None: ...

    def arm_checkpoints(self, checkpoints: list[ExpectedCheckpoint]) -> None: ...

    def start_program(self) -> None: ...

    def wait_for_checkpoint(self, checkpoint: ExpectedCheckpoint) -> CheckpointObservation: ...

    def get_runtime_details(self) -> dict[str, Any]: ...

    def disconnect(self) -> None: ...


@dataclass(slots=True)
class UnimplementedMecademicClient:
    """Placeholder until the Mecademic SDK package/API surface is pinned down."""

    robot_address: str

    def get_runtime_details(self) -> dict[str, Any]:
        return {
            "client": "unimplemented",
            "robot_address": self.robot_address,
            "dry_run": True,
            "enforce_sim_mode": True,
        }

    def connect(self) -> None:
        raise RobotClientError(
            "Mecademic SDK integration is not implemented yet. Use --dry-run for now."
        )

    def ensure_ready(self) -> None:
        raise RobotClientError("Robot readiness checks are not implemented yet")

    def load_program(self, mxprog_path: Path) -> None:
        raise RobotClientError(f"Program loading is not implemented yet: {mxprog_path}")

    def apply_scenario(self, scenario: ScenarioProfile) -> None:
        raise RobotClientError(f"Scenario application is not implemented yet: {scenario.name}")

    def arm_checkpoints(self, checkpoints: list[ExpectedCheckpoint]) -> None:
        raise RobotClientError(
            f"Checkpoint arming is not implemented yet: {len(checkpoints)} checkpoints"
        )

    def start_program(self) -> None:
        raise RobotClientError("Program start is not implemented yet")

    def wait_for_checkpoint(self, checkpoint: ExpectedCheckpoint) -> CheckpointObservation:
        raise RobotClientError(
            f"Checkpoint waiting is not implemented yet: {checkpoint.checkpoint_id}"
        )

    def disconnect(self) -> None:
        return None


@dataclass(slots=True)
class MecademicPyRobotClient:
    """Adapter around the official mecademicpy client."""

    robot_address: str
    enforce_sim_mode: bool = True
    robot: Any | None = None
    current_program_name: str | None = None
    checkpoint_events: dict[int, Any] | None = None
    discarded_checkpoint_ids: set[int] | None = None
    last_program_load_method: str | None = None
    initial_status: dict[str, Any] | None = None
    ready_status: dict[str, Any] | None = None
    deactivated_for_sim: bool = False

    ENFORCED_TIME_SCALING_PERCENT = 100.0
    ENFORCED_BLENDING_PERCENT = 100.0
    ENFORCED_JOINT_ACCELERATION_PERCENT = 100.0
    ENFORCED_CARTESIAN_ACCELERATION_PERCENT = 100.0

    def connect(self) -> None:
        if mdr is None or initializer is None:
            raise RobotClientError(
                "mecademicpy is not installed. Install dependencies before running against hardware."
            )
        if self.robot is not None:
            return

        self.robot = initializer.RobotWithTools()
        self.robot.Connect(address=self.robot_address, disconnect_on_exception=False)
        self.discarded_checkpoint_ids = set()
        self.checkpoint_events = {}
        self.initial_status = self._status_to_dict(self.robot.GetStatusRobot(synchronous_update=True))
        self.robot.RegisterCallback("on_checkpoint_discarded", self._on_checkpoint_discarded)

    def ensure_ready(self) -> None:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        status = self._reset_error_state_if_needed()
        if self.enforce_sim_mode:
            if getattr(status, "activation_state", False):
                self.deactivated_for_sim = True
                self.robot.DeactivateRobot()
                self.robot.WaitDeactivated()
            self.robot.ActivateSim()
            self.robot.WaitSimActivated()
        elif getattr(status, "simulation_mode", 0):
            if getattr(status, "activation_state", False):
                self.robot.DeactivateRobot()
                self.robot.WaitDeactivated()
            self.robot.DeactivateSim()
            self.robot.WaitSimDeactivated()
        self.robot.ActivateRobot()
        self.robot.WaitActivated()
        self.robot.Home()
        self.robot.WaitHomed()
        self.robot.WaitIdle()
        self.ready_status = self._status_to_dict(self.robot.GetStatusRobot(synchronous_update=True))

    def load_program(self, mxprog_path: Path) -> None:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        content = mxprog_path.read_text(encoding="utf-8")
        self.current_program_name = mxprog_path.name
        self.robot.SaveFile(self.current_program_name, content, overwrite=True)
        self.robot.LoadProgram(self.current_program_name)
        self.last_program_load_method = "LoadProgram"

    def apply_scenario(self, scenario: ScenarioProfile) -> None:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        self.robot.SetTimeScaling(self.ENFORCED_TIME_SCALING_PERCENT)
        self.robot.SetBlending(self.ENFORCED_BLENDING_PERCENT)
        self.robot.SetJointAcc(self.ENFORCED_JOINT_ACCELERATION_PERCENT)
        self.robot.SetCartAcc(self.ENFORCED_CARTESIAN_ACCELERATION_PERCENT)
        for variable_name, value in scenario.variables.items():
            self.robot.CreateVariable(variable_name, value, 0, 0)
            self.robot.SetVariable(variable_name, value)

    def arm_checkpoints(self, checkpoints: list[ExpectedCheckpoint]) -> None:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        if self.checkpoint_events is None or self.discarded_checkpoint_ids is None:
            raise RobotClientError("Robot checkpoint state is not initialized")

        self.checkpoint_events.clear()
        self.discarded_checkpoint_ids.clear()
        for checkpoint in checkpoints:
            self.checkpoint_events[checkpoint.checkpoint_id] = self.robot.ExpectExternalCheckpoint(
                checkpoint.checkpoint_id
            )

    def start_program(self) -> None:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        if not self.current_program_name:
            raise RobotClientError("No program is loaded")
        self.robot.StartProgram(self.current_program_name)

    def wait_for_checkpoint(self, checkpoint: ExpectedCheckpoint) -> CheckpointObservation:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        if not self.checkpoint_events or checkpoint.checkpoint_id not in self.checkpoint_events:
            raise RobotClientError(
                f"Checkpoint {checkpoint.checkpoint_id} was not armed before program start"
            )

        checkpoint_event = self.checkpoint_events[checkpoint.checkpoint_id]
        start_time = monotonic()
        try:
            checkpoint_event.wait(timeout=checkpoint.timeout_s)
        except mdr.TimeoutException:
            return CheckpointObservation(
                checkpoint_id=checkpoint.checkpoint_id,
                status="timeout",
                elapsed_s=monotonic() - start_time,
                label=checkpoint.label,
                detail="Timed out waiting for checkpoint",
            )
        except mdr.InterruptException as exc:
            detail = str(exc)
            if self.discarded_checkpoint_ids and checkpoint.checkpoint_id in self.discarded_checkpoint_ids:
                detail = f"Checkpoint {checkpoint.checkpoint_id} was discarded"
            return CheckpointObservation(
                checkpoint_id=checkpoint.checkpoint_id,
                status="discarded",
                elapsed_s=monotonic() - start_time,
                label=checkpoint.label,
                detail=detail,
            )

        return CheckpointObservation(
            checkpoint_id=checkpoint.checkpoint_id,
            status="reached",
            elapsed_s=monotonic() - start_time,
            label=checkpoint.label,
        )

    def disconnect(self) -> None:
        if self.robot is None:
            return
        try:
            if self.robot.IsConnected():
                self.robot.Disconnect()
        finally:
            self.robot = None
            self.current_program_name = None
            self.checkpoint_events = None
            self.discarded_checkpoint_ids = None

    def get_runtime_details(self) -> dict[str, Any]:
        return {
            "client": "mecademicpy",
            "robot_address": self.robot_address,
            "dry_run": False,
            "enforce_sim_mode": self.enforce_sim_mode,
            "deactivated_for_sim": self.deactivated_for_sim,
            "program_load_method": self.last_program_load_method,
            "initial_status": self.initial_status,
            "ready_status": self.ready_status,
        }

    def _on_checkpoint_discarded(self, checkpoint_id: int) -> None:
        if self.discarded_checkpoint_ids is None:
            self.discarded_checkpoint_ids = set()
        self.discarded_checkpoint_ids.add(checkpoint_id)

    def _reset_error_state_if_needed(self) -> Any:
        if self.robot is None:
            raise RobotClientError("Robot client is not connected")
        status = self.robot.GetStatusRobot(synchronous_update=True)
        if getattr(status, "error_status", False):
            self.robot.ResetError()
            self.robot.WaitErrorReset()
            status = self.robot.GetStatusRobot(synchronous_update=True)
        return status

    @staticmethod
    def _status_to_dict(status: Any) -> dict[str, Any]:
        return {
            "activation_state": bool(getattr(status, "activation_state", False)),
            "homing_state": bool(getattr(status, "homing_state", False)),
            "simulation_mode": int(getattr(status, "simulation_mode", 0)),
            "recovery_mode": bool(getattr(status, "recovery_mode", False)),
            "error_status": bool(getattr(status, "error_status", False)),
            "pause_motion_status": bool(getattr(status, "pause_motion_status", False)),
            "motion_cleared_status": bool(getattr(status, "motion_cleared_status", False)),
            "end_of_block_status": bool(getattr(status, "end_of_block_status", False)),
            "brakes_engaged": bool(getattr(status, "brakes_engaged", False)),
            "connection_watchdog_enabled": bool(
                getattr(status, "connection_watchdog_enabled", False)
            ),
        }

def create_robot_client(
    robot_address: str,
    *,
    dry_run: bool,
    enforce_sim_mode: bool = True,
) -> RobotClient:
    if dry_run:
        return UnimplementedMecademicClient(robot_address)
    return MecademicPyRobotClient(robot_address, enforce_sim_mode=enforce_sim_mode)
