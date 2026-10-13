# Kit identity before the kit-built image (2026-10-13)

Read-only checks, taken before any programming. Host names and home paths are replaced: `<kit>`, `<tools-host-home>`.

## Kit (over SSH)

- Board: `Microchip PolarFire-SoC Icicle Kit` (`/proc/device-tree/model`).
- OS: `Microchip Distro 1.0`; kernel image `fitImage-6.18.17-linux4microchip-2026.04.1-g7fbe4f69684d`; root on `/dev/mmcblk0p3`, command line includes `uio_pdrv_genirq.of_id=generic-uio`.
- Uptime at the check: 2 h 23 min, load 0.00.
- Fabric overlay: a boot service applies the case study's seed7 device-tree overlay (`seed7_vbx_pid.dtbo`, two-slot VectorBlox plus a passive PID node).
- `generic-uio` nodes and their map addresses:

| uio name | map0 address |
|---|---|
| `fpga_lsram` | `0x60000000` |
| `dma-controller@60010000` | `0x60010000` |
| `vbx@60030000` | `0x60030000` |
| `pid@60001000` | `0x60001000` |

- DMA buffers: `/dev/udmabuf-ddr-c0`, `/dev/udmabuf-ddr-nc-wcb0`, `/dev/udmabuf-ddr-nc0`.

## Address check for the kit-built design

The kit-built design's FIC0 initiator (reference `script_support/additional_configurations/Vectorblox/FIC0_INITIATOR_VBX.tcl`, `NUM_SLAVES:3`) has three targets: `0x60000000`-`0x60000fff`, `0x60001000`-`0x60001fff`, `0x60030000`-`0x60030fff`. The SDK's own overlay (`deps/vectorblox-sdk/example/soc-c/dts/mpfs_vbx.dtso:17-19`) places `vbx` at `0x60030000`. So the existing overlay's `vbx@60030000` node addresses the kit-built core's control page. The overlay's passive `pid@60001000` node will address a different block in the kit-built design (`docs/hardware.md` names `0x60001000` as the DMA controller page); the runner opens only the `vbx` node and never maps the others.

## Programmer and chain (FlashPro Express 2025.2.0.14, on the tools host)

- Programmer: Embedded FlashPro6, found.
- `scan_chain_prg`: 8 instruction-register bits; Device 1 IDCODE `1F81A1CF`, Microsemi `MPFS250(T|TS|TL|TLS|TC)`; "Scan and Check Chain PASSED".
- `read_idcode` is not a FlashPro Express 2025.2 command; `scan_chain_prg` needs `-name <programmer>`.
- The scan used a job project built from the rollback job; it ran no programming action.

## Programming jobs (on the tools host, verified by size and sha256)

| role | path | bytes | sha256 |
|---|---|---|---|
| new: kit-built Vectorblox | `<tools-host-home>/pfkit-build/reports/Vectorblox_FD0AEBB95776A726D3D.job` | 12,127,080 | `6d5cae6c30053ed5d16325f9cc03e57eb706e6ab3f3f9306d741cad02d711c6c` |
| rollback: case-study seed7 V250 | `<tools-host-home>/libero_seedsweep/seed7_vbx201_v250/export/polarfire_hybrid_control_two_slot_idfix2.job` | 12,126,891 | `39c8bcf2665ce8b79bcc2abb552ddd2b7b703729d50876744c2cb63c82ca230b` |

The new job's core: CoreVectorBlox 2.0.1, PRESET 0 (V250), timing met (`evidence/2026-10-12-libero-build/README.md`, lines 6-8, from `core_vectorblox_C0.cxf`). The build's `libero.log` names neither the core version nor the preset; it names no other preset.

No V500 rollback exists; the rollback job is the seed7 V250 job.

## Programming scripts (on the tools host, not in this repository)

| script | job | guard | guard test |
|---|---|---|---|
| `program_vectorblox_kitbuilt.tcl` | kit-built Vectorblox | path must contain `Vectorblox_FD0AEBB95776A726D3D` | a copy pointed at `wrong.job` printed `FATAL: refusing to program a job that is not the kit-built Vectorblox job`, no `JOB_PATH_VERIFIED`, exit 1 |
| `program_rollback_seed7.tcl` | seed7 V250 | path must contain `two_slot_idfix2` | the same test printed `FATAL: refusing to program a job that is not the rollback seed7 job`, exit 1 |

Both scripts run the PROGRAM action only (operator mode; eMMC, sNVM, HSS, U-Boot and the Linux image are not touched). Each guard runs before any device access. FlashPro Express maps the script's exit 90 to process exit 1; the `FATAL` line is the check.
