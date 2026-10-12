---
name: libero-build
description: Run ordered Libero Tcl stages and audit timing and resource reports.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Libero build

Run on the tools host from the source checkout. Source these Tcl stages in one Libero console, in this order. Stage 05 is a separate SmartPower workload pass after a placed design and a suitable VCD exist.

```tcl
source libero/scripts/01_scaffold_proj.tcl
source libero/scripts/02_import_ip.tcl
source libero/scripts/03_smartdesign.tcl
source libero/scripts/04_synth_pnr.tcl
```
Source: `workers/polarfire-hybrid-control/README.md`

The source has a headless `SCRIPT:` pattern for an existing closure pipeline. Verify the target script's project and report paths before use.

```bash
libero "SCRIPT:libero/scripts/closure_pipeline.tcl"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/closure_pipeline.tcl`

For workload power, verify the selected project and VCD before this separate headless pass. Do not treat vectorless power as workload-measured power.

```bash
libero SCRIPT:libero/scripts/05_smartpower_workload.tcl
```
Source: `workers/polarfire-hybrid-control/libero/scripts/05_smartpower_workload.tcl`

Copy the reports from the tools host using a host-specific transfer that you have reviewed. The source extraction script embeds machine-specific paths; it is not a portable command.

Source: `workers/polarfire-hybrid-control/libero/scripts/extract_reports.sh`

```bash
python3 tools/audit_libero_reports.py --strict $(REPORT_DIRS)
```
Source: `workers/polarfire-hybrid-control/Makefile`

Record timing slack, PID hierarchy, resource footprint, pruning messages, report paths, and audit exit code. Stop on failed closure or strict audit.

Source: `workers/polarfire-hybrid-control/tools/audit_libero_reports.py`
