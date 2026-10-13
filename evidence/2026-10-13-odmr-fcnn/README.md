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
| float vs TFLite | **failed**: max 29.8 µT against the example's 5.0 µT tolerance |
| float model test error | MAE 13.5 µT, RMSE 16.4 µT (100 test samples) |

Reading: the deployment path is exact: the kit reproduces the simulator, and the simulator reproduces the int8 TFLite model. The int8 quantization of this float model loses up to 29.8 µT. For comparison, `odmr-mlp` loses at most 1.67 µT under the same tolerance (`reports` run of 2026-10-13, not committed). The example is therefore not a passing example; its tolerance was not raised. The cause of the quantization loss was not investigated.
