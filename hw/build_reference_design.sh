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

# The reference design asks the IP catalog for ":*" (latest) versions of its DirectCore
# and SgCore blocks. A newer catalog can ship a core whose parameters no longer match
# the v2026.04 component scripts (seen with COREAXI4INTERCONNECT 3.0.130: parameter
# DWC_ADDR_FIFO_DEPTH_CEILING not found). PIN_VLNV pins named cores to the versions the
# case study built with; it is a comma-separated list of VENDOR:LIB:NAME=VERSION.
PIN_VLNV=${PIN_VLNV:-Actel:DirectCore:COREAXI4INTERCONNECT=2.9.100}
IFS=',' read -r -a pins <<< "$PIN_VLNV"
for pin in "${pins[@]}"; do
    [[ -n "$pin" ]] || continue
    vlnv=${pin%%=*}; ver=${pin#*=}
    [[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "bad PIN_VLNV entry: $pin" >&2; exit 2; }
    count=$(grep -rl "core_vlnv {${vlnv}:\*}" "$WORK_DIR/reference" | wc -l)
    grep -rl "core_vlnv {${vlnv}:\*}" "$WORK_DIR/reference" | xargs -r sed -i "s#core_vlnv {${vlnv}:\*}#core_vlnv {${vlnv}:${ver}}#g"
    echo "pinned ${vlnv} to ${ver} in ${count} file(s)"
done

# The reference README names VERIFY_TIMING and EXPORT_FPE:PATH. Both are needed:
# VERIFY_TIMING runs timing; EXPORT_FPE emits a programming job without PROGRAM.
# The reference Tcl may invoke git for a project label; no git is run by this wrapper.
# On an MSYS shell (Windows Libero) the Libero arguments need Windows-style paths.
libero_work="$WORK_DIR"
if command -v cygpath >/dev/null 2>&1; then libero_work=$(cygpath -m "$WORK_DIR"); fi
(
    cd "$WORK_DIR/reference"
    "$LIBERO" "SCRIPT:MPFS_ICICLE_KIT_REFERENCE_DESIGN.tcl" \
        "SCRIPT_ARGS:VECTORBLOX+${DEVICE}+VERIFY_TIMING+EXPORT_FPE:${libero_work}/reports" \
        "LOGFILE:${libero_work}/reports/libero.log"
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
