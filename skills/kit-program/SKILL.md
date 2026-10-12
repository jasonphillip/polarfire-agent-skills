---
name: kit-program
description: Check device identity and program an approved MPFS250T image.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Kit identity and programming

Read `docs/hardware.md` before changing the kit.
The model inference path needs a V250-enabled image.
The current kit build script creates a job but does not program the device.
Programming changes persistent hardware state.
Get operator approval for the exact image and target before programming.

## Identity

Read the raw device IDCODE and selected programmer.
Match both to the intended MPFS250T kit.
Record the currently loaded image identity.
Keep the previous programming job and its hash.
Write the exact rollback action into the run record.
Stop if identity or image provenance is unclear.

## Programming

Review the candidate job and generated core configuration.
Confirm CoreVectorBlox 2.0.1 with V250 in the generated IP.
Read the timing and resource reports for that job.
Program only the reviewed job.
Save the complete FlashPro log and job hash.
Stop on any programming error.
Keep the rollback job available.

The case study includes SmartDebug and FlashPro Tcl examples.
They bind local programmer and project paths.
Adapt a local copy only after checking those bindings.

## Linux image

The SD-card image step is separate from FPGA programming.
Decompress the selected `.wic.gz` before writing its `.wic`.
Check the destination device before the write.
Boot and inspect HSS, U-Boot, and Linux output.
Check the V250 UIO node and uncached DMA device.
Use `docs/hardware.md` for the overlay and runner path.
Do not infer the bitstream from a booted Linux image.

## Evidence

Keep the IDCODE, job hash, tool output, and boot log together.
Name the image and board beside any inference result.
Use `claim-log` to cite each raw output file.
A programming pass does not prove model inference.

## Checks

- Read device IDCODE and programmer from the identity output.
- Read the approved job hash and rollback action from the run record.
- Read PROGRAM success and job identity from the FlashPro log.
- Read boot stages and device nodes from kit output.
