---
name: vbx-ops-guard
description: Check a model graph and exported TFLite operations against the V250 path.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# V250 operation guard

Use `check_model_ops(model, input_shape)` before a costly training run. Stop if `disallowed` or `unknown` is nonempty. Its module check catches Conv1d even when export lowers it to Conv2d. This whitelist is a project guard, not a complete SDK specification.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py`

Use static input dimensions. The source guide allows Conv2d, Linear, ReLU, ReLU6, Add, Mean, and simple layout operations. It rejects normalization, sigmoid, softmax, pooling, and general matrix multiplication.

Source: `workers/odmr-edge-ml/AGENTS.md`

After export, call `verify_tflite_ops` on the flatbuffer. It rejects SHAPE, STRIDED_SLICE, and PACK. Stop if any unknown operation or compiler error appears.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py`

There is no generic model-independent shell command for this guard in these source files. Integrate the Python functions with the model code.
