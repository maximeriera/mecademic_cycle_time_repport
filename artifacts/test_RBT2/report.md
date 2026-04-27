# Mecademic Cycle Time Report

## Overview

- Robot address: `192.168.0.100`
- Dry run: `False`
- Alignment run before measurement: `True`
- Warmup runs per scenario: `0`
- Measured runs per scenario: `1`
- Contingency percent: `20.0`

## Robot Runtime

- Enforce sim mode: `True`
- Program load method: `LoadProgram`
- Deactivated for sim: `True`
- Ready status: sim=`1`, homed=`True`, paused=`False`

## Program Variables

`GRP_DELAY`, `SPD_INSERT`, `SPD_RETRACT`

## Scenario Summary

| Scenario | Avg (s) | Min (s) | Max (s) | Std Dev (s) | Contingency Avg (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 2.494 | 2.494 | 2.494 | 0.000 | 2.993 |
| cautious | 3.567 | 3.567 | 3.567 | 0.000 | 4.280 |
| baseline-variables.SPD_INSERT-minus10pct | 2.554 | 2.554 | 2.554 | 0.000 | 3.065 |
| baseline-variables.SPD_INSERT-plus10pct | 2.441 | 2.441 | 2.441 | 0.000 | 2.930 |
| baseline-variables.SPD_RETRACT-minus10pct | 2.497 | 2.497 | 2.497 | 0.000 | 2.997 |
| baseline-variables.SPD_RETRACT-plus10pct | 2.490 | 2.490 | 2.490 | 0.000 | 2.988 |
| baseline-variables.GRP_DELAY-minus10pct | 2.452 | 2.452 | 2.452 | 0.000 | 2.942 |
| baseline-variables.GRP_DELAY-plus10pct | 2.535 | 2.535 | 2.535 | 0.000 | 3.042 |
| cautious-variables.SPD_INSERT-minus10pct | 3.745 | 3.745 | 3.745 | 0.000 | 4.494 |
| cautious-variables.SPD_INSERT-plus10pct | 3.423 | 3.423 | 3.423 | 0.000 | 4.107 |
| cautious-variables.SPD_RETRACT-minus10pct | 3.572 | 3.572 | 3.572 | 0.000 | 4.286 |
| cautious-variables.SPD_RETRACT-plus10pct | 3.563 | 3.563 | 3.563 | 0.000 | 4.276 |
| cautious-variables.GRP_DELAY-minus10pct | 3.525 | 3.525 | 3.525 | 0.000 | 4.230 |
| cautious-variables.GRP_DELAY-plus10pct | 3.608 | 3.608 | 3.608 | 0.000 | 4.330 |

## Impact Insights

- `cautious` shifts average cycle time by `1.073s` (43.0% increase) relative to `baseline`.
- `baseline-variables.SPD_INSERT-minus10pct` shifts average cycle time by `0.060s` (2.4% increase) relative to `baseline`.
- `baseline-variables.SPD_INSERT-plus10pct` shifts average cycle time by `0.053s` (2.1% decrease) relative to `baseline`.
- `baseline-variables.SPD_RETRACT-minus10pct` shifts average cycle time by `0.003s` (0.1% increase) relative to `baseline`.
- `baseline-variables.SPD_RETRACT-plus10pct` shifts average cycle time by `0.004s` (0.2% decrease) relative to `baseline`.
- `baseline-variables.GRP_DELAY-minus10pct` shifts average cycle time by `0.042s` (1.7% decrease) relative to `baseline`.
- `baseline-variables.GRP_DELAY-plus10pct` shifts average cycle time by `0.041s` (1.7% increase) relative to `baseline`.
- `cautious-variables.SPD_INSERT-minus10pct` shifts average cycle time by `1.251s` (50.2% increase) relative to `baseline`.
- `cautious-variables.SPD_INSERT-plus10pct` shifts average cycle time by `0.929s` (37.2% increase) relative to `baseline`.
- `cautious-variables.SPD_RETRACT-minus10pct` shifts average cycle time by `1.078s` (43.2% increase) relative to `baseline`.
- `cautious-variables.SPD_RETRACT-plus10pct` shifts average cycle time by `1.069s` (42.9% increase) relative to `baseline`.
- `cautious-variables.GRP_DELAY-minus10pct` shifts average cycle time by `1.031s` (41.4% increase) relative to `baseline`.
- `cautious-variables.GRP_DELAY-plus10pct` shifts average cycle time by `1.114s` (44.7% increase) relative to `baseline`.

## Scenario Inputs

### baseline

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `150`
  - `SPD_RETRACT` = `800`

### cautious

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `50`
  - `SPD_RETRACT` = `500`

### baseline-variables.SPD_INSERT-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `135`
  - `SPD_RETRACT` = `800`

### baseline-variables.SPD_INSERT-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `165`
  - `SPD_RETRACT` = `800`

### baseline-variables.SPD_RETRACT-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `150`
  - `SPD_RETRACT` = `720`

### baseline-variables.SPD_RETRACT-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `150`
  - `SPD_RETRACT` = `880`

### baseline-variables.GRP_DELAY-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.18`
  - `SPD_INSERT` = `150`
  - `SPD_RETRACT` = `800`

### baseline-variables.GRP_DELAY-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.22`
  - `SPD_INSERT` = `150`
  - `SPD_RETRACT` = `800`

### cautious-variables.SPD_INSERT-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `45`
  - `SPD_RETRACT` = `500`

### cautious-variables.SPD_INSERT-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `55`
  - `SPD_RETRACT` = `500`

### cautious-variables.SPD_RETRACT-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `50`
  - `SPD_RETRACT` = `450`

### cautious-variables.SPD_RETRACT-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.2`
  - `SPD_INSERT` = `50`
  - `SPD_RETRACT` = `550`

### cautious-variables.GRP_DELAY-minus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.18`
  - `SPD_INSERT` = `50`
  - `SPD_RETRACT` = `500`

### cautious-variables.GRP_DELAY-plus10pct

- Time scaling: `None`
- Blending: `None`
- Gripper open delay: `0.0`
- Gripper close delay: `0.0`
- Variables:
  - `GRP_DELAY` = `0.22`
  - `SPD_INSERT` = `50`
  - `SPD_RETRACT` = `500`

## Measured Runs

### baseline run 1

- Total cycle time: `2.494s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.037 | reached |
| station_1_start | 0.044 | reached |
| cycle_complete | 2.529 | reached |
| program_end | 2.531 | reached |

### cautious run 1

- Total cycle time: `3.567s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.036 | reached |
| station_1_start | 0.039 | reached |
| cycle_complete | 3.601 | reached |
| program_end | 3.603 | reached |

### baseline-variables.SPD_INSERT-minus10pct run 1

- Total cycle time: `2.554s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.SPD_INSERT-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.036 | reached |
| station_1_start | 0.042 | reached |
| cycle_complete | 2.588 | reached |
| program_end | 2.590 | reached |

### baseline-variables.SPD_INSERT-plus10pct run 1

- Total cycle time: `2.441s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.SPD_INSERT-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.040 | reached |
| station_1_start | 0.042 | reached |
| cycle_complete | 2.479 | reached |
| program_end | 2.481 | reached |

### baseline-variables.SPD_RETRACT-minus10pct run 1

- Total cycle time: `2.497s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.SPD_RETRACT-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.034 | reached |
| station_1_start | 0.038 | reached |
| cycle_complete | 2.527 | reached |
| program_end | 2.531 | reached |

### baseline-variables.SPD_RETRACT-plus10pct run 1

- Total cycle time: `2.490s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.SPD_RETRACT-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.045 | reached |
| station_1_start | 0.050 | reached |
| cycle_complete | 2.533 | reached |
| program_end | 2.535 | reached |

### baseline-variables.GRP_DELAY-minus10pct run 1

- Total cycle time: `2.452s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.GRP_DELAY-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.046 | reached |
| station_1_start | 0.049 | reached |
| cycle_complete | 2.495 | reached |
| program_end | 2.498 | reached |

### baseline-variables.GRP_DELAY-plus10pct run 1

- Total cycle time: `2.535s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__baseline-variables.GRP_DELAY-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.034 | reached |
| station_1_start | 0.037 | reached |
| cycle_complete | 2.568 | reached |
| program_end | 2.570 | reached |

### cautious-variables.SPD_INSERT-minus10pct run 1

- Total cycle time: `3.745s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.SPD_INSERT-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.035 | reached |
| station_1_start | 0.039 | reached |
| cycle_complete | 3.778 | reached |
| program_end | 3.780 | reached |

### cautious-variables.SPD_INSERT-plus10pct run 1

- Total cycle time: `3.423s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.SPD_INSERT-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.039 | reached |
| station_1_start | 0.041 | reached |
| cycle_complete | 3.459 | reached |
| program_end | 3.462 | reached |

### cautious-variables.SPD_RETRACT-minus10pct run 1

- Total cycle time: `3.572s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.SPD_RETRACT-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.034 | reached |
| station_1_start | 0.040 | reached |
| cycle_complete | 3.603 | reached |
| program_end | 3.605 | reached |

### cautious-variables.SPD_RETRACT-plus10pct run 1

- Total cycle time: `3.563s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.SPD_RETRACT-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.046 | reached |
| station_1_start | 0.054 | reached |
| cycle_complete | 3.607 | reached |
| program_end | 3.610 | reached |

### cautious-variables.GRP_DELAY-minus10pct run 1

- Total cycle time: `3.525s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.GRP_DELAY-minus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.033 | reached |
| station_1_start | 0.038 | reached |
| cycle_complete | 3.557 | reached |
| program_end | 3.558 | reached |

### cautious-variables.GRP_DELAY-plus10pct run 1

- Total cycle time: `3.608s`
- Rendered program: `artifacts\test_RBT2\rendered_programs\test_RBT2__cautious-variables.GRP_DELAY-plus10pct.mxprog`

| Checkpoint | Elapsed (s) | Status |
| --- | ---: | --- |
| program_start | 0.039 | reached |
| station_1_start | 0.043 | reached |
| cycle_complete | 3.644 | reached |
| program_end | 3.647 | reached |
