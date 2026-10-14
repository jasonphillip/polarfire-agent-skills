# deployed-fcnn: the case study's deployed residual model on the kit (2026-10-14)

The deployed INT8 TFLite of `tychon-quantum-sensing` (`workers/odmr-edge-ml/exports/fcnn_v2_residual_dataset_a_int8.tflite`, 7,656 bytes, sha256 `e3b55da9…`), run as a bare model through `pfkit inspect` → `compile` → `sim` → `infer` (no registered example; the float side and the labels are handled by that repository's `experiments/deployed_model_on_kit.py`). Input `[512, 2, 1, 100]` int8 in model (NCHW) order: 512 held-out rows of the original `production_50k_v2_aic` test split, two channels (normalized spectrum, Gaussian PID anchor). Output: one int8 per sample (field correction, scale 0.0229, zero point 1).

| Stage | Result |
|---|---|
| compile (tools host, V250) | `model.vnnx` 12,832 bytes, sha256 `55bf88b7…`. The June 2026 bring-up recorded `6c5cd21a…` for the same TFLite at the same size (SDK 2.0.3 toolchain): the compiler build differs; the new file is bit-exact against the TFLite below |
| simulator | 512 of 512 |
| kit | 512 of 512, `npu_error 0`; wall time median 0.038 ms, p90 0.038 ms, max 0.069 ms (NPU start to poll, quiet board) |
| INT8 TFLite vs simulator | 0 LSB |
| simulator vs kit | 0 LSB |
| accuracy against the labels (computed in odmr-edge-ml) | final-field MAE float 14.467 µT, INT8-CPU 14.474, simulator 14.474, kit 14.474; PID-only 15.209; float vs INT8 residual max 0.703 µT, MAE 0.031 |

Pass criteria were set before the run (float vs INT8 max ≤ 5 µT and MAE ≤ 0.5; 0 LSB TFLite→simulator; 0 LSB simulator→kit; kit final-field MAE ≤ float + 0.2 µT): all four PASS. Files here were copied and scrubbed by `tools/record_evidence.py`; `compare.json` and `accuracy.json` do not exist for this run because the comparison lives in `tychon-quantum-sensing` (`workers/odmr-edge-ml/docs/deployed_model_on_kit_2026-10.md`). Kit image: overlay `vbx_only`, node `vbx@60030000`.
