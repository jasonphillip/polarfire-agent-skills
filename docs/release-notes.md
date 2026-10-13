# v0.1.0 (initial, scoped)

## What it is

This kit gives coding agents a staged path from two example models to INT8
TFLite, V250 compilation, simulation, and inference on an Icicle Kit.
It includes skill files, a Python pipeline, a fabric build wrapper, and an
inference runner.

## Supported configuration

The target is one MPFS250T Icicle Kit with CoreVectorBlox V250 and Linux.
The tested orchestration hosts are Linux aarch64 and macOS arm64 with Python
3.11. The tools host uses x86 Windows with Libero SoC 2025.2 and SmartHLS
2025.2, plus WSL Ubuntu with VectorBlox SDK 2.0.3.
The kit needs the V250 image, `generic-uio`, `udmabuf`, and SSH access.
The ODMR example also needs Tk with Homebrew Python 3.11 on macOS.
See `docs/scope.md` for the bounded adapter set and other targets.

## Validated

Both examples completed compile, simulation, and inference on one kit.
Each 64-sample held-out batch matched the simulator at 0 LSB.
The 64-sample CLI route passed on the case-study kit image for both examples:
complete comparisons, 0 LSB simulator versus hardware, and `hw.bin` files
byte-identical to the 2026-10-12 batch
(`evidence/2026-10-13-hardware-cli-route/README.md`).
Claude Code with only this plugin ran `signal-freq` through compare on the kit;
this was one assistant, one example and one run. It loaded
`kit-run-inference` and `claim-log`, without invoking the agent as a subagent
(`evidence/2026-10-13-assistant-run/README.md`). The earlier Claude Code and
Codex client checks reached inspect (`docs/validation.md`).

## Known limits

The kit's own Libero build ran on 2026-10-12 on the tools host: timing met, programming job exported, kit not programmed with it (docs/validation.md, evidence/2026-10-12-libero-build/).
The `prepare-input --samples 64` route regenerated both historical batch
payloads byte for byte on the host
(`evidence/2026-10-13-release-readiness/payload-regeneration.md`).
The clean clone reproduced the full `signal-freq` route after building the
runner. A public GitHub clone, cold pip cache and another machine were not
tested (`evidence/2026-10-13-clean-clone/README.md`).
No co-simulation or forced hardware NPU timeout was run.
A Codex plugin install and Cursor loading were not tested.
Codex and Cursor remote workflows were not tested
(`evidence/2026-10-13-assistant-run/README.md`).
Other boards, V sizes, and SDK 3.x are outside this release's validated path.

## What users supply

To compile and simulate, supply a tools host with the pinned software and
required Libero licences. To run inference, supply an MPFS250T Icicle Kit
with a suitable V250 image, Linux memory and UIO setup, and SSH access.
Building a new fabric image does not program the kit. Programming is a
separate step.

## Dependency licences

The pins and licence entries below come from `deps.lock`.

| Dependency | Pin | Licence |
|---|---|---|
| `jasonphillip/tychon-quantum-sensing` | `646d575` | Apache-2.0 |
| `polarfire-soc/icicle-kit-reference-design` | `v2026.04` | MIT |
| `Microchip-Vectorblox/VectorBlox-SDK` | `4186f9a` (`release-v2.0.3`) | No licence file; treated as all rights reserved |

The kit fetches the SDK into a user's checkout. It never redistributes SDK
files. Users obtain the SDK themselves under its applicable terms.
