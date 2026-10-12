# PolarFire Agent Skills

![Agent Skills](https://img.shields.io/badge/Agent_Skills-Standard-7B2D8E)
![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-F07535)
![Codex](https://img.shields.io/badge/Codex-Compatible-412991)
![Cursor](https://img.shields.io/badge/Cursor-Compatible-000000)
![License](https://img.shields.io/badge/License-Apache--2.0-blue)

This pack gives a coding agent an ordered workflow and evidence rules for model deployment and fabric control on the Microchip PolarFire SoC. It targets the MPFS250T kit and CoreVectorBlox V250.

## Quick Start

Clone this repository and add the clone as a plugin in Claude Code, Codex, or Cursor. One clone carries all ten skills, and updating the clone updates the pack. Pick one install method so each skill loads once.

In Claude Code, install from the marketplace.

```text
/plugin install polarfire-agent-skills --marketplace jasonphillip/polarfire-agent-skills
```

Or point Claude Code at the local clone.

```bash
claude --plugin-dir /path/to/polarfire-agent-skills
```

For Codex and Cursor, install the local clone as a plugin. The command is in each client's plugin docs.

I loaded the pack in Claude Code on 2026-10-12 and it listed all ten skills.

After the install, select `polarfire-bringup` for the complete path, or invoke a skill by name. `docs/getting-started.md` lists the checks to run before a kit run.

### Prerequisites

| Item | Required state |
|---|---|
| Kit | PolarFire SoC MPFS250T kit with a V250-enabled image |
| Tools host | x86 machine with Libero SoC, SmartHLS, and VectorBlox SDK installed |
| SDK and IP | VectorBlox SDK v2.0.3 paired with CoreVectorBlox IP v2.0.1 |
| Kit Linux | A compatible image with `generic-uio` and uncached DMA device support |
| Source checkout | A local checkout of the worked example for scripts and tests |

The pack doesn't ship Microchip tools, a Yocto image, or a `.vnnx` file. Install those separately and check their versions before use.

## Skills

| Skill | Use |
|---|---|
| `vbx-ops-guard` | Check graph and TFLite operations. |
| `vbx-export-int8` | Train and export static INT8 TFLite. |
| `vbx-compile` | Compile for V250 and hash the output. |
| `libero-build` | Run ordered Tcl stages and audit closure. |
| `smarthls-fixed-point` | Use SmartHLS fixed point and test the PID. |
| `kit-program` | Read IDCODE and program an approved image. |
| `kit-run-inference` | Run V250 inference and inspect the fabric output. |
| `fabric-watchdog-fallback` | Measure watchdog trip and fallback behavior. |
| `claim-log` | Link each claim to a report file. |
| `hls4ml-libero-route` | Evaluate Dense-only fabric inference. |

`agents/polarfire-bringup.md` orders the ten skills from model to kit. `SOURCES.md` maps every skill to its source files. `examples/fcnn-residual/README.md` points to the worked example.

## Evidence boundary

A tool output supports only the run it came from, so keep the command, inputs, versions, raw output, and report path together. The hardware results in the source repo came from my kit. Rerun them before you quote them for yours.

Copyright 2026 Jason Phillip, Tychon AI. Licensed under Apache-2.0.
