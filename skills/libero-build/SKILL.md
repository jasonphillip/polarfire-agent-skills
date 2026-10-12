---
name: libero-build
description: Run the documented Libero build path and audit timing and resource reports.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Libero build

Run Libero on the user-named tools host. Keep its version, project identity, command output, and reports together.

Source: `docs/model-to-v250.md`

## Path A: scaffold

The four scripts form a scaffold. Source them in one Libero Tcl console, in order.

```tcl
source libero/scripts/01_scaffold_proj.tcl
source libero/scripts/02_import_ip.tcl
source libero/scripts/03_smartdesign.tcl
source libero/scripts/04_synth_pnr.tcl
```
Source: `workers/polarfire-hybrid-control/README.md`

Script 01 creates the MPFS250T project. Script 02 imports PID RTL and CoreVectorBlox 2.0.1 with V250 configuration.

Source: `docs/model-to-v250.md`

Script 03 calls itself an early scaffold in its header. Do not claim this path produced the tested image.

Source: `workers/polarfire-hybrid-control/libero/scripts/03_smartdesign.tcl`

Script 04 line 39 uses invalid `-script {REPORT}`. The error is swallowed, so inspect the actual synthesis report.

Source: `workers/polarfire-hybrid-control/libero/scripts/04_synth_pnr.tcl`
Source: `workers/polarfire-hybrid-control/libero/scripts/parallel/README.md`

## Path B: image used on the kit

The tested image came from a clone of Microchip's Icicle Kit VectorBlox reference design plus `libero/scripts/two_slot/`.

Source: `docs/model-to-v250.md`

Run `patch_two_slot.py` first to patch the generated netlist and add the PID subsystem.
Run `build_two_slot_synth.tcl` next to import HDL and synthesize.
Run `build_two_slot_pnr.tcl` for placement, timing, and job export.
Use `rebuild_idfix2.tcl` for the later AXI handshake and actuator latch rebuild.

Source: `docs/model-to-v250.md`

The synthesis script header gives this headless form. Supply a Windows-style script path accepted by Libero.

```bash
libero "SCRIPT:<work-dir>/build_two_slot_synth.tcl"
```
Source: `workers/polarfire-hybrid-control/libero/scripts/two_slot/build_two_slot_synth.tcl`

The source has no V250-only image build script. Treat a V250-only build as manual work.

Source: `docs/model-to-v250.md`

Audit the report directory after the build. `<report-dir>` replaces the Makefile variable `$(REPORT_DIRS)`.

```bash
python3 tools/audit_libero_reports.py --strict <report-dir>
```
Source: `workers/polarfire-hybrid-control/Makefile`

Record timing slack, PID hierarchy, resource use, pruning markers, and the audit exit code.

Source: `workers/polarfire-hybrid-control/tools/audit_libero_reports.py`

## Checks

- Read the selected path and project identity from the Libero log.
- Read synthesis, timing, and programming-job results from the stage logs.
- Read report paths and a successful strict audit result from the audit output.
