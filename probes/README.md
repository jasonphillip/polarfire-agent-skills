# Claim probes

Run commands from the kit root. Use its Python 3.11 `.venv` after `.venv/.ready` appears.
The scripts read the two pinned source trees in `deps/`. They write generated models only to `probes/out/`.

| Claim | This machine | Tools host |
|---|---|---|
| C1 guard shape | `.venv/bin/python probes/c1_guard_shape.py` | — |
| C2 static operator models | `.venv/bin/python probes/c2_static_pack_slice.py` | `bash probes/c2_compile.sh` |
| C3 layer types | `.venv/bin/python probes/c3_layer_types.py` | — |
| C4 guard versus SDK lists | `.venv/bin/python probes/c4_guard_vs_sdk.py` | — |
| C5 SDK and core versions | Read `docs/claims.md` | — |
| C6 filter scales | `.venv/bin/python probes/c6_per_channel.py` | `bash probes/c6_compile_sim.sh` |
| C7 QAT export | `.venv/bin/python probes/c7_qat_vs_ptq.py` | — |

For C2 and C6, transfer `probes/out/` with the scripts to an x86 Linux tools host.
Use a Python 3.10 venv with the SDK `vbx` package, NumPy 1.23.5, TensorFlow CPU 2.15.1, and `vnnx_compile` on `PATH`.
The compile scripts print each exit code and the last 20 log lines.
C6 then compares raw simulator INT8 output with the TFLite interpreter on one fixed input.
Copy the host output into `docs/claims.md` after the run.

The generated TFLite operator names are checked before compile.
The SDK tables list possible operators. They do not prove a given shape, graph, or target works.
