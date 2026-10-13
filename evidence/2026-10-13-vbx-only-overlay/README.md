# Kit-built image with the vbx_only boot overlay (2026-10-13)

This folder records one configuration change and the runs on it: the kit's boot overlay was switched from the case study's seed7 overlay to this repository's `hw/overlay/vbx_only.dtso`. The fabric is unchanged: the kit-built Vectorblox image (`image.json`; job sha256 `6d5cae6c30053ed5d16325f9cc03e57eb706e6ab3f3f9306d741cad02d711c6c`). Runs under the seed7 overlay on the same fabric stay in `evidence/2026-10-13-kit-built-image/`.

## What was preserved first

On the kit, in `/root/bringup/overlay-backup-2026-10-13/` (copies also taken off the kit and checked against `SHA256SUMS`):

| file | sha256 |
|---|---|
| `apply-vbx-overlay.sh` (seed7 version) | `70bffd5e09ab613516e4ff2fbbd9aab4f8f2eeb8e3c57165e25c2ab7681fc96b` |
| `vbx-overlay.service` (seed7 version) | `b9d2e1e463ccd78c70576e41a7cff6a5b6334b5fdb3108ff4b7e8d1886536988` |
| `seed7_vbx_pid.dtbo` | `fcd88ada9b9eb6bee45153149c26c220720f03dbc56127fabb03685d711a9004` |
| `seed7_vbx_pid.dtso` | `c9dde7f1f8977bc8451098ebea5ddf66e6e33066cf32b470de00da19949900f6` |

`ROLLBACK.md` in that folder (copy: `kit-files/ROLLBACK.md`) gives the restore commands. It warns that the seed7 overlay's PID node fits only the case-study fabric, so roll it back together with the fabric rollback. The original `seed7_vbx_pid.dtbo` also stays in `/root/bringup/`.

## What changed

| file on the kit | new sha256 | change |
|---|---|---|
| `/root/bringup/vbx_only.dtso` | `b245f6583c65e31eaf14e990f0b68b7c3eb840259bf15f2d13d552293fea8849` | copy of `hw/overlay/vbx_only.dtso` (identical hash) |
| `/root/bringup/vbx_only.dtbo` | `2e611390ac9e3822af36930eb45773dc3248464d169fca613be4e7c81d9c31bc` | built on the kit with `dtc -@ -O dtb -o vbx_only.dtbo vbx_only.dtso -Wno-reg_format -Wno-avoid_default_addr_size` (DTC 1.7.0); one node `vbx@60030000`, interrupt 124, `plic` fixup |
| `/root/bringup/apply-vbx-overlay.sh` | `b15628819a6ea3005624a374822aee6f8323caec16c282d8f47c9c34c3dfa958` | applies `vbx_only` only; refuses if any other overlay is already applied (`kit-files/apply-vbx-overlay.sh`) |
| `/etc/systemd/system/vbx-overlay.service` | `ec5520ba86f01af462875a89104eab18ef9cbcecdf24d4e20fa92864d2c3b562` | same unit name; condition is now `vbx_only.dtbo` (`kit-files/vbx-overlay.service`) |

The overlay was replaced, not stacked: the seed7 overlay was never removed at run time; the kit was rebooted, and at boot the service applied only `vbx_only`.

## Checks after the reboot (2026-10-13 17:30 UTC)

| check | result |
|---|---|
| reboot to SSH | about 40 s (reboot 17:29:52, SSH 17:30:32 UTC) |
| applied overlays | `vbx_only` only, status `applied` |
| `vbx-overlay.service` | active (exited), exit 0 |
| uio nodes | `uio0 fpga_lsram 0x60000000`, `uio1 dma-controller@60010000 0x60010000`, `uio2 vbx@60030000 0x60030000` (size 0x1000) |
| stale PID node | gone: no `pid@60001000` uio, no `pid` node in the live device tree |
| DMA buffers | `/dev/udmabuf-ddr-nc0` 32 MiB at `0xc8000000`; `/dev/udmabuf-ddr-c0` 32 MiB at `0x88000000`; `/dev/udmabuf-ddr-nc-wcb0` 32 MiB at `0xd8000000` |
| processes holding a uio or DMA-buffer device | none |

## Runs, 64 test samples each, `example run --until compare`

| example | overall | kit vs simulator | kit completed, NPU error | wall ms median / max | `hw.bin` vs 2026-10-12 batch | `hw.bin` vs seed7-overlay run on this fabric |
|---|---|---|---|---|---|---|
| `signal-freq` | passed | 0 LSB, exact | 64, 0 | 0.024 / 0.025 | identical | identical |
| `odmr-mlp` | passed | 0 LSB, exact | 64, 0 | 0.034 / 0.065 | identical | identical |

Kit repository commit `53c8a56`, clean; runner sha256 `663504a508164c472f8edfc0dc1164ac6dc58f7e0ac53910b95887fb4f31c771`. Wall times are a quiet-board sample, not a worst-case bound. `odmr-fcnn` was not rerun here; its status is unchanged (`evidence/2026-10-13-odmr-fcnn/`).
