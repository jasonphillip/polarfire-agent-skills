---
name: smarthls-fixed-point
description: Use SmartHLS fixed-point types and run the software testbench.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# SmartHLS fixed point

Use `hls::ap_fixpt<W,I>` for SmartHLS fixed-point code. Check width, integer bits, signedness, overflow, and rounding at every interface. The source warns against the similarly named type from another toolchain.

Source: `workers/polarfire-hybrid-control/README.md`

Run the checked-in software testbench before synthesis.

```bash
make hls-test
```
Source: `workers/polarfire-hybrid-control/README.md`

The make target invokes `shls sw_run` in `hls/`. Preserve the test output and report failures before continuing to Libero.

Source: `workers/polarfire-hybrid-control/Makefile`

Compare fixed-point outputs with the testbench's stated tolerance. Record failing vectors and their raw values.

Source: `workers/polarfire-hybrid-control/hls/tb/tb_bumpless.cpp`

Check overflow and rounding at the software and fabric interface. A type name alone does not establish numeric behavior.

Source: `workers/polarfire-hybrid-control/README.md`

Keep the SmartHLS version, test input, command output, and exit code in the run record.

Source: `workers/polarfire-hybrid-control/AGENTS.md`

## Checks

- Read a passing software testbench result from `make hls-test` output.
- Read fixed-point input and output values from the test log.
- Read any failing vector and tolerance from the test output before continuing.
