---
name: fabric-watchdog-fallback
description: Check watchdog trip time and PID fallback at the actuator.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Watchdog and fallback

The fabric counter clears on a V250 completion heartbeat and asserts a level timeout. The controller uses that timeout to transfer to PID-only output at a subsequent start. A halted control process cannot compute a new fallback output until it resumes.

Source: `workers/polarfire-hybrid-control/libero/hdl/watchdog_timer.v`
Source: `workers/polarfire-hybrid-control/docs/watchdog_fallback_test_plan.md`

Measure clear-to-trip time with the read-only CSR observer. Compare each clear and trip timestamp. Report poll gaps alongside the distribution.

Source: `workers/polarfire-hybrid-control/docs/watchdog_trip_measured_2026-07-01.md`

For actuator fallback, collect paired observer and control CSV files. Inspect AI-mode movement, the first PID-only update, actuator continuity, and recovery. Keep the raw files and image identity.

Source: `workers/polarfire-hybrid-control/tools/run_wd_fallback.sh`

The source analyzer has documented issues in some criteria. Confirm conclusions against raw CSV and the later results notes before making a measured claim.

Source: `workers/polarfire-hybrid-control/docs/watchdog_fallback_test_plan.md`

The SmartHLS C++ watchdog is a design reference. The deployed fabric timer is the RTL module.

Source: `workers/polarfire-hybrid-control/hls/src/watchdog.cpp`

Do not infer actuator fallback from the timeout flag alone. Read the actuator output after transfer to PID-only mode.

Source: `workers/polarfire-hybrid-control/docs/watchdog_fallback_test_plan.md`

Keep the observer and control timestamps aligned. Record gaps in either stream before computing trip timing.

Source: `workers/polarfire-hybrid-control/docs/watchdog_trip_measured_2026-07-01.md`

Name the loaded image and source input beside each raw CSV. Treat a replay as a replay result.

Source: `workers/polarfire-hybrid-control/tools/run_wd_fallback.sh`

## Checks

- Read a clear and later trip timestamp from the CSR observer output.
- Read poll gaps and the trip interval from the timing report.
- Read a PID-only actuator update from paired raw CSV output.
- Read recovery behavior and image identity from the run record.
