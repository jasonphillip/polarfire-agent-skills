---
name: fabric-watchdog-fallback
description: Check watchdog trip timing and actuator fallback in an optional control path.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Watchdog and fallback

This is an optional control experiment.
The core model path does not require it.
Read `docs/scope.md` before adding it to a bring-up plan.
The case study used a fabric counter cleared by V250 completion.
It transferred to PID-only output after timeout at a later start.
A halted control process could not compute another output until it resumed.

## Plan the measurement

Name the image and control build in the run record.
Name the observer and actuator input files.
Record the expected clear and trip signals.
Keep a bounded observation period.
Do not use a timeout bit alone as evidence of actuator fallback.
Keep the raw observer and control streams.
Align their timestamps before calculating trip intervals.

## Trip check

Read each clear timestamp and the following trip timestamp.
Report poll gaps with the measured interval.
Keep any missed sample or time jump visible.
Do not infer a precise trip time from a sparse poll stream.
Read the actual counter settings from the loaded image.

## Fallback check

Observe AI-mode actuator movement before the trip.
Observe the first PID-only actuator update after the trip.
Check output continuity and recovery behavior.
Preserve the paired CSV files and the image identity.
Treat replayed input as a replay result.
Use a separate run for a live sensor result.

## Source boundary

The source analyzer has documented issues for some criteria.
Check its conclusion against raw CSV before using the number.
The SmartHLS watchdog C++ file is a design reference.
The deployed timer in the case study was RTL.

## Checks

- Read a clear and later trip timestamp from the observer output.
- Read poll gaps and interval values from the timing output.
- Read a PID-only actuator update from paired raw CSV output.
- Read recovery behavior and image identity from the run record.
