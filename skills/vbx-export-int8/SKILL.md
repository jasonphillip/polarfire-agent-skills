---
name: vbx-export-int8
description: Route INT8 export requests to the pfkit model adaptation workflow.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# INT8 export entry

Use `adapt-your-model` for the canonical export and inspect commands.
Use `dataset-and-training` when a dataset or checkpoint must be created.
This skill keeps the earlier name available for discovery.
It does not define a second converter path.

## Inputs

Ask for the example name and its run directory.
Read its `example.yaml` for shape, layout, units, and adapter.
Read `dataset.manifest.json` for the dataset identity.
Read `training.json` for the checkpoint hash and epoch count.
Check that the run directory belongs to the selected example.

## Decision path

If the example is new, follow `dataset-and-training` first.
If the checkpoint exists, follow `adapt-your-model` at export.
Its steps create `model.tflite` and `export.manifest.json`.
Its inspection step creates `inspect.json`.
Do not substitute the case study's export script.
That script targets a different model and converter path.

The converter receives one fixed input shape.
The adapter checks Torch and Keras output agreement on a sample.
The converter uses a representative set from the selected split.
It quantizes input and output to INT8.
The manifest records whether the fallback quantizer was used.
It records a primary converter error when fallback occurred.

## Evidence

Keep the run directory together with the exported model.
Record the calibration indices before interpreting output agreement.
Treat Torch fake quantization scales as comparison evidence.
The converter generates new tensor quantization values.
Use the float comparison tolerance from the example contract.
Keep a failed inspect result visible and stop before compile.
Use `docs/claims.md` for current probe limits.

## Checks

- Read the adapter and calibration indices from `export.manifest.json`.
- Read the TFLite size and SHA-256 from `export.manifest.json`.
- Read input and output INT8 metadata from `inspect.json`.
- Read empty unsupported and limit violation lists before compile.
