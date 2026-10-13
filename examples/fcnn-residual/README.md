# FCNN residual worked example

The public source is https://github.com/jasonphillip/tychon-quantum-sensing. Use these exact paths in its checkout:

- `workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py`
- `workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py`
- `workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py`
- `workers/odmr-edge-ml/scripts/fix_fcnn_export.py`
- `workers/polarfire-hybrid-control/models/README.md`
- `workers/polarfire-hybrid-control/firmware/linux/v250_pid_loop.c`
- `workers/polarfire-hybrid-control/docs/v250_pid_loop_2026-06-21.md`
- `workers/polarfire-hybrid-control/docs/rung_f_v250_on_silicon_results_2026-06-16.md`

The FCNN export script expects its own checkpoint and calibration data. It is an example of static-shape INT8 export, not a model-independent exporter. The source reports replayed ODMR input on its kit. Run the checks again for your model and kit.

For a runnable FCNN without a residual add, see `examples/odmr-fcnn` and `evidence/2026-10-13-odmr-fcnn/README.md`.
