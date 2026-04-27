# Mecademic Cycle Time Report

## Overview

- Robot address: `192.168.0.100`
- Dry run: `False`
- Alignment run before measurement: `True`
- Warmup runs per scenario: `0`
- Measured runs per scenario: `1`
- Contingency percent: `20.0`

## Robot Runtime

- Enforce sim mode: `False`
- Program load method: `LoadProgram`
- Deactivated for sim: `False`
- Ready status: sim=`0`, homed=`True`, paused=`False`

## Program Variables

`GRP_DELAY`, `PICK_X`, `PICK_Y`, `SPD_INSERT`, `SPD_PICK`, `SPD_RETRACT`

## Scenario Summary

| Scenario | Avg (s) | Min (s) | Max (s) | Std Dev (s) | Contingency Avg (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 2.607 | 2.607 | 2.607 | 0.000 | 3.129 |
| cautious | 3.860 | 3.860 | 3.860 | 0.000 | 4.632 |
| baseline-pick_position-best | 3.024 | 3.024 | 3.024 | 0.000 | 3.629 |
| baseline-pick_position-worst | 2.098 | 2.098 | 2.098 | 0.000 | 2.517 |
| baseline-pick_position-random | 2.635 | 2.269 | 3.119 | 0.304 | 3.162 |
| cautious-pick_position-best | 3.736 | 3.736 | 3.736 | 0.000 | 4.484 |
| cautious-pick_position-worst | 2.806 | 2.806 | 2.806 | 0.000 | 3.367 |
| cautious-pick_position-random | 3.187 | 2.963 | 3.744 | 0.252 | 3.824 |

## Impact Insights

- `cautious` shifts average cycle time by `1.252s` (48.0% increase) relative to `baseline`.
- `baseline-pick_position-best` shifts average cycle time by `0.417s` (16.0% increase) relative to `baseline`.
- `baseline-pick_position-worst` shifts average cycle time by `0.510s` (19.5% decrease) relative to `baseline`.
- `baseline-pick_position-random` shifts average cycle time by `0.028s` (1.1% increase) relative to `baseline`.
- `cautious-pick_position-best` shifts average cycle time by `1.129s` (43.3% increase) relative to `baseline`.
- `cautious-pick_position-worst` shifts average cycle time by `0.198s` (7.6% increase) relative to `baseline`.
- `cautious-pick_position-random` shifts average cycle time by `0.580s` (22.2% increase) relative to `baseline`.

## Scenario Inputs

### baseline

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.15`
  - `PICK_X` = `35`
  - `PICK_Y` = `85`
  - `SPD_INSERT` = `150`
  - `SPD_PICK` = `300`
  - `SPD_RETRACT` = `800`

### cautious

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `PICK_X` = `15`
  - `PICK_Y` = `15`
  - `SPD_INSERT` = `50`
  - `SPD_PICK` = `200`
  - `SPD_RETRACT` = `500`

### baseline-pick_position-best

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.15`
  - `PICK_X` = `75`
  - `PICK_Y` = `15`
  - `SPD_INSERT` = `150`
  - `SPD_PICK` = `300`
  - `SPD_RETRACT` = `800`

### baseline-pick_position-worst

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.15`
  - `PICK_X` = `15`
  - `PICK_Y` = `185`
  - `SPD_INSERT` = `150`
  - `SPD_PICK` = `300`
  - `SPD_RETRACT` = `800`

### baseline-pick_position-random

- Random samples summarized: `10`
- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.15`
  - `PICK_X` sampled over `15.1379` to `67.4568` (mean `39.355`)
  - `PICK_Y` sampled over `18.9556` to `164.6522` (mean `93.5309`)
  - `SPD_INSERT` = `150`
  - `SPD_PICK` = `300`
  - `SPD_RETRACT` = `800`

### cautious-pick_position-best

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `PICK_X` = `75`
  - `PICK_Y` = `15`
  - `SPD_INSERT` = `50`
  - `SPD_PICK` = `200`
  - `SPD_RETRACT` = `500`

### cautious-pick_position-worst

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `PICK_X` = `15`
  - `PICK_Y` = `185`
  - `SPD_INSERT` = `50`
  - `SPD_PICK` = `200`
  - `SPD_RETRACT` = `500`

### cautious-pick_position-random

- Random samples summarized: `10`
- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `PICK_X` sampled over `19.8879` to `68.2523` (mean `41.944`)
  - `PICK_Y` sampled over `15.9847` to `154.1687` (mean `110.929`)
  - `SPD_INSERT` = `50`
  - `SPD_PICK` = `200`
  - `SPD_RETRACT` = `500`

## Measured Runs

### baseline run 1

- Total cycle time: `2.607s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.057 | reached |
| pick_start | 0.058 | reached |
| transfer_complete | 1.244 | reached |
| return_complete | 2.661 | reached |
| program_end | 2.664 | reached |

### cautious run 1

- Total cycle time: `3.860s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.053 | reached |
| pick_start | 0.056 | reached |
| transfer_complete | 1.618 | reached |
| return_complete | 3.911 | reached |
| program_end | 3.913 | reached |

### baseline-pick_position-best run 1

- Total cycle time: `3.024s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline-pick_position-best.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.060 | reached |
| pick_start | 0.062 | reached |
| transfer_complete | 1.455 | reached |
| return_complete | 3.083 | reached |
| program_end | 3.084 | reached |

### baseline-pick_position-worst run 1

- Total cycle time: `2.098s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline-pick_position-worst.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.056 | reached |
| pick_start | 0.060 | reached |
| transfer_complete | 0.973 | reached |
| return_complete | 2.151 | reached |
| program_end | 2.154 | reached |

### cautious-pick_position-best run 1

- Total cycle time: `3.736s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious-pick_position-best.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.052 | reached |
| pick_start | 0.053 | reached |
| transfer_complete | 1.554 | reached |
| return_complete | 3.785 | reached |
| program_end | 3.788 | reached |

### cautious-pick_position-worst run 1

- Total cycle time: `2.806s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious-pick_position-worst.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.056 | reached |
| pick_start | 0.058 | reached |
| transfer_complete | 1.080 | reached |
| return_complete | 2.859 | reached |
| program_end | 2.861 | reached |
