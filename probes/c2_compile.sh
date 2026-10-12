#!/usr/bin/env bash
# Run on the x86 tools host in a Python 3.10 SDK venv.
set -u
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
out_dir="${script_dir}/out"
mkdir -p "${out_dir}"
for name in pack strided_slice shape; do
    input="${out_dir}/c2_${name}.tflite"
    output="${out_dir}/c2_${name}.vnnx"
    log="${out_dir}/c2_${name}.compile.log"
    if [[ ! -f "${input}" ]]; then
        printf '%s: input absent: %s\n' "${name}" "${input}"
        continue
    fi
    vnnx_compile -c V250 -t "${input}" -o "${output}" >"${log}" 2>&1
    rc=$?
    printf '%s: exit=%s; vnnx=%s\n' "${name}" "${rc}" "$([[ -f "${output}" ]] && printf yes || printf no)"
    tail -n 20 "${log}"
done
