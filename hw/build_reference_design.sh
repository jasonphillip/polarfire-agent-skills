#!/usr/bin/env bash
# Build in a copy of the pinned v2026.04 reference design. No SDK files are copied.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_dir=$(cd "$script_dir/.." && pwd)
source_dir="$repo_dir/deps/icicle-kit-reference-design"
DEVICE=${DEVICE:-MPFS250T}
VBX_SIZE=${VBX_SIZE:-V250}
CORE_VERSION=${CORE_VERSION:-2.0.1}
WORK_DIR=${WORK_DIR:?set WORK_DIR to an empty build directory outside this repository}
LIBERO=${LIBERO:-libero}

case "$DEVICE" in MPFS250T) ;; *) echo "Unsupported DEVICE: $DEVICE" >&2; exit 2;; esac
case "$VBX_SIZE" in V250|V500|V1000) ;; *) echo "Unsupported VBX_SIZE: $VBX_SIZE" >&2; exit 2;; esac
[[ "$CORE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "invalid CORE_VERSION" >&2; exit 2; }
[[ "$WORK_DIR" = /* ]] || { echo "WORK_DIR must be absolute" >&2; exit 2; }
WORK_DIR=${WORK_DIR%/}
[[ -n "$WORK_DIR" ]] || { echo "WORK_DIR must not be filesystem root" >&2; exit 2; }
case "$WORK_DIR" in "$repo_dir"|"$repo_dir"/*) echo "WORK_DIR must be outside this repository" >&2; exit 2;; esac
command -v tclsh >/dev/null || { echo "tclsh required" >&2; exit 3; }
command -v "$LIBERO" >/dev/null || { echo "Libero executable unavailable: $LIBERO" >&2; exit 3; }
[[ -f "$source_dir/MPFS_ICICLE_KIT_REFERENCE_DESIGN.tcl" ]] || { echo "pinned reference design missing" >&2; exit 3; }
[[ ! -e "$WORK_DIR" ]] || { echo "WORK_DIR must not exist: $WORK_DIR" >&2; exit 2; }

mkdir -p "$WORK_DIR/reference" "$WORK_DIR/reports"
cp -a "$source_dir/." "$WORK_DIR/reference/"
component="$WORK_DIR/reference/script_support/additional_configurations/Vectorblox/components/core_vectorblox_C0.tcl"
tclsh "$script_dir/pin_vectorblox.tcl" "$component" "$CORE_VERSION" "$VBX_SIZE"

# The reference README names VERIFY_TIMING and EXPORT_FPE:PATH. Both are needed:
# VERIFY_TIMING runs timing; EXPORT_FPE emits a programming job without PROGRAM.
# The reference Tcl may invoke git for a project label; no git is run by this wrapper.
(
    cd "$WORK_DIR/reference"
    "$LIBERO" "SCRIPT:MPFS_ICICLE_KIT_REFERENCE_DESIGN.tcl" \
        "SCRIPT_ARGS:VECTORBLOX+${DEVICE}+VERIFY_TIMING+EXPORT_FPE:${WORK_DIR}/reports" \
        "LOGFILE:${WORK_DIR}/reports/libero.log"
)

# Keep the native reports and job together. Report names vary by Libero release.
while IFS= read -r -d '' report; do
    rel=${report#"$WORK_DIR/reference/"}
    dest="$WORK_DIR/reports/$rel"
    mkdir -p "$(dirname "$dest")"
    cp -p "$report" "$dest"
done < <(find "$WORK_DIR/reference" -type f \
    \( -iname '*.rpt' -o -iname '*.xml' -o -iname '*.job' \) -print0)

if ! find "$WORK_DIR/reports" -type f -name '*.job' -print -quit | grep -q .; then
    echo "No .job found in reports; inspect Libero log" >&2
    exit 4
fi
echo "Build reports: $WORK_DIR/reports"
