# Boot checks after programming the kit-built image (2026-10-13)

- Programming: FlashPro Express 2025.2, PROGRAM action on `MPFS250T`, "Chain programming PASSED", elapsed 56 s, finished 2026-10-13 16:18:06 UTC (`program.log`). The log's fabric digest `C4307EA9…` and sNVM digest `49D5C5C9…` match the build record (`evidence/2026-10-12-libero-build/README.md`, line 8).
- The script's own lines printed before the job project opened (`==> kit-built Vectorblox PROGRAM`, `JOB_PATH_VERIFIED`) are not in the FlashPro log file; `STEP1_OK`, `STEP2_OK` and `PROGRAM_PASS` are. `STEP1_OK` follows the guard, so the guard passed.
- Reset: the JTAG PROGRAM action reset the SoC. A `reboot` sent over SSH 24 s after programming found the kit unreachable (connection timed out), so it was not delivered. The kit answered SSH at 16:18:37 UTC with uptime 0 min.

Checks at 16:18:38 UTC (kit `<kit>`):

| check | result |
|---|---|
| uptime | 0 min, load 0.28 |
| `generic-uio` names | `fpga_lsram`, `dma-controller@60010000`, `vbx@60030000`, `pid@60001000` |
| DMA buffers | `/dev/udmabuf-ddr-c0`, `/dev/udmabuf-ddr-nc-wcb0`, `/dev/udmabuf-ddr-nc0` |
| overlay boot service | active (the case-study seed7 overlay; its `vbx` node addresses the new core's control page, `identity-before.md`) |
| kernel command line | `earlycon root=/dev/mmcblk0p3 rootwait uio_pdrv_genirq.of_id=generic-uio` |
| dmesg | `mss-dma-uio 60010000.dma-controller: registered device as dma-controller@60010000` |

No power cycle was needed. No rollback was run.
