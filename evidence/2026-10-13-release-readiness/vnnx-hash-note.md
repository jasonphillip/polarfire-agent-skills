# Why compiled model files differ while outputs are identical (2026-10-13)

## Question

Two compiles of the same example give `model.vnnx` files with different sha256 values. Is the compiler output non-deterministic in a way that matters?

## Measured facts

Three signal-freq runs, compiled separately (one on 2026-10-12, two on 2026-10-13), each with 64 samples:

| file | the three runs |
|---|---|
| `model.pt`, `model.tflite`, `dataset.npz` | identical sha256 |
| `sim.npz` (simulator outputs) | identical sha256 |
| `model.vnnx` (11,552 bytes) | three different sha256 values |
| `hw.bin` (kit outputs, same image) | identical sha256 (`f3e1261b53f12fd8...`); both 2026-10-13 runs `passed`, 64 samples, 0 LSB against the simulator |

Each pair of `model.vnnx` files differs in the same 35 bytes (0-based offsets):

- 12 bytes: the low four bytes of three 8-byte values at 2856, 2864 and 2872. Values in the three files: `0x1aa059e0`, `0x2aa53b70`, `0x327a6c30` at 2856, and the other two at the same fixed distances (`+0x2b0`, `+0x9f4`).
- 23 single bytes at 2887 2907 2923 2935 2955 3003 3035 3067 3083 3131 3195 3227 3243 3291 3355 3371 3419 3483 3515 4291 5003 5403 5527. Each is the top byte of a 32-bit little-endian word whose low 24 bits do not change (for example `0x0814ffdc`, `0xb814ffdc`, `0xe814ffdc`).

## Where the bytes sit

All 35 bytes lie in the graph's replay buffer (`vnnx_graph_t.replay_buffer`, `deps/vectorblox-sdk/drivers/vectorblox/vnnx-types.h:581-582`), which starts at offset 2848 in these files. The SDK's TFLite flow runs the model in its simulator (`vbx.sim.Model`) and copies the replay bytes from the simulator's model image into the file (`deps/vectorblox-sdk/python/vbx/vbx/generate/vnnx_tflite.py:1186-1196`, joined into the file at `:1222-1232`). Weights, node tables and tensor descriptors are identical.

The varying values behave like addresses in the compiling process's memory: the three 8-byte values move together with fixed spacing, and the 23 words keep their low 24 bits and change only the top byte. This reading is an inference from the byte pattern; the SDK source does not name these words. The kit's host driver does not parse the replay bytes (`vbx_cnn_model.c`); `vbx_cnn_api.c:240-267` passes the model address to the core. The source does not show whether the core reads the replay buffer; the identical `hw.bin` files show that, if it does, the differing bytes do not change the outputs.

## Conclusion

The compiler writes 35 run-dependent bytes into the replay buffer of each build; weights, graph structure, simulator outputs and kit outputs are identical.

Consequence: rebuilds are output-identical, not file-identical. Compare outputs and the payload hash, never the `.vnnx` hash.

Method: `cmp -l` on the three files; the offsets were mapped with the SDK's own structure layout; source lines read, not executed, for the driver statements.
