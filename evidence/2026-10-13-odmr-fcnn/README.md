# odmr-fcnn: first convolution-route model on the kit (2026-10-13)

Example `examples/odmr-fcnn` (adapter `conv2d_1k`): the case study's ODMR FCNN (three `(1,5)` stride-2 convolutions with ReLU, a `(1,spatial)` head, Flatten), trained on the same simulated ODMR spectra as `odmr-mlp`. Input `[1,1,1,100]` NCHW, output microtesla.

Run: `pfkit example run odmr-fcnn --until compare --samples 64`, on the kit's case-study seed7 V250 image (before any kit-built image). Records in `case-study-image/` (scrubbed by `tools/record_evidence.py`).

| check | result |
|---|---|
| inspect | no blocking flag; operators `CONV_2D` x4, `RESHAPE` |
| compile (tools host) | completed |
| simulator | completed after the runner fix for a model input shape with a leading batch of 1 (`pfkit/remote/vbx_sim_run.py`) |
| kit | 64 of 64 completed, NPU error 0; wall time median 0.038 ms, max 0.083 ms (quiet-board sample, not a worst-case bound) |
| simulator vs kit | 0 LSB, exact |
| TFLite vs simulator | 0 LSB, exact |
| float vs INT8 TFLite prediction difference | **failed**: largest per-sample difference 29.8 µT against the example's 5.0 µT tolerance |
| float model error against ground truth | MAE 13.5 µT, RMSE 16.4 µT (100 test samples, `eval.json`) |

Reading, in two separate parts:

- Hardware parity: exact. The kit reproduces the simulator, and the simulator reproduces the INT8 TFLite model, on all 64 samples.
- Conversion accuracy: below the example's tolerance. The 29.8 µT figure is the largest difference between the float and the INT8 prediction for one sample; it is not an error against ground truth. On the kit-built image the same run gives a mean difference of 2.39 µT and one sample of 64 over the 5.0 µT tolerance; float and INT8 errors against ground truth are about equal (MAE 14.0 and 13.9 µT on those 64 samples); `odmr-mlp` has a 1.67 µT largest difference (`evidence/2026-10-13-kit-built-image/README.md`, `odmr-fcnn/accuracy.json`).

The overall result stays failed; the tolerance was not raised. The cause of the one large difference was not investigated.
