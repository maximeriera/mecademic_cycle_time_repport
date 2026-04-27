# Example Usage

This document shows concrete ways to run the Mecademic cycle time analyzer with your own `.mxprog` and config files.

The files under `tests/fixtures` are repository samples only. They are useful as references, but they are not intended to be the place where users store production programs.

## Prerequisites

Install the package in editable mode:

```powershell
pip install -e .[dev]
```

On Windows, if you want to call the CLI through the workspace virtual environment explicitly, you can also use:

```powershell
.venv\Scripts\python.exe -m mecademic_cycle_report.cli --help
```

Recommended layout in your own workspace:

```text
programs/
	my_process.mxprog
configs/
	my_process.scenarios.yaml
reports/
```

## 1. Validate a Scenario Config

Use this before a run to catch invalid config structure or missing required fields.

```powershell
mecademic-cycle-report validate-config configs/my_process.scenarios.yaml
```

Equivalent module invocation:

```powershell
.venv\Scripts\python.exe -m mecademic_cycle_report.cli validate-config configs/my_process.scenarios.yaml
```

## 2. Run a Dry Analysis

Dry-run mode builds the scenario matrix and report payload without talking to a robot.

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --dry-run
```

This is the safest way to verify:

- the config loads correctly
- checkpoints are defined in the expected order
- scenario variables expand as intended
- report artifacts are generated in the configured output folder

## 3. Print the Full Report as JSON

Useful for automation or quick inspection from the terminal.

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --dry-run --json
```

## 4. Run a Real Program With Simulation Enforced

If the config enables simulation mode, or you want to force it from the command line:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --enforce-sim-mode
```

Use this when you want the controller in Mecademic simulation mode before homing and execution.

## 5. Run a Real Program Without Simulation Enforcement

Use this only when you intentionally want to execute against the real robot state.

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --no-enforce-sim-mode
```

If you want concrete examples from this repository, inspect `tests/fixtures/test_RBT1.*` and `tests/fixtures/test_RBT2.*`, then copy that structure into your own program and config files.

## 6. Example With the Current Workspace Virtual Environment

This is the exact command style used in this repository when running from PowerShell on Windows:

```powershell
.venv\Scripts\python.exe -m mecademic_cycle_report.cli analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml
```

## 7. Generated Artifacts

After `analyze`, the tool writes report artifacts to the configured output directory.

Typical outputs are:

- `report.json`
- `report.md`
- `records.csv`
- `scenario_summary.csv`
- `rendered_programs/*.mxprog`

These rendered programs include:

- scenario variable assignments
- a synthetic `program_start` checkpoint
- the original program body
- a synthetic `program_end` checkpoint

## 8. Common Workflows

### Check a config before touching hardware

```powershell
mecademic-cycle-report validate-config configs/my_process.scenarios.yaml
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --dry-run
```

### Run a real measurement on RBT1-style studies

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --no-enforce-sim-mode
```

### Run a simulation-backed sensitivity study

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --enforce-sim-mode
```

## 9. Repository Samples

This repository includes sample programs and configs under `tests/fixtures` for development and regression testing.

Examples:

- `tests/fixtures/test_RBT1.mxprog`
- `tests/fixtures/test_RBT1.scenarios.yaml`
- `tests/fixtures/test_RBT2.mxprog`
- `tests/fixtures/test_RBT2.scenarios.yaml`

Use them as reference material, not as the normal storage location for your own robot programs.

## 10. Notes on What the Tool Measures

The total cycle time is measured as the delta between the synthetic wrapper checkpoints:

- `program_start`
- `program_end`

Any checkpoints inside the original `.mxprog` are still recorded and used for segment-level timing inside that execution window.

## 11. Troubleshooting

If a run fails early, check these first:

- the robot IP address in the config
- whether simulation mode should be forced or explicitly disabled
- whether the program references `vars.NAME` values missing from a scenario
- whether the checkpoints listed in the config match the checkpoints expected inside the original program body

If you only need to inspect scenario expansion or artifact generation, prefer `--dry-run` first.