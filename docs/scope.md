# Scope

This document defines what the PolarFire Agent Skills kit supports. It also names what the kit does not support.
The kit takes a small model to a Microchip PolarFire SoC Icicle Kit (MPFS250T) with the CoreVectorBlox V250 soft NPU.
Every claim here comes from a run or a vendor statement dated 2026-10-12. Untested items carry the word "untested".

## 1. Supported target

The supported target is one board and one NPU size.

- Board: PolarFire SoC Icicle Kit with the MPFS250T device.
- NPU: CoreVectorBlox V250, built into the fabric by the reference design.
- Operating system: Linux on the microprocessor subsystem (MSS).
- Access path: Linux reaches the V250 through the `generic-uio` driver and the `udmabuf` driver.
- Control page: the V250 control page sits at `0x60030000`, exposed as the `generic-uio` node `vbx`.
- DMA buffer: the kit uses the device `/dev/udmabuf-ddr-nc0`.

Model deployment is the core path. The path runs from a trained model to an INT8 TFLite file, then to a compiled `.vnnx` file, then to inference on the kit.

PID and watchdog integration is a separate, optional example. Inference does not need it.
A user can skip that example and still complete the core path.

## 2. Tested profile and compatible range

The tools-host validation used VectorBlox SDK `release-v2.0.3` and targeted CoreVectorBlox IP 2.0.1.
The kit ran inference on one Icicle Kit on 2026-10-12 with the case study's image and overlay (see `docs/validation.md`); a bitstream from the kit's own build script is a separate item.

Microchip states that any 2.0.x core works with any 2.0.x SDK (VectorBlox SDK issue #27).
The kit treats 2.0.x as the vendor-stated compatible range.
The kit has not run any other 2.0.x pairing.

SDK 3.x is not supported by this kit.

## 3. Platform matrix

The kit separates three roles. Each role can run on a different machine.

| Role | What runs there | What must be installed |
|---|---|---|
| Orchestration host | The Python pipeline and the agent | Python 3.11, the kit venv, SSH client |
| Tools host | Compile, simulate, synthesize, cross-build | Libero SoC 2025.2, SmartHLS 2025.2, VectorBlox SDK 2.0.3 in a Python 3.10 venv |
| Kit (the board) | Linux, the V250, the inference runner | The Linux image with `generic-uio` and `udmabuf`, the V250 bitstream, SSH server |

### Orchestration host

- Linux aarch64 with Python 3.11 is supported.
- macOS arm64 with Python 3.11 is supported.
- x86 Linux is expected to work. It is untested.

### Tools host

- The tools host is an x86 machine.
- The orchestration host reaches the tools host over SSH.
- The kit never requires Microchip tools on the orchestration host.
- The tested tools host runs Libero SoC 2025.2 and SmartHLS 2025.2 on Windows.
- The VectorBlox SDK 2.0.3 runs in a Python 3.10 venv inside a Linux layer on that machine.
- That venv provides the `vnnx_compile` command and the `vbx.sim` simulator.

### Kit

- The orchestration host reaches the kit over SSH on the local network.
- The tested image is `mchp-base-image-mpfs-icicle-kit.rootfs-20260430113402.wic.gz`.
- CoreVectorBlox needs a free add-on Libero licence.

## 4. Python dependency decisions

The kit pins the orchestration environment as follows.

| Package | Decision | Reason |
|---|---|---|
| Python | 3.11 | One version that has wheels for both orchestration platforms. |
| `tensorflow` | 2.15.1 | Its TFLite converter matches the pin on the SDK host. It has Python 3.11 wheels for Linux aarch64 and macOS arm64. |
| `numpy` | below 2 | TensorFlow 2.15.1 does not combine with NumPy 2. |
| `torch` | `2.11.0` | The public benchmark trains with this version. The earlier `2.11.0+cpu` local tag failed on macOS because that tag is Linux-only. |

The public benchmark pins `numpy` 2.4.2. That pin does not combine with TensorFlow 2.15.1.
For this reason the kit uses its own venv and does not reuse the benchmark environment.

The SDK host pins `tensorflow-cpu` 2.15.1, `numpy` 1.23.5 and `onnx` 1.16.1 on x86.
The `tensorflow-cpu` package has no wheel for Linux aarch64 or macOS arm64 at 2.15.1. The kit therefore uses `tensorflow`.
The ODMR example also needs the case-study simulator, `simos`, and Tk.
With Homebrew Python 3.11 on macOS, install `python-tk@3.11` for ODMR; verified on 2026-10-12 (11 tests pass, ODMR runs through inspect).
The `signal-freq` example does not need them.

## 5. Adaptation targets (untested)

The items below are adaptation targets. The kit has not run any of them.
A user who wants one of them must expect to change the parts listed.

| Target | Examples | Status |
|---|---|---|
| Other PolarFire SoC boards | Discovery Kit, Video Kit | Untested |
| Other V sizes | V500, V1000 | Untested |
| Other reference designs | A user design with CoreVectorBlox | Untested |

The compiler accepts `-c V250`, `-c V500` and `-c V1000`. Acceptance of the flag is not a hardware result.
The kit has compiled only for V250.

An adapter would have to change these items:

- The device and the part number in the Libero build.
- The address map, including the V250 control page and the DMA region.
- The device tree, including the `generic-uio` node and the `udmabuf` node.
- The Linux image that carries those nodes.
- The compile flag for the V size.

None of these changes has been run.

## 6. Out of scope

The kit does not support these items.

- Other FPGA vendors.
- Arbitrary model architectures. The kit supports a bounded adapter set. The pipeline docs name the set.
- Training on real sensor data. The examples use generated data.
- SDK 3.x.

A model outside the adapter set is rejected with a clear message.

## 7. External dependencies pinned by the kit

| Dependency | Pin | Licence | Role |
|---|---|---|---|
| `jasonphillip/tychon-quantum-sensing` | `646d575` | Apache-2.0 | Case study and worked examples |
| `polarfire-soc/icicle-kit-reference-design` | tag `v2026.04` | MIT | Libero reference design for the kit. The `VECTORBLOX+MPFS250T` script argument adds the CNN. |
| `Microchip-Vectorblox/VectorBlox-SDK` | `release-v2.0.3` (`4186f9a`) | No licence file in the repository (GitHub reports none, checked 2026-10-12); treated as all rights reserved, so the kit fetches it and never redistributes its files | Compiler, simulator and operator table |

The reference design needs Libero SoC 2025.2.
The VectorBlox CNN sits on FIC0 for control and on FIC2 for data.
Before the kit publishes, someone must read the licence of the two dependencies marked above.
