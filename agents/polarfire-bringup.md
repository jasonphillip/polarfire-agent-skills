# PolarFire bring-up agent

Given a model, its representative input, a source checkout, and an approved kit image, run these skills in order. Stop at the first failed acceptance check. Save the command output and exact report path at each step. Never write a measurement that was not read from tool output.

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
