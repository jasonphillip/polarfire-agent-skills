---
name: libero-build
description: Build the Icicle reference design and inspect timing and resource output.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Libero build

Read `docs/hardware.md` and `docs/scope.md`.
Use the tools host for Libero and the pinned reference design.
The kit's build entry is `hw/build_reference_design.sh`.
Set `DEVICE`, `VBX_SIZE`, `CORE_VERSION`, `WORK_DIR`, and `LIBERO`.
Use an absolute, new `WORK_DIR` and keep its logs.
The script copies the reference design into that directory.
It does not program the kit.

## Before build

Check the Libero version and licence.
Check the reference design revision.
Check that the licensed CoreVectorBlox IP is available offline.
Use MPFS250T, V250, and CoreVectorBlox 2.0.1 for the tested profile.
Read the generated IP configuration after the build.
Confirm the core version and preset before programming.
Treat other V sizes as untested in this kit.

## Build command

Run the command from this repository on the tools host.
Choose local absolute values for the two path variables.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
export DEVICE=MPFS250T
export VBX_SIZE=V250
export CORE_VERSION=2.0.1
export WORK_DIR=/absolute/build-directory
export LIBERO=/absolute/path/to/libero
bash "$KIT_ROOT/hw/build_reference_design.sh"
```

The reference Tcl receives timing verification and programming-job export options.
Keep its full command output, generated job, synthesis, timing, and resource reports.
A script exit alone does not prove timing closure.
Read the reports for slack and core identity.
Do not promote a source case study image to this build's result.

## Source boundary

The case study used its own two-slot image and Tcl sequence.
Those scripts are not the kit's build entry.
Read the case study only when adapting its PID subsystem.
Use `fabric-watchdog-fallback` for the optional control experiment.

## Checks

- Read the selected device, core version, and V size from generated IP output.
- Read the build exit and exported job path from the Libero output.
- Read timing slack and resource values from the generated reports.
- Read the exact report path beside every hardware build claim.
