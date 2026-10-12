---
name: kit-program
description: Read device identity and program an approved MPFS250T image.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Kit identity and programming

Read the raw IDCODE before selecting a programming job.
The SmartDebug script binds a specific programmer and device candidates.
Edit a local copy for the attached kit, then inspect its log.

Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode.tcl`

This invocation replaces source-specific executable and log paths with `<path>`.

```bash
<path>/sdbg.exe SCRIPT:"<path>/libero/scripts/read_idcode.tcl" LOGFILE:"<path>/sdbg_idcode.log"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode.tcl`

The Libero alternative opens a fixed project before reading IDCODE.
Replace its project path in a local copy if you use it.

Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode_libero.tcl`

Before programming, record the hash of the job being replaced.
Record the exact rollback command and preserve the rollback job.
The source applied this habit before each persistent programming change.

Source: `workers/polarfire-hybrid-control/README.md`

Review the new job, device identity, and selected PROGRAM action.
Get operator approval for the exact image before changing the kit.
Adapt the source script's fixed job path in a local copy.

Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`

This invocation replaces source-specific executable and log paths with `<path>`.

```bash
<path>/fpexpress.exe SCRIPT:"<path>/libero/scripts/program_kit.tcl" LOGFILE:"<path>/program.log"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`

Stop on any programming failure. Keep the full log for review.

Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`

The SD-card image step is manual. Decompress the `.wic.gz` with `gunzip` first.
Then write the resulting `.wic` with `dd` or USBImager.
Check the destination device twice before writing.

Source: `workers/polarfire-hybrid-control/firmware/linux/README.md`

Boot the kit from SD and inspect HSS, U-Boot, and Linux output.

Source: `docs/model-to-v250.md`

## Checks

- Read the raw IDCODE and connected programmer from the SmartDebug output.
- Read the replaced job hash and exact rollback command from the run record.
- Read PROGRAM success and job identity from the FlashPro log.
- Read the boot stages from the serial console after the manual SD-card step.
