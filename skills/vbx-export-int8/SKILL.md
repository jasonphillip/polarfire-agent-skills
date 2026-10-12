---
name: vbx-export-int8
description: Train with QAT and export a static-shape INT8 TFLite model.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# QAT and INT8 export

Use `prepare_model_qat` for FX graph QAT. The implementation uses symmetric per-tensor INT8 for activations and weights. Preserve calibration input order and record the checkpoint and dataset hashes.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py`

The first-train script checks data and gradient plumbing with a throwaway MLP. It is not the production export path.

```bash
python scripts/run_first_train.py
```
Source: `workers/odmr-edge-ml/scripts/run_first_train.py`

For the worked FCNN, the export script loads a fixed checkpoint, builds static NHWC batch-one Keras input, copies weights, checks float fidelity, calibrates, and exports INT8 TFLite.

```bash
python scripts/fix_fcnn_export.py
```
Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`

Check the emitted input and output dtypes, tensor scales, and operator list. Stop before compile if the shape or operation check fails. This script is model-specific; adapt it for another model.

Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`
