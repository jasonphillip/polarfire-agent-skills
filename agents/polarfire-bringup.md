---
name: polarfire-bringup
description: Run a pfkit example from data through selected V250 gates and cite each result.
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
  - adapt-your-model
  - claim-log
  - dataset-and-training
  - fabric-watchdog-fallback
  - hls4ml-libero-route
  - kit-program
  - kit-run-inference
  - libero-build
  - smarthls-fixed-point
  - vbx-compile
  - vbx-export-int8
  - vbx-ops-guard
---

# PolarFire bring-up

Accept either an example name or a user model.
For a user model, first create a valid example contract and module.
Use `dataset-and-training` and `adapt-your-model` for that adaptation.
Read `docs/contracts.md`, `docs/adapters.md`, and `docs/claims.md`.
Keep one model, one mode, and one run directory per run.
Run from the kit root with its Python 3.11 environment.

## Staged command

Set `KIT_ROOT` to the absolute kit checkout path.
Set `EXAMPLE` to the example name.
Choose one final stage and a new `RUN_DIR`.
The command runs every prior stage in order.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
EXAMPLE=signal-freq
RUN_DIR="$KIT_ROOT/reports/signal-inspect"
"$KIT_ROOT/.venv/bin/python" -m pfkit example run "$EXAMPLE" --until inspect --run-dir "$RUN_DIR"
```

Choose `--until data`, `train`, `eval`, `export`, or `inspect` for local work.
Choose `--until compile`, `sim`, `infer`, or `compare` for remote work.
For a 64-sample run, add `--samples 64`; the default is a labeled one-sample
fast path. The CLI prepares one input selection before simulation, then uses
it for inference and comparison. The new 64-sample CLI route has not run on
the kit. Use a fresh run directory and read its `attempt.json`.
A second `example run` starts again at data.
Use a new run directory when changing the final stage or `--full` mode.
Use individual pfkit commands only when their input files are already prepared.

## Gates

Inspect must pass before compile.
Compile and sim need a configured `toolshost.yaml` and available tools host.
Infer needs a configured `kit.yaml`, compatible kit image, and built `hw/vbx_run`.
Read the generated IP version and V250 preset before programming any image.
Do not run optional control and programming work as part of model inference.
Stop at a failed gate and keep its output.

| Stage | Acceptance file | Required result |
|---|---|---|
| data | `RUN_DIR/dataset.manifest.json` | Arrays meet the contract. |
| train | `RUN_DIR/training.json` | Checkpoint hash and epochs recorded. |
| eval | `RUN_DIR/eval.json` | Test error and units recorded. |
| export | `RUN_DIR/export.manifest.json` | INT8 model and calibration recorded. |
| inspect | `RUN_DIR/inspect.json` | Unsupported and limit lists empty. |
| prepare-input | `RUN_DIR/input.manifest.json` | Sample indices, layout and payload hash recorded before sim. |
| compile | `RUN_DIR/compile.json` | Remote command passed and VNNX recorded. |
| sim | `RUN_DIR/sim.json` | Simulator output recorded. |
| infer | `RUN_DIR/infer.json` and `RUN_DIR/hw.json` | Kit output and runner metadata recorded. |
| compare | `RUN_DIR/compare.json` | `status` is `passed`. For a full deployment check, `complete` is also true. `incomplete`, `no_evidence`, `failed` and `stale` are not passes. `exact` false means within tolerance, not equal. |

Use `claim-log` to summarize the run.
Never write a number not read from tool output.
Every result row cites the exact run directory file that supports it.
Label every unrun stage `not run`.
Keep case study results separate from this kit's results.
