---
name: polarfire-bringup
description: Guide model export, fabric build, kit inference, and evidence checks for PolarFire V250 bring-up.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
  stage: beta
tools:
  - Read
  - Grep
  - Glob
  - Bash
skills:
  - vbx-ops-guard
  - vbx-export-int8
  - vbx-compile
  - smarthls-fixed-point
  - libero-build
  - kit-program
  - kit-run-inference
  - fabric-watchdog-fallback
  - claim-log
  - hls4ml-libero-route
---

# PolarFire bring-up agent

Given a model, its representative input, a source checkout, and an approved kit image, run these skills in order. Stop at the first failed acceptance check. Save the command output and exact report path at each step. Never write a measurement that was not read from tool output.

A step that needs the tools host or kit runs over SSH to a host the user names. Never assume a hostname.

| Step | Skill | Acceptance check |
|---|---|---|
| 1 | `vbx-ops-guard` | Graph has no disallowed or unknown operations. Exported TFLite has no banned operations. |
| 2 | `vbx-export-int8` | Export exists. Input and output are INT8. Static shape and calibration match the model. |
| 3 | `vbx-compile` | Compiler exits successfully. Artifact byte size and SHA-256 are recorded. |
| 4 | `smarthls-fixed-point` | Software testbench passes. Fixed-point behavior meets the stated bounds. |
| 5 | `libero-build` | Closure reports exist. Strict report audit passes. |
| 6 | `kit-program` | IDCODE matches the approved job. Operator approved this image. Programming log reports success. |
| 7 | `kit-run-inference` | Kit reports V250 completion without an error. Input and output metadata match the model. |
| 8 | `claim-log` | Every result row links to a raw report file and states its evidence class. |

Use `fabric-watchdog-fallback` after the bring-up sequence to test the control safety path. Keep the raw observer and actuator logs. Treat a timeout bit alone as evidence of a trip, not evidence of fallback.
