# Hardware path: Icicle Kit and CoreVectorBlox

This path targets the MPFS250T Icicle Kit. The reference design uses FIC0 for control and FIC2 for data. Source: `deps/icicle-kit-reference-design/README.md:77-78`.

The tools host needs Libero SoC 2025.2, SmartHLS, the pinned reference design `v2026.04`, and a user supplied VectorBlox SDK `release-v2.0.3`. The case study used CoreVectorBlox `2.0.1` at `V250`. Sources: `deps/tychon-quantum-sensing/docs/model-to-v250.md:10-19`; `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/README.md:202-205`; `deps/icicle-kit-reference-design/README.md:77-78`.

Libero Silver and the free CoreVectorBlox add-on licence are required for this path. Check both on the tools host before a build. Source: `deps/tychon-quantum-sensing/docs/model-to-v250.md:10-19`; `deps/icicle-kit-reference-design/README.md:77`.

## Licence and source boundaries

- This kit is Apache-2.0. The case study is Apache-2.0. The overlay adapts `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/two_slot_vbx_pid.dtso`; that file's origin is named in the overlay header. Source: `deps/tychon-quantum-sensing/LICENSE:1-4`.
- NOTICE: `hw/Makefile` follows the Apache-2.0 case study's SmartHLS toolchain and SDK-by-path build pattern. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/Makefile:5-18,58-67`.
- The reference design is MIT. Its notice reads `Copyright 2019-2023 Microchip Corporation.` and `SPDX-License-Identifier: MIT`. The build script copies its intact checkout into `WORK_DIR`; keep its `LICENSE.md` there. Source: `deps/icicle-kit-reference-design/LICENSE.md:3-17`.
- The supplied SDK checkout has no licence grant. Treat it as all rights reserved. Obtain it yourself. `hw/Makefile` includes headers and compiles driver sources by path from `VBX_SDK`; this repo does not redistribute them. Source: inspected `deps/vectorblox-sdk/README.md`, `deps/vectorblox-sdk/drivers/vectorblox/`, and the SDK checkout root (one local inspection; licence status is supplied by the task brief).

## Build the fabric

The build copies `deps/icicle-kit-reference-design` into an empty `WORK_DIR`. It pins `core_vectorblox` in the copy. It runs the reference design headlessly with `VECTORBLOX+MPFS250T+VERIFY_TIMING+EXPORT_FPE:<reports>`. It collects the `.job`, timing, synthesis, and resource reports. The reference README documents the arguments and headless syntax: `deps/icicle-kit-reference-design/README.md:91-95,121-130`. The Tcl selects timing and export branches at `deps/icicle-kit-reference-design/MPFS_ICICLE_KIT_REFERENCE_DESIGN.tcl:431-499`.

```bash
export DEVICE=MPFS250T
export VBX_SIZE=V250
export CORE_VERSION=2.0.1
export WORK_DIR=/absolute/build-directory
export LIBERO=/absolute/path/to/libero
bash hw/build_reference_design.sh
```

Run this from a checkout of this kit. `WORK_DIR` must be absolute and absent. `LIBERO` may be an executable on `PATH`. `V500` and `V1000` are offered as untested options. Source for device and sizes: `deps/icicle-kit-reference-design/README.md:78`; `deps/vectorblox-sdk/drivers/vectorblox/vbx_cnn_api.h:33-39`.

**IP size verification gate:** The reference component has `M_AXI_DATA_WIDTH:128` and `PRESET:1`. Its VLNV ends in `:*`, so it does not pin an IP version. Source: `deps/icicle-kit-reference-design/script_support/additional_configurations/Vectorblox/components/core_vectorblox_C0.tcl:5-7`. The unpinned case study resolved to CoreVectorBlox `1.1.12` / V500. Its fix set `core_vectorblox_C0` to `2.0.1` / `PRESET:0` (V250) with 128-bit M_AXI. The generated `.cxf` confirmed the version and preset. It also changed `vectorblox_axi_resize` (COREAXI4INTERCONNECT `2.9.100`) from `ID_WIDTH:3` to `ID_WIDTH:4` to match the core. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/rung_f_v250_post_program_handoff_2026-06-16.md:21-33`. `hw/pin_vectorblox.tcl` applies both changes to a copied reference design and refuses an absent `ID_WIDTH:3` line. The V500 and V1000 preset mappings remain unconfirmed. Check the generated IP configuration in Libero before programming. The case study's separate `VSIZE:V250` setting is marked for verification in `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/libero/scripts/02_import_ip.tcl:129-145`.

The wrapper does not program a kit. The vendor Tcl may read a Git revision for its project label. It can use `UNKNOWN` when unavailable: `deps/icicle-kit-reference-design/MPFS_ICICLE_KIT_REFERENCE_DESIGN.tcl:103-114`. Its `-download_core` option can require an IP catalog download; cache the licensed IP before an offline build. Source: `deps/icicle-kit-reference-design/script_support/additional_configurations/Vectorblox/components/core_vectorblox_C0.tcl:5`. The wrapper does not fetch or copy VectorBlox SDK sources.

## Linux image and memory

The case study used `mchp-base-image-mpfs-icicle-kit.rootfs-20260430113402.wic.gz` from the `linux4microchip-2026.04` release. Microchip publishes Icicle Linux images in the `linux4microchip/meta-mchp` releases. Locate the exact named asset there; the release page was not checked in this offline task. Sources: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/README.md:25,104-112`; `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/vectorblox_deployment_reference_2026-06-02.md:33-34`.

```text
https://github.com/linux4microchip/meta-mchp/releases
```

Decompress the `.wic.gz` before writing the `.wic` to an SD card. Check the destination device. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/README.md:104-112`.

The image needs `generic-uio` for the control page and `/dev/udmabuf-ddr-nc0` for DMA model and IO buffers. The case study observed its non-cached pool at physical `0xc8000000`, size `0x02000000` bytes (32 MiB). That is a case-study observation, not a promise for another image. Sources: `deps/tychon-quantum-sensing/docs/model-to-v250.md:165-170`; `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/rung_f_decerr_handoff_2026-06-16.md:31-34`. If the image lacks the pool, reserve it in the **base** device tree at boot. A runtime overlay cannot reserve this memory. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/README.md:197-200`.

The control page is `0x60030000` through `0x60030fff`. The PID/watchdog page begins at `0x60040000`. The DMA controller page begins at `0x60001000`. The runner uses only the SDK mapped V250 control page; do not map or probe the other pages with it. Sources: `deps/icicle-kit-reference-design/script_support/additional_configurations/Vectorblox/FIC0_INITIATOR_VBX.tcl:1162-1165`; `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/two_slot_vbx_pid.dtso:20-45`.

## Device tree overlay

`hw/overlay/vbx_only.dtso` keeps the case study's `generic-uio` V250 node at `0x60030000` and interrupt `124`. It omits the PID node. The source is `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/two_slot_vbx_pid.dtso:9-45`. Apply it on the kit at every boot:

```bash
dtc -@ -O dtb -o vbx_only.dtbo vbx_only.dtso -Wno-reg_format -Wno-avoid_default_addr_size
mkdir -p /sys/kernel/config/device-tree/overlays/vbx_only
cat vbx_only.dtbo > /sys/kernel/config/device-tree/overlays/vbx_only/dtbo
cat /sys/class/uio/uio*/name
ls /dev/udmabuf-ddr-nc0
```

Run `dtc` from the directory containing `vbx_only.dtso`. Check that one UIO name is exactly `vbx`. The SDK `release-v2.0.3` driver searches that literal name in `deps/vectorblox-sdk/drivers/vectorblox/vbx_cnn_api.c:75-107`. The overlay is not proof that the fabric contains the correct core.

## Runner

Build on the tools host with the SmartHLS glibc RISC-V toolchain. Its Cygwin runtime directory must be on `PATH`. These lines follow `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/Makefile:5-18,58-67`.

```bash
export SHLS=/absolute/path/to/SmartHLS
export KIT_ROOT=/absolute/path/to/polarfire-agent-skills
export VBX_SDK=/absolute/path/to/VectorBlox-SDK
export PATH="$SHLS/swtools/binutils/riscv-gnu-toolchain/bin:$SHLS/dependencies/lib/cygwin:$PATH"
riscv64-unknown-linux-gnu-gcc -O2 -std=c11 -Wall -Wextra \
  -DVBX_SOC_DRIVER -DMSS_DDR -DUSE_INTERRUPTS=0 \
  -I"$VBX_SDK/drivers/vectorblox" \
  "$KIT_ROOT/hw/vbx_run.c" \
  "$VBX_SDK/drivers/vectorblox/vbx_cnn_api.c" \
  "$VBX_SDK/drivers/vectorblox/vbx_cnn_model.c" \
  -o "$KIT_ROOT/hw/vbx_run" -lm -lpthread
```

The tools host's MSYS shell did not have `make` on `PATH`.
The direct GCC command above follows `hw/Makefile` and was used for the measured cross-build.
Alternatively, add SmartHLS `dependencies/mingw64/bin` to `PATH` and run
`mingw32-make -C "$KIT_ROOT/hw" CROSS=riscv64-unknown-linux-gnu- VBX_SDK="$VBX_SDK"`.

On the kit, `make -C hw native VBX_SDK=/absolute/path/to/VectorBlox-SDK` uses `gcc`. Supply the SDK checkout there if using this target. The output is `hw/vbx_run` for the cross build and `hw/vbx_run.native` for the native build.

```bash
hw/vbx_run --model m.vnnx --input in.bin --output out.bin --timeout-ms 1000 --json meta.json --uio-name vbx --repeat 10
```

The input file contains already quantized bytes in model input order. The runner accepts a V250 model with one input and one or more INT8 outputs. It checks the input byte count against the model descriptor. It writes concatenated raw INT8 outputs; `meta.json` gives each output's offset and size. It reports input and output counts, element counts, byte counts, dtypes, scales, zero points, the core version register word, SDK graph format version, control and error words, each wall time, and min/median/max. Descriptor APIs are in `deps/vectorblox-sdk/drivers/vectorblox/vbx_cnn_api.h:179-332`. The SDK graph format is in `deps/vectorblox-sdk/drivers/vectorblox/graph_version.h:1-5`. The core version word is word index `10`, as used in `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/vbx_probe.c:39-43`.

| Exit | Meaning |
|---|---|
| `0` | All requested runs completed; output and metadata written. |
| `2` | Invalid CLI, unsupported model IO, or input read or size error. A size mismatch prints actual and expected bytes. |
| `3` | UIO, udmabuf, model load, DMA, or output file failure. |
| `4` | Wall-clock poll timeout. Metadata retains the NPU control and error words. |
| `5` | NPU start, poll, or error-register failure. |

The SDK's `vbx_cnn_model_start` contains an internal wait for the START bit to clear (`deps/vectorblox-sdk/drivers/vectorblox/vbx_cnn_api.c:239-267`). The runner checks READY before calling it. A race or broken register could still stall inside that SDK call. The timeout bounds the poll loop, not a blocked SDK call.

## Evidence boundary

The case study ran a `2.0.1` V250 image on silicon and recorded `ERR=0`, version word `0x20000000`, and completed inference. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/README.md:202-205`. Its loaded model's start plus poll had median `32 µs` and p99 `33 µs`. Source: `deps/tychon-quantum-sensing/docs/model-to-v250.md:233-238`.

As of 2026-10-12, this kit's new build script has not run in Libero. Its generated `.job`, timing, and resource reports are unverified. The new overlay has not been applied to its new image. The runner cross-compiled with SmartHLS GCC 10.2.0; see `evidence/2026-10-12-toolshost/runner-build.txt`. It has not run on hardware. Its input mismatch, timeout, and multi-output paths have not been exercised on the kit. The case study confirms only `2.0.1` / `PRESET:0` as V250; V500 and V1000 mappings need confirmation. Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/rung_f_v250_post_program_handoff_2026-06-16.md:21-33`. These are limits of this kit, not results from the case study.
