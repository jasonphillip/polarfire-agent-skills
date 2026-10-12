---
name: adapt-your-model
description: Adapt a user model to the pfkit INT8 export and inspection gates.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Adapt your model

Read `docs/contracts.md`, `docs/adapters.md`, and `docs/claims.md`.
Use `dataset-and-training` to create a valid example and checkpoint.
Keep a single graph input and a fixed batch of one for export.
Check that the model input layout and preprocessing match its dataset.

## Adaptation checklist

1. Add `examples/<name>/example.yaml` and its named Python module.
2. Choose `mlp` or `conv2d_1k` from the actual Torch graph.
3. Set shape, layout, dtype, units, normalization, and target scale.
4. Provide train, validation, and test arrays with the contract keys.
5. Choose a calibration split, count, and seed that cover normal inputs.
6. Set float output and raw INT8 simulator tolerances in YAML.
7. Run the small data and training mode before spending the full budget.
8. Inspect the INT8 result before requesting compilation.
9. Compare float and TFLite output before claiming model agreement.

The adapter copies Torch float weights to Keras layers.
The TFLite converter makes new scales and zero points.
The export manifest records calibration indices and quantization values.
Torch observer values, when present, are comparison evidence only.
An SDK operator listing is a filter, not proof of compilation or simulation.

## Export and inspect

Use the same run directory as the data and training stages.
The inspection command writes `inspect.json` and fails on unsupported operations or limits.
Supply `--sdk-root` when the pinned SDK checkout is available.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
"$KIT_ROOT/.venv/bin/python" -m pfkit export signal-freq --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit inspect "$KIT_ROOT/reports/signal-local/model.tflite" --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit compare signal-freq --run-dir "$KIT_ROOT/reports/signal-local"
"$KIT_ROOT/.venv/bin/python" -m pfkit report --run-dir "$KIT_ROOT/reports/signal-local"
```

`compare` checks float against dequantized TFLite at this stage.
Simulator and hardware comparisons say `not run` without their files.
Do not turn an absent comparison into a pass.
Read `docs/claims.md` before interpreting operator or quantization results.
Its defaults keep static shapes and conservative graph choices.
They do not establish a broader SDK capability.
Use `kit-run-inference` after the inspect gate passes.

## Checks

- Read calibration indices, adapter, TFLite hash, and quantization from `export.manifest.json`.
- Read tensor dtypes, shapes, operators, and empty failure lists from `inspect.json`.
- Read float comparison status and any `not run` stages from `compare.json`.
- Read file hashes and command records from `artifacts.json` and `commands.jsonl`.
