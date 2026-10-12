---
name: vbx-compile
description: Compile INT8 TFLite for CoreVectorBlox V250 and record artifact identity.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Compile for V250

Run on the tools host with VectorBlox SDK v2.0.3 and CoreVectorBlox IP v2.0.1. Use the TFLite produced by the export check.

```bash
vnnx_compile -c V250 -t <model>_integer_quant.tflite -o <model>.vnnx
```
Source: `workers/polarfire-hybrid-control/models/README.md`

The placeholders replace model names in the source command. Record SDK version, input hash, output byte size, and output SHA-256 in a report beside the artifact.

```bash
sha256sum models/fcnn_v2_residual_dataset_a.vnnx
```
Source: `workers/polarfire-hybrid-control/models/README.md`

The hash command is the worked-example form; replace the model filename for a new model. Stop on nonzero exit or `VECTORBLOX ERROR` in stderr.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py`

Read the installed SDK version before compiling. The tutorial pairs SDK v2.0.3 with CoreVectorBlox IP v2.0.1.

```bash
pip show vbx
```
Source: `docs/model-to-v250.md`

Keep the input TFLite hash with the output hash. Compare byte size and hash only for the same input and SDK.

Source: `workers/polarfire-hybrid-control/models/README.md`

Treat successful compilation as an artifact check. Run a separate simulator or kit check for behavior.

Source: `docs/model-to-v250.md`

## Checks

- Read SDK version 2.0.3 from the package output.
- Read successful compiler exit and no `VECTORBLOX ERROR` from its output.
- Read the artifact byte size and SHA-256 from file tool output.
