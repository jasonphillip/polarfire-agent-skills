# Roll back the boot overlay to the case study's seed7 overlay

Saved here on 2026-10-13, before the switch to vbx_only: apply-vbx-overlay.sh, vbx-overlay.service,
seed7_vbx_pid.dtbo, seed7_vbx_pid.dtso (checksums in SHA256SUMS).

    cd /root/bringup/overlay-backup-2026-10-13 && sha256sum -c SHA256SUMS
    cp -p apply-vbx-overlay.sh /root/bringup/apply-vbx-overlay.sh
    cp -p seed7_vbx_pid.dtbo /root/bringup/seed7_vbx_pid.dtbo
    cp -p vbx-overlay.service /etc/systemd/system/vbx-overlay.service
    systemctl daemon-reload
    reboot

After the reboot: `ls /sys/kernel/config/device-tree/overlays/` shows only `seed7`, and
/sys/class/uio lists vbx@60030000 and pid@60001000.

The seed7 overlay's pid@60001000 node matches the case-study seed7 V250 fabric only. On the
kit-built Vectorblox fabric that page is the fabric DMA controller. Roll the overlay back only
together with the fabric rollback (program_rollback_seed7.tcl on the tools host), or leave the
PID tools unused.
