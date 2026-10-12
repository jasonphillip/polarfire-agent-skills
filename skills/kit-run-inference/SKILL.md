---
name: kit-run-inference
description: Run and log V250 inference through Linux UIO and uncached DMA.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Run inference on the kit

Run kit commands over SSH to the user-named kit host. Match the loaded model, overlay, and bitstream before inference.

Source: `docs/model-to-v250.md`

Use the two-slot overlay with the two-slot image. Apply it every boot; runtime overlays do not persist.

```bash
dtc -@ -O dtb -o two_slot_vbx_pid.dtbo two_slot_vbx_pid.dtso \
    -Wno-reg_format -Wno-avoid_default_addr_size
mkdir -p /sys/kernel/config/device-tree/overlays/two_slot
cat two_slot_vbx_pid.dtbo > /sys/kernel/config/device-tree/overlays/two_slot/dtbo
```
Source: `workers/polarfire-hybrid-control/firmware/linux/two_slot_vbx_pid.dtso`

Check that `generic-uio` exposes a node named `vbx`. Check the uncached DMA device too.

```bash
ls -l /dev/uio*
cat /sys/class/uio/uio*/name
ls /dev/udmabuf-ddr-nc0
```
Source: `docs/model-to-v250.md`

The DMA pool uses `/dev/udmabuf-ddr-nc0`. The base device tree must reserve its memory at boot.

Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

Run the bounded `vbx_probe` before the smoke helper. Its output shows control, error, and version registers.

Source: `workers/polarfire-hybrid-control/firmware/linux/vbx_probe.c`

Run this kit-local part of the source invocation from the model directory.

```bash
./vbx_probe fcnn_v2_residual_dataset_a.vnnx
```
Source: `workers/polarfire-hybrid-control/docs/two_slot_handoff_2026-06-17.md`

The source smoke invocation uses the embedded test input in the named model.

```bash
./vnnx_smoke fcnn_v2_residual_dataset_a.vnnx
```
Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

The smoke helper polls without a bound. Stop if the probe reports a stalled or errored NPU.

Source: `workers/polarfire-hybrid-control/firmware/linux/vnnx_smoke.c`

Dequantize each INT8 output with `(q - zero_point) * scale_fix16 / 65536`.

Source: `workers/polarfire-hybrid-control/firmware/linux/vnnx_smoke.c`

For replayed input, the source loop quantizes CSV rows and writes the AI term to the PID.

```bash
./v250_pid_loop fcnn_v2_residual_dataset_a.vnnx 50 2 odmr_v250_rows.csv
```
Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

Match the helper's input shape and layout before using another model or CSV.

Source: `workers/polarfire-hybrid-control/firmware/linux/v250_pid_loop.c`

Never read or write `0x60001000`. That page is the DMA controller, not the PID.

Source: `workers/polarfire-hybrid-control/firmware/linux/two_slot_vbx_pid.dtso`
Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

## Checks

- Read `vbx` from the UIO name output and the DMA device from the device listing.
- Read `RESULT: INFERENCE COMPLETED` and the version register from the bounded probe output.
- Read `inference complete.` and output quantization metadata from the smoke output.
- Read actuator and watchdog fields from the replay output before claiming control behavior.
