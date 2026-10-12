# Separate PID and watchdog example

The V250-only hardware path in `hw/` does not control the PID or watchdog. The case study keeps that design in `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/`.

Start with its `hls/` controller, `libero/hdl/` integration, `firmware/linux/v250_pid_loop.c`, and `docs/watchdog_fallback_test_plan.md`. The dated watchdog measurements are in `docs/watchdog_trip_measured_2026-07-01.md`. See the case study's `README.md:7-12,130-142` for the overall result.

The case study measured a watchdog clear-to-trip median of **2.000 ms over 120 trips** (`deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/watchdog_trip_measured_2026-07-01.md`; summary at `README.md:9,140-142`). It measured **66–71 µs** from timeout rise to the first PID-only update when a controller update saw the timeout (`docs/watchdog_fallback_test_plan.md:188-201`). The later trip-start software fix recovered **20/20** short pulses and **10/10** paused-process trials after resume (`docs/watchdog_fallback_test_plan.md:217-227`). These numbers belong to the case study image and workload.

The case-study README states the remaining limit verbatim: “A processor that stays frozen gets no fallback until it resumes, and at recovery the actuator still steps by about 0.01, ten times the slew limit” (`deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/README.md:9`). The retest records the same limitation at `docs/watchdog_fallback_test_plan.md:227-232`.

This example is a guide to the separate case study. This kit has not rebuilt that PID image or repeated those measurements.
