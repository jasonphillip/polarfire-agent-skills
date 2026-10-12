# Software pipeline

Run these commands in the kit repository. Use Python 3.11. Set `KIT_ROOT` to its absolute path.

```sh
KIT_ROOT="$(pwd -P)"
make -C "$KIT_ROOT" env
make -C "$KIT_ROOT" test
"$KIT_ROOT/.venv/bin/python" -m pfkit deps fetch --dry-run
"$KIT_ROOT/.venv/bin/python" -m pfkit deps fetch
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect
"$KIT_ROOT/.venv/bin/python" -m pfkit example run odmr-mlp --until inspect
```

`make -C "$KIT_ROOT" env` creates `.venv`, installs the package and pinned workers, writes `.venv/freeze.txt`, then marks `.venv/.ready`.
`deps fetch` reads `deps.lock`, checks out each source, and installs both workers in editable mode.
The dry run prints each command without network access.

Use one run directory for manual stages:

```sh
"$KIT_ROOT/.venv/bin/python" -m pfkit data signal-freq --run-dir "$KIT_ROOT/reports/manual-signal"
"$KIT_ROOT/.venv/bin/python" -m pfkit train signal-freq --run-dir "$KIT_ROOT/reports/manual-signal"
"$KIT_ROOT/.venv/bin/python" -m pfkit eval signal-freq --run-dir "$KIT_ROOT/reports/manual-signal"
"$KIT_ROOT/.venv/bin/python" -m pfkit export signal-freq --run-dir "$KIT_ROOT/reports/manual-signal"
"$KIT_ROOT/.venv/bin/python" -m pfkit inspect "$KIT_ROOT/reports/manual-signal/model.tflite" --run-dir "$KIT_ROOT/reports/manual-signal"
"$KIT_ROOT/.venv/bin/python" -m pfkit report --run-dir "$KIT_ROOT/reports/manual-signal"
```

`data` writes `dataset.npz` and `dataset.manifest.json`. Add `--import /path/to/source.npz` to validate and copy input arrays.
`train` writes `model.pt` and `training.json`. `eval` writes `eval.json`.
`export` writes `model.tflite` and `export.manifest.json`.
`inspect` prints operators and tensors and writes `inspect.json` when given a run directory.
`report` writes package versions, revisions, hashes and `summary.md`.

The remote stages use local config files. Set their SSH targets and paths before execution.

```sh
"$KIT_ROOT/.venv/bin/python" -m pfkit compile "$KIT_ROOT/reports/manual-signal/model.tflite" --output "$KIT_ROOT/reports/manual-signal/model.vnnx" --dry-run
"$KIT_ROOT/.venv/bin/python" -m pfkit sim "$KIT_ROOT/reports/manual-signal/model.vnnx" --input "$KIT_ROOT/reports/manual-signal/input.int8.npy" --output "$KIT_ROOT/reports/manual-signal/sim.npz" --dry-run
"$KIT_ROOT/.venv/bin/python" -m pfkit infer "$KIT_ROOT/reports/manual-signal/model.vnnx" --input "$KIT_ROOT/reports/manual-signal/input.int8.bin" --output "$KIT_ROOT/reports/manual-signal/hw.bin" --json "$KIT_ROOT/reports/manual-signal/hw.json" --dry-run
"$KIT_ROOT/.venv/bin/python" -m pfkit compare signal-freq --run-dir "$KIT_ROOT/reports/manual-signal" --sim "$KIT_ROOT/reports/manual-signal/sim.npz" --hw "$KIT_ROOT/reports/manual-signal/hw.bin"
```

`compile` copies the TFLite file to the tools host and runs `vnnx_compile -c V250 -t ... -o ...`.
It copies the VNNX file back and records command output, exit codes, size and SHA-256 when a run directory is set.
`sim` copies the model, input array and small SDK runner to the tools host. It copies a raw output archive back.
`infer` copies the runner, model and binary input to the kit. It copies binary output and JSON metadata back.
Dry runs print every SSH and SCP command without contacting either host.
`compare` checks float and TFLite outputs. It checks simulator and hardware outputs when supplied.

The kit runner CLI contract is `vbx_run --model m.vnnx --input in.bin --output out.bin --timeout-ms N --json meta.json`.
Its exit codes are 0 for success, 2 for bad arguments or size, 3 for model load or DMA failure, 4 for timeout, and 5 for an NPU error register.
The runner is built separately. The Python package does not build or install it.
