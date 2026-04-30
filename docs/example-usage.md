# Example Usage

This guide is organized as the normal user workflow:

1. place your `.mxprog` in your own workspace
2. generate a starter scenario file
3. edit the scenario file
4. run the analysis
5. inspect the report

The files under `tests/fixtures` are repository samples only. They are useful as references, but they are not intended to be the place where users store production programs.

To start from a hand-edited config instead of a generated one, see `docs/scenarios-template.yaml`.

## Prerequisites

Install the package in editable mode:

```powershell
pip install -e .[dev]
```

On Windows, you can also call the CLI explicitly through the workspace virtual environment:

```powershell
.venv\Scripts\python.exe -m mecademic_cycle_report.cli --help
```

Recommended workspace layout:

```text
programs/
	my_process.mxprog
configs/
	my_process.scenarios.yaml
reports/
```

## Step 1: Put Your `.mxprog` In Your Workspace

Store your own program in a user-owned folder such as `programs/`:

```text
programs/my_process.mxprog
```

If you have several programs, put them all in the same folder:

```text
programs/
	cell_a.mxprog
	cell_b.mxprog
	cell_c.mxprog
```

## Step 2: Generate Starter Scenario Files

Generate one starter scenario config per `.mxprog` file:

```powershell
mecademic-cycle-report generate-scenarios programs --output-dir configs/generated
```

This creates files such as:

- `configs/generated/cell_a.scenarios.yaml`
- `configs/generated/cell_b.scenarios.yaml`
- `configs/generated/cell_c.scenarios.yaml`

The generated files include:

- detected `SetCheckpoint(...)` ids
- detected `vars.NAME` variable references
- a single `baseline` scenario
- `__TODO__` placeholders for the variable values you still need to define

By default, the generated `analysis.output_dir` mirrors the scenario-file folder structure under `artifacts/`. For example, `configs/generated/my_process.scenarios.yaml` defaults to `artifacts/generated/my_process`.

Useful optional overrides:

```powershell
mecademic-cycle-report generate-scenarios programs --output-dir configs/generated --robot-address 192.168.0.100 --no-enforce-sim-mode --analysis-output-root artifacts/generated
```

## Step 3: Edit The Generated Scenario File

Open the generated file for your program, for example:

```text
configs/generated/my_process.scenarios.yaml
```

Then update it before running anything:

- replace every `__TODO__` value with a real value used by your program
- review the auto-generated checkpoint labels and rename them to something meaningful
- set the correct robot address
- decide whether `enforce_sim_mode` should stay `true` or be set to `false`
- add more scenario profiles if you want comparisons such as `baseline`, `fast`, or `cautious`
- add optional `sweep`, `perturbations`, or `variable_cases` only if you need them

If you prefer to start from a clean hand-written config, copy `docs/scenarios-template.yaml` to `configs/my_process.scenarios.yaml` and edit it directly.

## Step 4: Validate The Scenario File

Validate the edited config before running analysis:

```powershell
mecademic-cycle-report validate-config configs/generated/my_process.scenarios.yaml
```

Equivalent module invocation:

```powershell
.venv\Scripts\python.exe -m mecademic_cycle_report.cli validate-config configs/generated/my_process.scenarios.yaml
```

Note:

- validation will fail if `__TODO__` placeholders are still present
- validation will fail if required config sections are missing or malformed

## Step 5: Run The Analysis

Start with a dry run to check the scenario expansion and report generation without talking to the robot:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/generated/my_process.scenarios.yaml --dry-run
```

Then run against the robot when ready.

Run with simulation enforced:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/generated/my_process.scenarios.yaml --enforce-sim-mode
```

Run without simulation enforcement:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/generated/my_process.scenarios.yaml --no-enforce-sim-mode
```

If you want the raw report payload in the terminal:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/generated/my_process.scenarios.yaml --dry-run --json
```

## Step 6: Inspect The Report

After `analyze`, the tool writes report artifacts to the configured output directory.

Typical outputs are:

- `report.json`
- `report.md`
- `records.csv`
- `scenario_summary.csv`
- `rendered_programs/*.mxprog`

The Markdown report is the easiest human-readable summary. The JSON and CSV files are more useful for automation or comparisons.

The rendered programs include:

- scenario variable assignments
- a synthetic `program_start` checkpoint
- the original program body
- a synthetic `program_end` checkpoint

## Minimal End-To-End Example

```powershell
mecademic-cycle-report generate-scenarios programs --output-dir configs/generated
mecademic-cycle-report validate-config configs/generated/my_process.scenarios.yaml
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/generated/my_process.scenarios.yaml --dry-run
```

In practice, you edit `configs/generated/my_process.scenarios.yaml` between the first and second commands.

## What The Tool Measures

The total cycle time is measured as the delta between the synthetic wrapper checkpoints:

- `program_start`
- `program_end`

Any checkpoints inside the original `.mxprog` are still recorded and used for segment-level timing inside that execution window.

## Repository Samples

This repository includes sample programs and configs under `tests/fixtures` for development and regression testing.

Examples:

- `tests/fixtures/test_RBT1.mxprog`
- `tests/fixtures/test_RBT1.scenarios.yaml`
- `tests/fixtures/test_RBT2.mxprog`
- `tests/fixtures/test_RBT2.scenarios.yaml`

Use them as reference material, not as the normal storage location for your own robot programs.

## Troubleshooting

If a run fails early, check these first:

- the robot IP address in the config
- whether simulation mode should be forced or explicitly disabled
- whether the program references `vars.NAME` values missing from a scenario
- whether the checkpoints listed in the config match the checkpoints expected inside the original program body

If you only need to inspect scenario expansion or artifact generation, prefer `--dry-run` first.