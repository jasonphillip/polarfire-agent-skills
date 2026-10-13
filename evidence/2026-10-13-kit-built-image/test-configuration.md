# Test configuration on the kit-built image (2026-10-13)

Every run in this folder used this configuration. Checks are read-only, taken after programming (16:20-16:24 UTC). Host names, addresses and home paths are replaced.

## Programmed image

| item | value |
|---|---|
| job | `Vectorblox_FD0AEBB95776A726D3D.job`, 12,127,080 bytes |
| job sha256 | `6d5cae6c30053ed5d16325f9cc03e57eb706e6ab3f3f9306d741cad02d711c6c` |
| fabric digest (programming log) | `C4307EA9E823359B5C5F551DEEEB11F6072ECF51ED2B4893FCD05F6711B1FB94`, equal to the build record |
| core | CoreVectorBlox 2.0.1, PRESET 0 (V250) |
| programmed | 2026-10-13 16:18:06 UTC, PROGRAM action only (`program.log`) |
| rollback job, not used | case-study seed7 V250, sha256 `39c8bcf2665ce8b79bcc2abb552ddd2b7b703729d50876744c2cb63c82ca230b` |

## Kit software and device tree

- OS `Microchip Distro 1.0`, kernel `6.18.17-linux4microchip-2026.04.1`, unchanged by programming.
- Active overlay: `seed7` (status `applied`), from `seed7_vbx_pid.dtbo` (sha256 `fcd88ada9b9eb6bee45153149c26c220720f03dbc56127fabb03685d711a9004`), applied at boot by the one custom unit, `vbx-overlay.service` (oneshot).

| uio | name | address | in the kit-built fabric |
|---|---|---|---|
| uio0 | `fpga_lsram` | `0x60000000` | base-image node |
| uio1 | `dma-controller@60010000` | `0x60010000` | base-image node |
| uio2 | `vbx@60030000` | `0x60030000` | VectorBlox control page: `FIC0_INITIATOR:AXI4mslave2` to `Vectorblox_ss_0:S_control` (reference `Vectorblox/Vectorblox.tcl:17`). The runner opens only this node. |
| uio3 | `pid@60001000` | `0x60001000` | **mismatch**: in the kit-built fabric this page is the fabric DMA controller's control interface (`FIC0_INITIATOR:AXI4mslave0` to `DMA_CONTROLLER:AXI4TargetCtrl_IF`, reference `components/FIC_0_PERIPHERALS.tcl:231`; range `0x60001000`-`0x60001fff`). The node is a leftover of the case study's PID slot. |

The overlay matches the new fabric for the node the tests use (`vbx`) and does not match it for `pid@60001000`. The repository's `hw/overlay/vbx_only.dtso` omits the PID node; it was not applied for these tests.

## Nothing touches the old PID node

| check | result |
|---|---|
| processes with a `/dev/uio*` or `/dev/udmabuf*` file open | none |
| processes with a uio mapping | none |
| custom systemd units | `vbx-overlay.service` only (applies the overlay; does not open the devices) |
| running services | system daemons only (journald, udevd, networkd, resolved, timesyncd, logind, dbus, avahi, rpcbind, crond, syslog, klogd, gettys, sshd) |
| timers | `systemd-tmpfiles-clean`, `logrotate` |
| cron and at | no root crontab; `/etc/crontab` has no jobs; `/etc/cron.d` and the periodic folders are empty; at queue empty |
| init scripts, login hooks | no `/etc/rc.local`, no `/etc/init.d`; no profile file names a PID, watchdog or bring-up tool |
| boot journal | no PID, watchdog or bring-up tool ran |
| listening sockets | SSH, rpcbind, local DNS only; no dashboard |
| SSH sessions since boot | 17, all from the machine that ran these tests |

The case study's PID and watchdog tools (`pid_poke`, `pid_ctl`, `v250_pid_loop`, `wd_observer`, `run_wd_fallback.sh` and others) remain in the root user's bring-up folder. They run only by hand. On this image they would address the DMA controller's registers through `uio3`; do not run them on the kit-built image.

## Hosts and tools

| item | value |
|---|---|
| kit repository | commit `473c5e2`, clean worktree (`attempt.json`) |
| runner `hw/vbx_run` | sha256 `663504a508164c472f8edfc0dc1164ac6dc58f7e0ac53910b95887fb4f31c771` (`infer.json`) |
| kit config | remote directory `/tmp/pfkit`; infer timeout 300 s |
| tools host config | WSL Ubuntu; `size_config` V250; the SDK virtual environment (Python 3.10.20, `vbx` package 2.0.0); simulator timeout 1800 s |
