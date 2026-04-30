# Mecademic Cycle Time Report

Checkpoint-driven cycle time analysis for Mecademic robot programs.

For command examples and common run patterns, see [docs/example-usage.md](docs/example-usage.md).
For a copyable scenario config starter, see [docs/scenarios-template.yaml](docs/scenarios-template.yaml).

## Current Status

This repository now contains the first implementation slice:

- Python package scaffold with CLI entrypoint
- YAML or JSON config loading
- Native Mecademic checkpoint expectations and validation
- Folder-based scenario starter generation from `.mxprog` inspection
- Scenario profile and scenario sweep expansion
- Run metrics and summary statistics with contingency-adjusted totals
- Scenario-based mxprog template rendering for optional preprocessing
- JSON and CSV artifact export
- Dry-run analysis path that produces report payloads without robot hardware
- Unit tests for checkpoint validation, scenario expansion, analysis, and runner behavior

The project now includes an initial `mecademicpy` integration path. For real runs, it uploads the `.mxprog` with `SaveFile`, loads it with `LoadProgram`, arms external checkpoints with `ExpectExternalCheckpoint`, and starts execution with `StartProgram`. Dry-run mode remains available when hardware is not present.

For safety, real runs force robot simulation mode by default with `ActivateSim()` before homing. Keep `robot.enforce_sim_mode: true` unless you intentionally want to opt out.

## Project Layout

- `src/mecademic_cycle_report/cli.py`: CLI entrypoint
- `src/mecademic_cycle_report/config.py`: config schema and loading
- `src/mecademic_cycle_report/checkpoint_spec.py`: checkpoint definitions and validation
- `src/mecademic_cycle_report/mxprog_inspection.py`: `.mxprog` variable and checkpoint inspection helpers
- `src/mecademic_cycle_report/scenario_matrix.py`: scenario profiles and sweep expansion
- `src/mecademic_cycle_report/runner.py`: checkpoint-driven run orchestration
- `src/mecademic_cycle_report/analysis.py`: timing statistics and scenario comparisons
- `src/mecademic_cycle_report/reporting.py`: terminal summary and structured report payloads
- `docs/scenarios-template.yaml`: copyable scenario config starter
- `tests/fixtures/scenarios.yaml`: sample config for dry-run analysis

## Config Model

The tool expects a config file with four sections:

- `robot`: robot connection settings such as IP address; `enforce_sim_mode` defaults to `true` and forces Mecademic simulation mode before homing or running any program
- `analysis`: run counts, warmup count, pre-measurement alignment run flag, contingency percentage, output directory, and optional dry-run flag
- `checkpoints`: the ordered native Mecademic checkpoints expected during the program
- `scenarios`: named profiles plus optional sweeps, perturbations, and grouped variable-case studies for parameter exploration

Variables are treated as scenario inputs, not checkpoint markers. This is the primary workflow for real `.mxprog` files: the program references robot variables through `vars.NAME`, and the tool applies scenario values before each run. Rendered programs also inject `SetVariable(name, value)` commands at the top of the wrapper so the saved program carries its scenario inputs explicitly.

The analyzer scans the input `.mxprog` for `vars.NAME` references and emits warnings when a scenario does not define one of the required variables. That gives you an early config mismatch signal before a real robot run.

The CLI also includes a starter-config helper. `generate-scenarios` scans every `.mxprog` in a folder, extracts the `SetCheckpoint(...)` ids and `vars.NAME` references from each file, and writes one `.scenarios.yaml` starter per program.

Optional template preprocessing is also supported for programs that need literal substitution before upload. Templates can reference placeholders such as `{{ gripper_open_delay_s }}`, `{{ gripper_close_delay_s }}`, `{{ time_scaling_percent }}`, `{{ blending_percent }}`, or nested values like `{{ scenario.name }}` and `{{ variables.SPD_PICK }}`. In normal cycle-time studies, treat `blending_percent` as an advanced override for trajectory-planning validation rather than a routine process parameter.

Example config: `tests/fixtures/scenarios.yaml`

Real program examples are also included in `tests/fixtures/test_RBT1.mxprog` and `tests/fixtures/test_RBT2.mxprog` with matching configs in `tests/fixtures/test_RBT1.scenarios.yaml` and `tests/fixtures/test_RBT2.scenarios.yaml`.

## Usage

Install the package in editable mode with development dependencies:

```powershell
pip install -e .[dev]
```

This installs `mecademicpy`, which is the official Mecademic Python API used by the hardware adapter.

Validate a config file:

```powershell
mecademic-cycle-report validate-config configs/my_process.scenarios.yaml
```

Generate starter scenario configs for every `.mxprog` in a folder:

```powershell
mecademic-cycle-report generate-scenarios programs --output-dir configs/generated
```

Useful generator options:

```powershell
mecademic-cycle-report generate-scenarios programs --output-dir configs/generated --robot-address 192.168.0.100 --no-enforce-sim-mode --analysis-output-root artifacts/generated
```

Each generated file contains:

- detected checkpoint ids from `SetCheckpoint(...)`
- detected variables from `vars.NAME`
- a single `baseline` scenario
- `__TODO__` placeholders for variable values that you must replace before running analysis

By default, the generated `analysis.output_dir` mirrors the scenario-file folder structure under `artifacts/`. For example, generating into `configs/generated` produces `artifacts/generated/<program_name>`.

Run a dry analysis against your own mxprog:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --dry-run
```

Run a real robot program with simulation mode enforced:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --enforce-sim-mode
```

Print the report payload as JSON:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --dry-run --json
```

Override simulation enforcement for a single run:

```powershell
mecademic-cycle-report analyze programs/my_process.mxprog --config configs/my_process.scenarios.yaml --no-enforce-sim-mode
```

The `tests/fixtures` directory contains repository samples for development and testing. Treat those as examples to copy from, not as the normal location for your own `.mxprog` files.

The generated starter configs are meant to accelerate setup, not to be final run-ready files. Review checkpoint labels, fill in real variable values, and add extra profiles or scenario studies as needed.

The analyze command also writes artifacts into the configured output directory:

- `report.json`
- `report.md`
- `records.csv`
- `scenario_summary.csv`
- `rendered_programs/*.mxprog`

Run the test suite:

```powershell
pytest
```

## Checkpoint Convention

This implementation assumes your mxprog program contains native Mecademic checkpoints and, in the common case, scenario-driven robot variables such as:

```text
SetJointVel(150)
SetJointAcc(150)
SetCartLinVel(5000)
SetBlending(100)
SetCheckpoint(10)
MovePose(vars.PICK_X, vars.PICK_Y, 30, 180, 0, 0)
SetCartLinVel(vars.SPD_PICK)
MoveLin(vars.PICK_X, vars.PICK_Y, 0, 180, 0, 0)
Delay(vars.GRP_DELAY_OPEN)
SetCheckpoint(20)
SetCartLinVel(vars.SPD_INSERT)
MoveLin(0.000, 0.000, -15.000, -90.000, -30.000, -90.000)
Delay(vars.GRP_DELAY_CLOSE)
SetCartLinVel(vars.SPD_RETRACT)
SetCheckpoint(30)
```

The config file lists the checkpoints expected inside the original program body. During rendering, the tool wraps that program with scenario-variable assignments at the top, a synthetic `program_start` checkpoint immediately before the original program body, and a synthetic `program_end` checkpoint at the bottom. During a real run, the tool also applies scenario variables through the API before `StartProgram`, calls `ExpectExternalCheckpoint(n)` for the wrapper checkpoints and the configured in-program checkpoints, then waits for those events in sequence. If a checkpoint is discarded or times out, the run fails and the failure is recorded.

The measured cycle time is the delta between the synthetic `program_start` and `program_end` timestamps. The internal checkpoints remain available for segment-level analysis inside that execution window.

By default, a real run also performs one unmeasured alignment cycle before recorded runs. This is intended to bring the robot and the process back to a consistent starting pose so the first measured cycle is not biased by whatever position the robot was in before analysis started.

Scenario variable names should match the Mecademic variable convention used by `vars.NAME`, for example `SPD_PICK`, `SPD_INSERT`, `SPD_RETRACT`, `GRP_DELAY_OPEN`, `GRP_DELAY_CLOSE`, `PICK_X`, and `PICK_Y`.

Sweep entries can also override robot variables directly with keys such as `variables.SPD_INSERT` or `variables.GRP_DELAY_CLOSE`. When profiles are present, each sweep combination is applied as an overlay on top of each base profile.

`blending_percent` is supported, but it is usually better left fixed or omitted entirely. In most applications blending is part of the motion design, so varying it during process studies tends to mix path-planning effects with process effects. Reserve it for dedicated planner-tuning experiments.

For one-factor-at-a-time sensitivity checks, use `scenarios.perturbations` with percentage deltas. For example, `variables.SPD_INSERT: [-10, 10]` generates two extra scenarios around the baseline, one at `-10%` and one at `+10%`, which is useful for seeing how a single parameter changes cycle time without exploding into a full cartesian sweep.

For pick-position studies such as `test_RBT1`, use `scenarios.variable_cases` to generate best-case, worst-case, and random position samples while keeping the random samples grouped under one summary in the final report. Each generated random sample is still recorded with its concrete `PICK_X` and `PICK_Y` values.

Example:

```yaml
scenarios:
  profiles:
    - name: baseline
      variables:
        PICK_X: 12.5
        PICK_Y: -18.0
        SPD_PICK: 1200
        SPD_INSERT: 800
        SPD_RETRACT: 2500
        GRP_DELAY: 0.20
  variable_cases:
    - name: pick_position
      variables:
        PICK_X:
          minimum: 10.0
          maximum: 15.0
          best: 12.5
          worst: 15.0
        PICK_Y:
          minimum: -21.0
          maximum: -18.0
          best: -18.0
          worst: -21.0
      include:
        - best
        - worst
      random_runs: 10
      continuous_random_cycle: true
```

This expands into deterministic scenarios named like `baseline-pick_position-best` and `baseline-pick_position-worst`, plus concrete random samples named like `baseline-pick_position-random-1`. The Markdown and CSV summaries aggregate those random samples under `baseline-pick_position-random` so you can compare the mean against the fixed cases.

Set `random_seed` when you want the same sampled positions every run. Leave it out when you want a fresh random sample set each time you launch the study.

    If `continuous_random_cycle` is enabled, the random samples in that grouped study run back-to-back. The runner performs the configured alignment run and warmup cycles once before the first random sample, then continues directly into the remaining random samples with updated variable values. That is useful when you want to simulate a continuously changing pick position instead of resetting the process between each sampled position.

## Next Implementation Step

The next concrete step is expanding the hardware adapter with richer runtime controls and observability, especially scenario-variable application details, gripper-related timing controls, and exported real-time data for final reports.