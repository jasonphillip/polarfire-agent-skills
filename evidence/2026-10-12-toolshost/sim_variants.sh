#!/bin/bash
cd "$(dirname "$0")"
for name in A_2d B_4d_dense C_4d_reshape; do
  vnnx_compile -c V250 -t $name.tflite -o $name.vnnx > $name.compile.log 2>&1; echo "$name compile_exit=$? $(tail -1 $name.compile.log | cut -c1-100)"
  [ -f $name.vnnx ] || continue
  python - $name <<'PY'
import sys, numpy as np
from vbx.sim import Model
name=sys.argv[1]; m=Model(open(f"{name}.vnnx","rb").read()); q=np.load(f"{name}.q.npy"); ref=np.load(f"{name}.tflite_out.npy")
print(name,"vnnx input_shape",m.input_shape,"dtypes",m.input_dtypes,"out shape",m.output_shape,"in scale/zp",m.input_scale_factor,m.input_zeropoint)
for mode in ("asis","nchw"):
    outs=[]
    for k in range(q.shape[0]):
        x=q[k]
        if mode=="nchw" and x.ndim==3: x=x.transpose(2,0,1)
        x=np.ascontiguousarray(x).ravel()
        if x.size!=int(np.prod(m.input_shape[0])): outs.append(None); continue
        outs.append(int(np.asarray(m.run([x])[0]).ravel()[0]))
    print(f"  {mode}: sim_raw={outs} tflite_raw={ref.tolist()} maxdiff={max(abs(a-b) for a,b in zip(outs,ref.tolist()) if a is not None) if any(o is not None for o in outs) else 'n/a'}")
PY
done
