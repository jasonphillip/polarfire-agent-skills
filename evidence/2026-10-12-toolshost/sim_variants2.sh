#!/bin/bash
cd "$(dirname "$0")"
for name in D_conv1x1 E_single_dense F_dense_relu; do
  vnnx_compile -c V250 -t $name.tflite -o $name.vnnx > $name.compile.log 2>&1; echo "$name compile_exit=$?"
  [ -f $name.vnnx ] || { tail -3 $name.compile.log; continue; }
  python - $name <<'PY'
import sys, numpy as np
from vbx.sim import Model
name=sys.argv[1]; m=Model(open(f"{name}.vnnx","rb").read()); q=np.load(f"{name}.q.npy"); ref=np.load(f"{name}.tflite_out.npy")
print(" ",name,"vnnx in",m.input_shape,"out",m.output_shape)
outs=[]
for k in range(q.shape[0]):
    x=q[k]; x=x.transpose(2,0,1) if x.ndim==3 else x
    outs.append(np.asarray(m.run([np.ascontiguousarray(x).ravel()])[0]).ravel().astype(int)[:ref.shape[1]].tolist())
print("   sim_raw(first vals)",[o[:3] for o in outs]); print("   tflite_raw(first vals)",[r[:3] for r in ref.astype(int).tolist()]); print("   maxdiff", int(np.max(np.abs(np.array(outs)-ref.astype(int)))))
PY
done
echo "== SDK own embedded-input check on A_2d"; vnnx_compile -c V250 -t A_2d.tflite -o A_i.vnnx -i A_2d.q.npy > A_i.compile.log 2>&1; echo "A_i compile_exit=$?"; tail -4 A_i.compile.log; python -m vbx.sim A_i.vnnx 2>&1 | tail -6
