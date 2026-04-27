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
| baseline | 2.611 | 2.611 | 2.611 | 0.000 | 3.133 |
| cautious | 3.867 | 3.867 | 3.867 | 0.000 | 4.640 |
| baseline-pick_position-best | 3.031 | 3.031 | 3.031 | 0.000 | 3.637 |
| baseline-pick_position-worst | 2.099 | 2.099 | 2.099 | 0.000 | 2.519 |
| baseline-pick_position-random | 2.528 | 2.242 | 3.041 | 0.323 | 3.034 |
| cautious-pick_position-best | 3.738 | 3.738 | 3.738 | 0.000 | 4.485 |
| cautious-pick_position-worst | 2.802 | 2.802 | 2.802 | 0.000 | 3.363 |
| cautious-pick_position-random | 3.305 | 3.056 | 3.596 | 0.171 | 3.966 |

## Impact Insights

- `cautious` shifts average cycle time by `1.256s` (48.1% increase) relative to `baseline`.
- `baseline-pick_position-best` shifts average cycle time by `0.420s` (16.1% increase) relative to `baseline`.
- `baseline-pick_position-worst` shifts average cycle time by `0.512s` (19.6% decrease) relative to `baseline`.
- `baseline-pick_position-random` shifts average cycle time by `0.083s` (3.2% decrease) relative to `baseline`.
- `cautious-pick_position-best` shifts average cycle time by `1.127s` (43.1% increase) relative to `baseline`.
- `cautious-pick_position-worst` shifts average cycle time by `0.191s` (7.3% increase) relative to `baseline`.
- `cautious-pick_position-random` shifts average cycle time by `0.694s` (26.6% increase) relative to `baseline`.

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
  - `PICK_X` sampled over `17.3766` to `62.6266` (mean `42.6068`)
  - `PICK_Y` sampled over `15.8182` to `183.702` (mean `119.6896`)
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
  - `PICK_X` sampled over `18.4451` to `69.4643` (mean `36.9008`)
  - `PICK_Y` sampled over `42.2319` to `180.3632` (mean `121.6417`)
  - `SPD_INSERT` = `50`
  - `SPD_PICK` = `200`
  - `SPD_RETRACT` = `500`

## Measured Runs

### baseline run 1

- Total cycle time: `2.611s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.055 | reached |
| pick_start | 0.056 | reached |
| transfer_complete | 1.247 | reached |
| return_complete | 2.664 | reached |
| program_end | 2.666 | reached |

### cautious run 1

- Total cycle time: `3.867s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.045 | reached |
| pick_start | 0.049 | reached |
| transfer_complete | 1.619 | reached |
| return_complete | 3.910 | reached |
| program_end | 3.912 | reached |

### baseline-pick_position-best run 1

- Total cycle time: `3.031s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline-pick_position-best.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.053 | reached |
| pick_start | 0.056 | reached |
| transfer_complete | 1.452 | reached |
| return_complete | 3.082 | reached |
| program_end | 3.084 | reached |

### baseline-pick_position-worst run 1

- Total cycle time: `2.099s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__baseline-pick_position-worst.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.052 | reached |
| pick_start | 0.054 | reached |
| transfer_complete | 0.973 | reached |
| return_complete | 2.149 | reached |
| program_end | 2.151 | reached |

### cautious-pick_position-best run 1

- Total cycle time: `3.738s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious-pick_position-best.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.055 | reached |
| pick_start | 0.056 | reached |
| transfer_complete | 1.562 | reached |
| return_complete | 3.791 | reached |
| program_end | 3.793 | reached |

### cautious-pick_position-worst run 1

- Total cycle time: `2.802s`
- Rendered program: `artifacts\test_RBT1\rendered_programs\test_RBT1__cautious-pick_position-worst.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.057 | reached |
| pick_start | 0.060 | reached |
| transfer_complete | 1.080 | reached |
| return_complete | 2.857 | reached |
| program_end | 2.859 | reached |
