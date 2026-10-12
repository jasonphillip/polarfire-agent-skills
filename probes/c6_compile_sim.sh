#!/usr/bin/env bash
# Run on the x86 tools host in a Python 3.10 SDK venv.
set -u
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
out_dir="${script_dir}/out"
for name in per_channel per_tensor; do
    input="${out_dir}/c6_${name}.tflite"
    output="${out_dir}/c6_${name}.vnnx"
    log="${out_dir}/c6_${name}.compile.log"
    if [[ ! -f "${input}" || ! -f "${out_dir}/c6_input.npy" ]]; then
        printf '%s: input files absent\n' "${name}"
        continue
    fi
    vnnx_compile -c V250 -t "${input}" -o "${output}" >"${log}" 2>&1
    rc=$?
    printf '%s: compile_exit=%s; vnnx=%s\n' "${name}" "${rc}" "$([[ -f "${output}" ]] && printf yes || printf no)"
    tail -n 20 "${log}"
    if [[ ${rc} -ne 0 || ! -f "${output}" ]]; then continue; fi
    python - "${input}" "${output}" "${out_dir}/c6_input.npy" <<'PY'
import sys
import numpy as np
import tensorflow as tf
from vbx.sim import Model

tflite_path, vnnx_path, sample_path = sys.argv[1:]
interp = tf.lite.Interpreter(model_path=tflite_path)
interp.allocate_tensors()
detail = interp.get_input_details()[0]
sample = np.load(sample_path)
scale, zero = detail['quantization']
q = np.clip(np.rint(sample / scale + zero), -128, 127).astype(np.int8)
interp.set_tensor(detail['index'], q)
interp.invoke()
reference = interp.get_tensor(interp.get_output_details()[0]['index'])
sim = Model(open(vnnx_path, 'rb').read())
if sim.num_inputs != 1 or sim.num_outputs != 1:
    raise RuntimeError('expected one input and one output')
# SDK's lite_flow transposes NHWC inputs to NCHW for VNNX.
sim_input = q.transpose(0, 3, 1, 2).copy().ravel()
actual = np.asarray(sim.run([sim_input])[0]).reshape(sim.output_shape[0])
if actual.ndim == 4:
    actual = actual.transpose(0, 2, 3, 1)
if actual.shape != reference.shape:
    raise RuntimeError(f'output shape mismatch: VNNX {actual.shape}, TFLite {reference.shape}')
print(f'max_raw_int8_difference={int(np.abs(actual.astype(np.int16) - reference.astype(np.int16)).max())}')
print(f'tflite_raw={reference.ravel().tolist()}')
print(f'vnnx_raw={actual.ravel().tolist()}')
PY
    sim_rc=$?
    printf '%s: simulator_exit=%s\n' "${name}" "${sim_rc}"
done
