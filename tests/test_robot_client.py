from pathlib import Path

from mecademic_cycle_report.checkpoint_spec import ExpectedCheckpoint
from mecademic_cycle_report.scenario_matrix import ScenarioProfile
from mecademic_cycle_report.robot_client import MecademicPyRobotClient, RobotClientError


class FakeSdkRobot:
    def __init__(
        self,
        *,
        error_status: bool = False,
        activation_state: bool = False,
        simulation_mode: int = 0,
    ) -> None:
        self.calls: list[str] = []
        self.error_status = error_status
        self.activation_state = activation_state
        self.simulation_mode = simulation_mode

    def GetStatusRobot(self, synchronous_update: bool = False):
        self.calls.append(f"GetStatusRobot:{synchronous_update}")

        class Status:
            def __init__(self, error_status: bool, activation_state: bool, simulation_mode: int) -> None:
                self.error_status = error_status
                self.activation_state = activation_state
                self.simulation_mode = simulation_mode

        return Status(self.error_status, self.activation_state, self.simulation_mode)

    def ResetError(self) -> None:
        self.calls.append("ResetError")
        self.error_status = False

    def WaitErrorReset(self) -> None:
        self.calls.append("WaitErrorReset")

    def DeactivateRobot(self) -> None:
        self.calls.append("DeactivateRobot")
        self.activation_state = False

    def WaitDeactivated(self) -> None:
        self.calls.append("WaitDeactivated")

    def ActivateSim(self) -> None:
        self.calls.append("ActivateSim")
        self.simulation_mode = 1

    def WaitSimActivated(self) -> None:
        self.calls.append("WaitSimActivated")

    def DeactivateSim(self) -> None:
        self.calls.append("DeactivateSim")
        self.simulation_mode = 0

    def WaitSimDeactivated(self) -> None:
        self.calls.append("WaitSimDeactivated")

    def ActivateRobot(self) -> None:
        self.calls.append("ActivateRobot")
        self.activation_state = True

    def WaitActivated(self) -> None:
        self.calls.append("WaitActivated")

    def Home(self) -> None:
        self.calls.append("Home")

    def WaitHomed(self) -> None:
        self.calls.append("WaitHomed")

    def WaitIdle(self) -> None:
        self.calls.append("WaitIdle")


class FakeProgramRobot:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def SaveFile(self, name: str, content: str, overwrite: bool = False) -> None:
        self.calls.append(f"SaveFile:{name}:{overwrite}:{bool(content)}")

    def LoadProgram(self, name: str) -> None:
        self.calls.append(f"LoadProgram:{name}")

    def SetCheckpoint(self, checkpoint_id: int) -> None:
        self.calls.append(f"SetCheckpoint:{checkpoint_id}")

    def StartProgram(self, name: str) -> None:
        self.calls.append(f"StartProgram:{name}")


class FakeScenarioRobot:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def SetTimeScaling(self, value: float) -> None:
        self.calls.append(f"SetTimeScaling:{value}")

    def SetBlending(self, value: float) -> None:
        self.calls.append(f"SetBlending:{value}")

    def SetJointAcc(self, value: float) -> None:
        self.calls.append(f"SetJointAcc:{value}")

    def SetCartAcc(self, value: float) -> None:
        self.calls.append(f"SetCartAcc:{value}")

    def CreateVariable(self, name: str, value, cyclic_id: int = 0, override: int = 0) -> None:
        self.calls.append(f"CreateVariable:{name}:{value}:{cyclic_id}:{override}")

    def SetVariable(self, name: str, value) -> None:
        self.calls.append(f"SetVariable:{name}:{value}")


class FakeDisconnectRobot:
    def __init__(self, *, fail_wait_idle: bool = False, connected: bool = True) -> None:
        self.calls: list[str] = []
        self.fail_wait_idle = fail_wait_idle
        self.connected = connected

    def IsConnected(self) -> bool:
        self.calls.append("IsConnected")
        return self.connected

    def WaitIdle(self) -> None:
        self.calls.append("WaitIdle")
        if self.fail_wait_idle:
            raise RuntimeError("simulated wait idle failure")

    def Disconnect(self) -> None:
        self.calls.append("Disconnect")


class FakeCheckpointEvent:
    def __init__(self, event_name: str, call_log: list[str]) -> None:
        self.event_name = event_name
        self.call_log = call_log

    def wait(self, timeout: float | None = None) -> None:
        self.call_log.append(f"wait:{self.event_name}:{timeout}")


class FakeCheckpointRobot:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.wait_calls: list[str] = []
        self._event_index = 0

    def ExpectExternalCheckpoint(self, checkpoint_id: int) -> FakeCheckpointEvent:
        self._event_index += 1
        event_name = f"cp{checkpoint_id}#{self._event_index}"
        self.calls.append(f"ExpectExternalCheckpoint:{event_name}")
        return FakeCheckpointEvent(event_name, self.wait_calls)


def test_ensure_ready_enforces_sim_mode_before_homing() -> None:
    robot = FakeSdkRobot()
    client = MecademicPyRobotClient(
        robot_address="192.168.0.100",
        enforce_sim_mode=True,
        robot=robot,
    )

    client.ensure_ready()

    assert robot.calls == [
        "GetStatusRobot:True",
        "ActivateSim",
        "WaitSimActivated",
        "ActivateRobot",
        "WaitActivated",
        "Home",
        "WaitHomed",
        "WaitIdle",
        "GetStatusRobot:True",
    ]


def test_ensure_ready_can_skip_sim_mode_when_disabled() -> None:
    robot = FakeSdkRobot()
    client = MecademicPyRobotClient(
        robot_address="192.168.0.100",
        enforce_sim_mode=False,
        robot=robot,
    )

    client.ensure_ready()

    assert robot.calls == [
        "GetStatusRobot:True",
        "ActivateRobot",
        "WaitActivated",
        "Home",
        "WaitHomed",
        "WaitIdle",
        "GetStatusRobot:True",
    ]


def test_ensure_ready_deactivates_sim_mode_when_disabled() -> None:
    robot = FakeSdkRobot(simulation_mode=1)
    client = MecademicPyRobotClient(
        robot_address="192.168.0.100",
        enforce_sim_mode=False,
        robot=robot,
    )

    client.ensure_ready()

    assert robot.calls == [
        "GetStatusRobot:True",
        "DeactivateSim",
        "WaitSimDeactivated",
        "ActivateRobot",
        "WaitActivated",
        "Home",
        "WaitHomed",
        "WaitIdle",
        "GetStatusRobot:True",
    ]


def test_ensure_ready_requires_connection() -> None:
    client = MecademicPyRobotClient(robot_address="192.168.0.100")

    try:
        client.ensure_ready()
    except RobotClientError as exc:
        assert "not connected" in str(exc)
    else:
        raise AssertionError("Expected ensure_ready to fail when robot is missing")


def test_ensure_ready_resets_error_before_homing() -> None:
    robot = FakeSdkRobot(error_status=True)
    client = MecademicPyRobotClient(
        robot_address="192.168.0.100",
        enforce_sim_mode=True,
        robot=robot,
    )

    client.ensure_ready()

    assert robot.calls == [
        "GetStatusRobot:True",
        "ResetError",
        "WaitErrorReset",
        "GetStatusRobot:True",
        "ActivateSim",
        "WaitSimActivated",
        "ActivateRobot",
        "WaitActivated",
        "Home",
        "WaitHomed",
        "WaitIdle",
        "GetStatusRobot:True",
    ]


def test_ensure_ready_deactivates_before_enabling_sim_mode() -> None:
    robot = FakeSdkRobot(activation_state=True)
    client = MecademicPyRobotClient(
        robot_address="192.168.0.100",
        enforce_sim_mode=True,
        robot=robot,
    )

    client.ensure_ready()

    assert robot.calls == [
        "GetStatusRobot:True",
        "DeactivateRobot",
        "WaitDeactivated",
        "ActivateSim",
        "WaitSimActivated",
        "ActivateRobot",
        "WaitActivated",
        "Home",
        "WaitHomed",
        "WaitIdle",
        "GetStatusRobot:True",
    ]


def test_load_program_uses_load_program_after_save_file(tmp_path: Path) -> None:
    mxprog_path = tmp_path / "program.mxprog"
    mxprog_path.write_text("SetCheckpoint(1)\n", encoding="utf-8")
    robot = FakeProgramRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)

    client.load_program(mxprog_path)

    assert robot.calls == [
        "SaveFile:program.mxprog:True:True",
        "LoadProgram:program.mxprog",
    ]


def test_load_program_shortens_robot_file_name_when_rendered_name_is_too_long(tmp_path: Path) -> None:
    mxprog_path = tmp_path / (
        "test_RBT2__baseline_variables_SPD_INSERT_plus10pct__accel_decel.mxprog"
    )
    mxprog_path.write_text("SetCheckpoint(1)\n", encoding="utf-8")
    robot = FakeProgramRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)

    client.load_program(mxprog_path)

    assert len(client.current_program_name or "") <= 63
    assert client.current_program_name.endswith(".mxprog")
    assert robot.calls == [
        f"SaveFile:{client.current_program_name}:True:True",
        f"LoadProgram:{client.current_program_name}",
    ]


def test_start_program_sets_boundary_checkpoints_around_program_start() -> None:
    robot = FakeProgramRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)
    client.current_program_name = "program.mxprog"

    client.start_program(7000, 7001)

    assert robot.calls == [
        "SetCheckpoint:7000",
        "StartProgram:program.mxprog",
        "SetCheckpoint:7001",
    ]


def test_apply_scenario_creates_missing_variables_before_setting_values() -> None:
    robot = FakeScenarioRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)

    client.apply_scenario(
        ScenarioProfile(
            name="baseline",
            variables={
                "PICK_X": 35,
                "GRP_DELAY": 0.15,
            },
        )
    )

    assert robot.calls[:4] == [
        "SetTimeScaling:100.0",
        "SetBlending:100.0",
        "SetJointAcc:100.0",
        "SetCartAcc:100.0",
    ]
    assert "CreateVariable:PICK_X:35:0:0" in robot.calls
    assert "SetVariable:PICK_X:35" in robot.calls
    assert "CreateVariable:GRP_DELAY:0.15:0:0" in robot.calls
    assert "SetVariable:GRP_DELAY:0.15" in robot.calls
    assert "CreateVariable:MCR_SCENARIO_NAME:baseline:0:0" in robot.calls
    assert "SetVariable:MCR_SCENARIO_NAME:baseline" in robot.calls
    assert "CreateVariable:MCR_GRIPPER_CLOSE_DELAY_S:0.0:0:0" in robot.calls
    assert "SetVariable:MCR_GRIPPER_CLOSE_DELAY_S:0.0" in robot.calls


def test_disconnect_waits_idle_before_disconnect() -> None:
    robot = FakeDisconnectRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)

    client.disconnect()

    assert robot.calls == ["IsConnected", "WaitIdle", "Disconnect"]
    assert client.robot is None


def test_disconnect_still_disconnects_when_wait_idle_fails() -> None:
    robot = FakeDisconnectRobot(fail_wait_idle=True)
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)

    client.disconnect()

    assert robot.calls == ["IsConnected", "WaitIdle", "Disconnect"]
    assert client.robot is None


def test_wait_for_checkpoint_consumes_duplicate_checkpoint_events_in_order() -> None:
    robot = FakeCheckpointRobot()
    client = MecademicPyRobotClient(robot_address="192.168.0.100", robot=robot)
    client.checkpoint_events = {}
    client.discarded_checkpoint_ids = set()

    checkpoints = [
        ExpectedCheckpoint(checkpoint_id=1, label="first"),
        ExpectedCheckpoint(checkpoint_id=1, label="second"),
    ]
    client.arm_checkpoints(checkpoints)

    first_observation = client.wait_for_checkpoint(checkpoints[0])
    second_observation = client.wait_for_checkpoint(checkpoints[1])

    assert first_observation.status == "reached"
    assert second_observation.status == "reached"
    assert robot.calls == [
        "ExpectExternalCheckpoint:cp1#1",
        "ExpectExternalCheckpoint:cp1#2",
    ]
    assert robot.wait_calls == [
        "wait:cp1#1:None",
        "wait:cp1#2:None",
    ]
