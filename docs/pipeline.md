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
It installs `pfkit` in editable mode, including the `.venv/bin/pfkit` console script. `make test` checks that script before pytest.
`"$KIT_ROOT/.venv/bin/python" -m pfkit` runs the same CLI as `"$KIT_ROOT/.venv/bin/pfkit"`.
`deps fetch` reads `deps.lock`, checks out each source, and installs both workers in editable mode.
The dry run prints each command without network access.
For `example run`, pass `--toolshost /absolute/path/to/private-toolshost.yaml` and
`--kit /absolute/path/to/private-kit.yaml` to use private remote settings.
These options default to `toolshost.yaml` and `kit.yaml` in the kit checkout.
`--toolshost` applies to compile and sim; `--kit` applies to infer.

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
MLP exports use 1x1 Conv2D by default. Pass `--form fc` to `export` or `example run` for an FC experiment.
`inspect` prints operators and tensors and writes `inspect.json` when given a run directory.
It rejects a fused FULLY_CONNECTED chain by default. Pass `--allow-fc-chain` to inspect it for experiments.
It also rejects `PACK` and `STRIDED_SLICE` despite their SDK table entries.
Per-channel quantization is informational; the C6 tools-host probe compiled and matched TFLite.
It reads `docs/OPS.md` from the SDK checkout named in `deps.lock` at run time. The kit does not contain a copy.
Use `--sdk-root /absolute/path/to/VectorBlox-SDK` on `inspect` or `example run`, or set `PFKIT_SDK_ROOT`.
If the table is absent, `inspect` reports its path and asks you to run `pfkit deps fetch`.
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
`infer --input input.int8.npy` plans a conversion to the adjacent `input.int8.bin`.
Dry runs print the sample count, byte count, payload SHA-256 and every SSH and SCP command.
They do not write the binary payload or contact either host. An explicit `--run-dir` can write plan and attempt records.
During execution, an existing identical binary is reused. A different binary causes an error; use
`--overwrite-payload` to replace it intentionally. The output and runner JSON directories are created before transfer.
Inference plans accept a `.bin` path only; the CLI performs `.npy` conversion for execution.
The same conversion handles non-contiguous arrays in C element order and rejects empty or non-int8 samples.

Config files require `ssh_target` and `remote_dir` for the kit, or `ssh_target`, `remote_work_dir`
and `size_config` for the tools host. Optional `timeouts` are seconds per remote command:
`{compile: null, sim: 1800, infer: 300}` by default. `null` means no subprocess timeout.
Set a longer compile timeout only when needed. The runner's `--timeout-ms` is a separate device-call limit.
Each remote command uses the stage timeout, including transfers. A timeout is recorded in the stage manifest
when `--run-dir` is set. Remote paths with spaces are quoted in SSH scripts and SCP targets.
`compare` checks float and TFLite outputs. It checks simulator and hardware outputs when supplied.

The kit runner CLI contract is `vbx_run --model m.vnnx --input in.bin --output out.bin --timeout-ms N --json meta.json`.
Its exit codes are 0 for success, 2 for bad arguments or size, 3 for model load or DMA failure, 4 for timeout, and 5 for an NPU error register.
The runner is built separately. The Python package does not build or install it.
