from pathlib import Path

from mecademic_cycle_report.program_template import (
    ProgramTemplateError,
    render_program_file,
    render_program_text,
    wrap_program_text,
)
from mecademic_cycle_report.scenario_matrix import ScenarioProfile


def test_render_program_text_replaces_top_level_and_variable_placeholders() -> None:
    scenario = ScenarioProfile(
        name="baseline",
        gripper_open_delay_s=0.2,
        variables={"cycle_speed": 80},
    )

    rendered = render_program_text(
        "SetTimeScaling({{ cycle_speed }})\nDelay({{ gripper_open_delay_s }})\n",
        scenario,
    )

    assert "SetTimeScaling(80)" in rendered
    assert "Delay(0.2)" in rendered


def test_render_program_text_rejects_unknown_placeholder() -> None:
    try:
        render_program_text("Delay({{ missing_value }})", ScenarioProfile(name="baseline"))
    except ProgramTemplateError as exc:
        assert "Unknown template placeholder" in str(exc)
    else:
        raise AssertionError("Expected unknown placeholder to fail")


def test_render_program_file_writes_scenario_specific_output(tmp_path: Path) -> None:
    template_path = tmp_path / "input.mxprog"
    template_path.write_text("Delay({{ gripper_close_delay_s }})", encoding="utf-8")

    output_path = render_program_file(
        template_path,
        ScenarioProfile(name="slow", gripper_close_delay_s=0.4),
        tmp_path / "artifacts",
    )

    assert output_path.name == "input__slow.mxprog"
    assert output_path.read_text(encoding="utf-8") == "Delay(0.4)\n"


def test_wrap_program_text_adds_boundary_checkpoints() -> None:
    wrapped = wrap_program_text("MovePose(1, 2, 3, 4, 5, 6)\n", None, 101, 102)

    assert wrapped == "SetCheckpoint(101)\nMovePose(1, 2, 3, 4, 5, 6)\nSetCheckpoint(102)\n"


def test_wrap_program_text_sets_variables_before_boundary_checkpoint() -> None:
    wrapped = wrap_program_text(
        "MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\n",
        ScenarioProfile(name="baseline", variables={"PICK_X": 12.5, "PICK_Y": -18.0, "USE_PART": True}),
        101,
        102,
    )

    assert wrapped == (
        "SetVariable(PICK_X, 12.5)\n"
        "SetVariable(PICK_Y, -18.0)\n"
        "SetVariable(USE_PART, true)\n"
        "SetCheckpoint(101)\n"
        "MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\n"
        "SetCheckpoint(102)\n"
    )


def test_render_program_file_wraps_rendered_program_with_boundary_checkpoints(tmp_path: Path) -> None:
    template_path = tmp_path / "input.mxprog"
    template_path.write_text("Delay({{ gripper_close_delay_s }})\n", encoding="utf-8")

    output_path = render_program_file(
        template_path,
        ScenarioProfile(name="slow", gripper_close_delay_s=0.4),
        tmp_path / "artifacts",
        start_checkpoint_id=101,
        end_checkpoint_id=102,
    )

    assert output_path.read_text(encoding="utf-8") == "SetCheckpoint(101)\nDelay(0.4)\nSetCheckpoint(102)\n"


def test_render_program_file_includes_variable_assignments_before_program_start(tmp_path: Path) -> None:
    template_path = tmp_path / "input.mxprog"
    template_path.write_text("MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\n", encoding="utf-8")

    output_path = render_program_file(
        template_path,
        ScenarioProfile(name="baseline", variables={"PICK_X": 12.5, "PICK_Y": -18.0}),
        tmp_path / "artifacts",
        start_checkpoint_id=101,
        end_checkpoint_id=102,
    )

    assert output_path.read_text(encoding="utf-8") == (
        "SetVariable(PICK_X, 12.5)\n"
        "SetVariable(PICK_Y, -18.0)\n"
        "SetCheckpoint(101)\n"
        "MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)\n"
        "SetCheckpoint(102)\n"
    )