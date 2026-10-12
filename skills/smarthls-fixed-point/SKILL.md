---
name: smarthls-fixed-point
description: Check fixed-point behavior for the optional SmartHLS control path.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# SmartHLS fixed point

This skill covers optional fabric control logic.
The pfkit model deployment path does not need a PID design.
Read `docs/scope.md` before treating control as a requirement.
Use the tools host for SmartHLS and keep its version in the record.

## Types and interfaces

Use `hls::ap_fixpt<W,I>` in SmartHLS C++.
Check width, integer bits, signedness, overflow, and rounding.
Check the type at each software and fabric boundary.
The type name alone does not establish numeric behavior.
Record the scale of inputs and outputs.
Record each saturation or wrap rule.
Keep the test vectors with the run.

## Test sequence

Run the checked-in software testbench for the chosen control source.
Keep its exact command, version, output, and exit code.
Compare raw fixed-point output with the stated tolerance.
Record every failed vector and its difference.
Stop before synthesis when a required tolerance fails.
Then keep generated RTL and synthesis output with source identity.
Do not infer kit control behavior from a software test.

The case study uses this test target for its control block:

```sh
make -C /absolute/path/to/tychon-quantum-sensing/workers/polarfire-hybrid-control hls-test
```
Source: `workers/polarfire-hybrid-control/README.md`

Its target invokes `shls sw_run` in the source HLS tree.
Use it only from that source checkout.
Do not run it as a kit-root command.
Read the source Makefile before adapting the target.
Source: `workers/polarfire-hybrid-control/Makefile`

## Evidence

Label software tests, synthesis, and kit output separately.
Use `claim-log` for measured result rows.
Keep the source revision, test input, and report path together.
A passing testbench result does not establish actuator fallback.

## Checks

- Read a passing software testbench result from command output.
- Read fixed-point input and output values from the test log.
- Read tolerance and failed vectors from the test output when present.
- Read a kit control log before claiming deployed behavior.
