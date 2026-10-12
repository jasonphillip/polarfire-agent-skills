---
name: kit-run-inference
description: Run and log V250 inference through Linux UIO and uncached DMA.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Run inference on the kit

Confirm the active device tree exposes the V250 control page through `generic-uio` and the uncached DMA pool through `/dev/udmabuf-ddr-nc0`. Match the loaded model and bitstream before inference.

Source: `workers/polarfire-hybrid-control/README.md`

Run the source smoke helper on the kit from the directory containing the model and executable.

```bash
./vnnx_smoke fcnn_v2_residual_dataset_a.vnnx
```
Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

The example filename is specific to the source model. For another model, use its own file and log the exact command, output, device version, and errors. A completed run does not prove input fidelity.

Source: `workers/polarfire-hybrid-control/docs/rung_f_v250_on_silicon_results_2026-06-16.md`

The source loop dequantizes the V250 output, writes the AI term to the fabric PID, starts the controller, and reads the actuator and watchdog status. Verify clamp setup before claiming the AI term reached the actuator.

Source: `workers/polarfire-hybrid-control/docs/v250_pid_loop_2026-06-21.md`

```bash
./v250_pid_loop fcnn_v2_residual_dataset_a.vnnx 50 2 odmr_v250_rows.csv
```
Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

This is a worked-example invocation with replayed input. Replace model and CSV only after checking the helper's expected shape and layout. Save the CSV output as the result report.

Source: `workers/polarfire-hybrid-control/firmware/linux/v250_pid_loop.c`
