# Getting started

Read `docs/install.md` for client setup and tested installation claims.
Read `docs/scope.md` for the supported board and software profile.
Read `docs/contracts.md` and `docs/adapters.md` before adding a model.
Read `docs/pipeline.md` for stage outputs and remote configuration.
Read `docs/hardware.md` before any tools host or kit step.
Read `docs/claims.md` before making an operator or quantization claim.

## First local run

Set `KIT_ROOT` to the absolute checkout path.
Create the Python environment.
Use a new run directory for the local inspect path.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect --run-dir "$KIT_ROOT/reports/signal-inspect"
```

Check `dataset.manifest.json`, `training.json`, `eval.json`, and `export.manifest.json`.
Check `inspect.json` for empty unsupported and limit violation lists.
Check `commands.jsonl` for the run command and exit code.
Do not report an unrun remote stage as a pass.

## Later stages

Configure `toolshost.yaml` before compile or sim.
Build `hw/vbx_run` and configure `kit.yaml` before infer.
Use `polarfire-bringup` for the acceptance table and stage choices.
Use the individual pfkit commands in the skills to continue one run directory.
A fresh `example run` starts again at data.
Keep its generated report files with the model and input identity.

For a manual remote run, prepare the selected test samples after compile.
Use a run directory with `dataset.npz` and `model.tflite` from the earlier stages.
The preparation command writes `input.int8.npy`, `input.int8.bin`, and `input.manifest.json` in that directory.

```sh
RUN="$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit compile "$RUN/model.tflite" --output "$RUN/model.vnnx" --run-dir "$RUN"
"$KIT_ROOT/.venv/bin/python" -m pfkit prepare-input signal-freq --run-dir "$RUN" --samples 64
"$KIT_ROOT/.venv/bin/python" -m pfkit sim "$RUN/model.vnnx" --input "$RUN/input.int8.npy" --output "$RUN/sim.npz" --run-dir "$RUN"
"$KIT_ROOT/.venv/bin/python" -m pfkit infer "$RUN/model.vnnx" --input "$RUN/input.int8.bin" --output "$RUN/hw.bin" --json "$RUN/hw.json" --run-dir "$RUN"
"$KIT_ROOT/.venv/bin/python" -m pfkit compare signal-freq --run-dir "$RUN" --sim "$RUN/sim.npz" --hw "$RUN/hw.bin" --scope full
```

The complete example route accepts `--samples 64` and defaults to a labeled one-sample fast path.
Use `--selection random --seed N` on `prepare-input` or `example run` for a repeatable random selection.
The input manifest records the chosen indices and payload hash.
For a fresh held-out batch, configure the tools host and kit, then run:

```sh
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until compare --samples 64 --toolshost "$KIT_ROOT/toolshost.yaml" --kit "$KIT_ROOT/kit.yaml" --run-dir "$KIT_ROOT/reports/signal-batch64"
```

This CLI route has local tests. Its 64-sample hardware run is not recorded here.
