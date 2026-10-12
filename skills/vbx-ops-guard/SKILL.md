---
name: vbx-ops-guard
description: Check a model graph and exported TFLite operations against the V250 path.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# V250 operation guard

Call `check_model_ops(model, input_shape)` before training at scale. Stop when its report has disallowed or unknown operations.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py`

The guard allows Linear, Conv2d, ReLU, ReLU6, Add, Mean, and AdaptiveAvgPool2d.
It also allows reshape, view, flatten, permute, contiguous, transpose, unsqueeze, and squeeze.
The source lists these as `aten` operations.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py`

The guard bans Conv1d, batch, layer, instance, and group normalization.
It bans sigmoid, tanh, GELU, SiLU, softmax, log-softmax, and max pooling.
It also bans dropout, mul, and matmul.
Its module check catches Conv1d even when export lowers it to Conv2d.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py`

Use Conv2d with `(1, k)` kernels on reshaped input in place of Conv1d.
Keep every tensor dimension static at export.

Source: `workers/odmr-edge-ml/AGENTS.md`

The 2026-07-02 probe limits the guard's interpretation.
`vnnx_compile` accepted sigmoid, tanh, and softmax in single-input graphs.
A two-input graph compiled but produced wrong simulator output.
A GRU cell crashed the compiler.
Keep the model to one graph input.

Source: `workers/polarfire-hybrid-control/docs/vnnx_ops_support_probe_2026-07-02.md`

The guard is a project filter, not a complete compiler specification.
Treat the measured probe and a current compile as separate evidence.

Source: `docs/model-to-v250.md`

After export, call `verify_tflite_ops` on the flatbuffer.
It rejects SHAPE, STRIDED_SLICE, and PACK in this workflow.

Source: `workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py`

Keep the guard report, flatbuffer operator list, and model identity together.
Do not infer kit behavior from a successful export or compiler run.

Source: `docs/model-to-v250.md`

## Checks

- Read an empty disallowed list and an empty unknown list from the guard report.
- Read one static graph input from the exported model metadata.
- Read no banned operators from the TFLite verification output.
