---
name: vbx-export-int8
description: Train with QAT and export a static-shape INT8 TFLite model.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# QAT and INT8 export

Use `prepare_model_qat` for FX graph QAT. Preserve input order and record the checkpoint and dataset hashes.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py`

The QAT code uses symmetric INT8 with one scale per tensor for activations and weights.
The VectorBlox SDK 2.0.x path uses per-tensor weights, not per-channel weights.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py`

The source FCNN has a `view()` that reads the batch size at runtime.
That dynamic batch can leak SHAPE, STRIDED_SLICE, and PACK into TFLite.
The compiler rejects those operators.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn_v2.py`

Use a fixed batch of one and an already-shaped NHWC input for the worked FCNN export.
The script copies trained weights, calibrates, converts, and checks the result.

```bash
python scripts/fix_fcnn_export.py
```
Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`

For another model, copy these converter settings from the source script.
Choose representative samples that span its expected input range.

```python
converter = tf.lite.TFLiteConverter.from_keras_model(tf_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```
Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`

The source representative dataset yields one sample per call.
It caps calibration at 1,000 samples.

Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`

Check input and output dtypes, tensor scales, static shape, and operator list.
Stop before compilation if the exported graph contains banned operations.

Source: `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`
Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py`

## Checks

- Read an exported TFLite path and byte size from the converter output.
- Read INT8 input and output dtypes with fixed input dimensions from model metadata.
- Read no SHAPE, STRIDED_SLICE, or PACK from the operator check output.
- Read the representative sample count from the export log.
