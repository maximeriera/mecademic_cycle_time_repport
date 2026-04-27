from pathlib import Path

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

    assert robot.calls == [
        "SetTimeScaling:100.0",
        "SetBlending:100.0",
        "SetJointAcc:100.0",
        "SetCartAcc:100.0",
        "CreateVariable:PICK_X:35:0:0",
        "SetVariable:PICK_X:35",
        "CreateVariable:GRP_DELAY:0.15:0:0",
        "SetVariable:GRP_DELAY:0.15",
    ]
