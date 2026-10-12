---
name: dataset-and-training
description: Define a pfkit example, validate its data, and train its Torch model.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Dataset and training

Work from the kit root with its Python 3.11 environment.
Read `docs/contracts.md` and the selected `examples/<name>/example.yaml` first.
An example needs `example.yaml` and the named Python module.
The module exports `generate(splits, seed)` and `model()`.
The generator returns train, val, and test input and target pairs.

## Example contract

Set `name`, `module`, and one supported `adapter` in the YAML file.
Set input shape, layout, dtype, units, and normalization.
Set output shape, dtype, units, and `target_scale`.
Set calibration split, sample count, and seed.
Set float and simulator tolerances.
Set default and full split sizes and epoch counts.
Set data seed, model seed, and learning rate.
Use `signal-freq` and `odmr-mlp` as complete examples.

`mlp` accepts one input and one output with Linear, ReLU, ReLU6, and Flatten.
`conv2d_1k` accepts restricted `(1,k)` Conv2d, activation, optional pooling, Flatten, and Linear.
Read `docs/adapters.md` for exact graph rules.
Branches, extra inputs, dynamic shapes, Conv1d, and Sigmoid are rejected.
The data stage checks float32 arrays, equal input and target counts, and input shape.
An unsupported graph fails during export with `UnsupportedModelError`.

## Run

Use a new run directory for each input and mode.
The default mode uses the small split and epoch budget in YAML.
Pass `--full` to both data and train for the larger configured budget.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
"$KIT_ROOT/.venv/bin/python" -m pfkit data signal-freq --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit train signal-freq --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit eval signal-freq --run-dir "$KIT_ROOT/reports/signal-local"
```

For external arrays, add `--import /absolute/path/data.npz` to `pfkit data`.
The archive needs `train_x`, `train_y`, `val_x`, `val_y`, `test_x`, and `test_y`.
For the full mode, append `--full` to the data and train commands.
The stages write `dataset.npz`, `dataset.manifest.json`, `model.pt`, `training.json`, and `eval.json`.
The manifest records split sizes, units, normalization, seed, and data hash.
The checkpoint stores the Torch state dictionary.
Evaluation reports test MAE, RMSE, units, and sample count.
Proceed to `adapt-your-model` for export and comparison.

## Checks

- Read split sizes, array shapes, dtypes, and hash from `dataset.manifest.json`.
- Read the epoch count, loss curve, seeds, and checkpoint hash from `training.json`.
- Read test units, sample count, MAE, and RMSE from `eval.json`.
