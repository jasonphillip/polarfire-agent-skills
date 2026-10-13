#!/bin/sh
# Apply the polarfire-agent-skills vbx_only overlay: one generic-uio node, vbx@60030000 (V250 control page).
# No PID node. Replaced the case study's seed7 overlay on 2026-10-13 (kit-built Vectorblox image).
# Exactly one overlay: refuses to stack on any overlay already applied.
# Rollback: /root/bringup/overlay-backup-2026-10-13/ROLLBACK.md
O=/sys/kernel/config/device-tree/overlays
grep -q configfs /proc/mounts 2>/dev/null || mount -t configfs none /sys/kernel/config
[ -d "$O/vbx_only" ] && exit 0
for d in "$O"/*; do
    if [ -d "$d" ]; then echo "apply-vbx-overlay: refusing, overlay already applied: $d" >&2; exit 1; fi
done
mkdir -p "$O/vbx_only"
cat /root/bringup/vbx_only.dtbo > "$O/vbx_only/dtbo"
grep -q applied "$O/vbx_only/status"
