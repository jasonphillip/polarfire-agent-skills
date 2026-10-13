---
name: kit-run-inference
description: Compile, simulate, and run a pfkit model on the V250 kit.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Run inference on the kit

Start only after `inspect.json` has empty unsupported and limit violation lists.
Read `docs/pipeline.md` and `docs/hardware.md`.
Use one run directory for all stages of one model.
Configure `toolshost.yaml` for compile and sim.
Configure `kit.yaml` and build `hw/vbx_run` before infer.
The kit image needs the V250 overlay and uncached DMA pool.
Check the UIO name `vbx` and the DMA device before infer.
The runner receives already quantized input bytes.

## Remote stages

Use the kit environment from the repository root.
The first two commands need the tools host.
The third command needs the configured kit and built runner.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
"$KIT_ROOT/.venv/bin/python" -m pfkit compile "$KIT_ROOT/reports/signal-local/model.tflite" --output "$KIT_ROOT/reports/signal-local/model.vnnx" --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit prepare-input signal-freq --run-dir "$KIT_ROOT/reports/signal-local" --samples 64
"$KIT_ROOT/.venv/bin/python" -m pfkit sim "$KIT_ROOT/reports/signal-local/model.vnnx" --input "$KIT_ROOT/reports/signal-local/input.int8.npy" --output "$KIT_ROOT/reports/signal-local/sim.npz" --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit infer "$KIT_ROOT/reports/signal-local/model.vnnx" --input "$KIT_ROOT/reports/signal-local/input.int8.bin" --output "$KIT_ROOT/reports/signal-local/hw.bin" --json "$KIT_ROOT/reports/signal-local/hw.json" --run-dir "$KIT_ROOT/reports/signal-local"
```

The `example run` path prepares both quantized input files before sim.
For manual stages, `prepare-input` uses the inspected TFLite input scale and zero point.
It writes both files and a manifest with sample indices and the payload hash.
`example run signal-freq --until compare --samples 64` carries one held-out selection through all stages.
Its default is one sample, labeled as the one-sample fast path.
Use `--selection random --seed N` for a repeatable random selection.
Keep the fixed batch and input layout from the example contract.
The binary file must contain K * input_bytes bytes, where K >= 1 matches the selected sample count.
Use `--dry-run` to review each remote command before execution.
A dry run is a plan, not a successful remote stage.

## Comparison

Follow `adapt-your-model` for the canonical compare and report commands.
Pass the simulator archive and hardware output to compare when present.
The example contract sets float and TFLite-to-simulator tolerances.
Hardware equality is exact by default.
Use `--lsb-tolerance` only when the run states the changed bound.
A missing simulator or hardware file leaves that comparison `not run`.
Stop when a comparison reports a failed bound.
Read `compare.json` `status`, `complete`, each row's `status` and `exact`,
and `attempt_id`. `stale` and `failed` are non-passes. A `passed` result
without `complete: true` is not full deployment validation.
The new 64-sample CLI route has not run on the kit.

## Evidence

`compile.json`, `sim.json`, and `infer.json` record remote commands.
The files also record output identity after actual runs.
`hw.json` holds runner metadata from the kit.
Read its core version, control and error words, output metadata, and timing values.
Do not report timing or output values from a dry run.
Do not infer kit behavior from successful compile or simulation.
Use `claim-log` to make each result row point to its run directory file.

## Checks

- Read empty inspection failure lists before compiling.
- Read command status, exit codes, size, and hashes from remote stage JSON files.
- Read input and output metadata plus status from `hw.json`.
- Read all comparison statuses and tolerances from `compare.json`.
