---
name: kit-program
description: Read device identity and program an approved MPFS250T image.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Kit identity and programming

Read the raw IDCODE before selecting a programming job. The SmartDebug script binds a specific programmer ID and device candidates. Edit a local copy for the attached kit, then inspect its log. The command below replaces the source's local executable and log paths with `<path>`.

```bash
<path>/sdbg.exe SCRIPT:"<path>/libero/scripts/read_idcode.tcl" LOGFILE:"<path>/sdbg_idcode.log"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode.tcl`

Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode.tcl`

The Libero variant opens a hard-coded project before `read_id_code`. Replace that project path in a local copy if you use it.

Source: `workers/polarfire-hybrid-control/libero/scripts/read_idcode_libero.tcl`

Program only after the operator approves the exact image and a rollback image is preserved. Review the job file, device identity, and selected PROGRAM action. The source script contains a fixed job path and should be adapted before use. The command below replaces its local executable and log paths with `<path>`.

```bash
<path>/fpexpress.exe SCRIPT:"<path>/libero/scripts/program_kit.tcl" LOGFILE:"<path>/program.log"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`

Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`

Stop on any programming failure. Preserve the full log and do not retry or cycle power until the operator reviews the failure.

Source: `workers/polarfire-hybrid-control/libero/scripts/program_kit.tcl`
