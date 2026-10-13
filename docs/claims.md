# Claims and probes

These findings use the pinned source snapshots under `deps/`.
Local commands run in the kit's Python 3.11 environment.
The C2, C6, and C8 compiler and simulator results below came from the tools host.
These probes bound the `mlp` and `conv2d_1k` adapters in `docs/adapters.md`.
On 2026-10-13, `odmr-fcnn` became the first `conv2d_1k` model to run on the
kit, on both the case-study and kit-built images. Hardware parity: kit =
simulator = INT8 TFLite, 0 LSB, on both images. Conversion accuracy: the
largest per-sample float-to-INT8 prediction difference was 29.8 µT against
the 5.0 µT tolerance. One of 64 samples exceeded it; the mean difference was
2.39 µT. This is not an error against ground truth. Overall result: failed.
See `evidence/2026-10-13-odmr-fcnn/README.md` and
`evidence/2026-10-13-kit-built-image/README.md`.
An inspect pass alone does not establish compiler acceptance or correct kit
output. Keep probe results separate from the later kit run.

## C1 — Guard input shape

**Original:** `check_model_ops(model, input_shape=(1, 100))` is the tutorial example.
Source: `deps/tychon-quantum-sensing/docs/model-to-v250.md:30-35`.

**Probe:** `.venv/bin/python probes/c1_guard_shape.py`.

**Result:** Command stdout:

```text
default FCNN (1, 100): compatible=True; allowed=['aten.conv2d', 'aten.flatten', 'aten.relu', 'aten.view']; disallowed=[]; unknown=[]
default FCNN (1, 200): export failed: RuntimeError: shape '[1, 1, 1, 100]' is invalid for input of size 200
two-channel FCNN (1, 100): export failed: RuntimeError: shape '[1, 2, 1, 100]' is invalid for input of size 100
two-channel FCNN (1, 200): compatible=True; allowed=['aten.conv2d', 'aten.flatten', 'aten.relu', 'aten.view']; disallowed=[]; unknown=[]
```

**Corrected:** The default `OdmrFCNN` takes 100 flat values.
The two-channel `OdmrFCNN(in_channels=2)` takes 200 flat values.
The model reshapes by `in_channels * input_dim`.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn.py:47-52,83-99`.

**Kit default:** Pass the selected model's actual flat input shape to the guard.
Use `(1, 200)` for the two-channel FCNN example.
This catches export errors before training.

## C2 — Dynamic shape operators

**Original:** The compiler rejects `SHAPE`, `STRIDED_SLICE`, and `PACK`.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn_v2.py:72-83`.

**Probes:** `.venv/bin/python probes/c2_static_pack_slice.py` and `bash probes/c2_compile.sh`.

**Result:** Local command stdout:

```text
probes/out/c2_pack.tflite: ops=ADD,PACK
probes/out/c2_strided_slice.tflite: ops=STRIDED_SLICE
probes/out/c2_shape.tflite: ops=ADD,CAST,MUL,QUANTIZE,SHAPE,STRIDED_SLICE
```

Tools-host output from `evidence/2026-10-12-toolshost/probes-c2-c6.log`:

```text
pack: exit=1; vnnx=no
    assert(check_pack(i_tensor['shape'], o_tensor['shape'], opts['axis'], node.PackOptions.axis, node.PackOptions.count))
AssertionError
strided_slice: exit=1; vnnx=no
    channel_matches = sn.tensor_array[0].shape[-3] == sn.tensor_array[-1].shape[-3]
IndexError: tuple index out of range
shape: exit=1; vnnx=no
Error unsupported ops:	 SHAPE at location 0 is not currently supported.
```

The `SHAPE` probe also reports `SHAPE` as unsupported.
It reports `STRIDED_SLICE` with an `INT32` input as unsupported.
It reports `QUANTIZE` with a `FLOAT32` input as unsupported.

**Corrected:** The SDK operator table lists `PACK` and `STRIDED_SLICE`.
It does not list `SHAPE`.
Source: `deps/vectorblox-sdk/docs/OPS.md:38,61`; `deps/vectorblox-sdk/python/vbx/vbx/generate/supported_ops.json`.
The tools-host `PACK` probe failed in `check_pack` with `AssertionError`.
The `STRIDED_SLICE` probe failed in `set_skip_channel_slice` with `IndexError`.
The `SHAPE` graph failed with the unsupported operators stated above.

**Kit default:** Use a fixed batch and static spatial shapes for the provided exports.
The kit bans `PACK` and `STRIDED_SLICE` by default despite their SDK table entries.
Inspect the generated TFLite operators, then compile on the target SDK.

## C3 — Compute layer types

**Original:** The FCNN is the Conv2d candidate; the MLP is the Dense candidate.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn.py:3-8`; `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/mlp.py:1-4`.

**Probe:** `.venv/bin/python probes/c3_layer_types.py`.

**Result:** Command stdout:

```text
OdmrFCNN: Conv2d
OdmrFCNNv2: Conv2d
OdmrMLP: Linear
```

**Corrected:** The two FCNN classes contain `torch.nn.Conv2d` compute layers.
`OdmrMLP` contains `torch.nn.Linear` layers.
The kit maps them to 1x1 Conv2D by default. `--form fc` maps them to Dense for experiments.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn_v2.py:54-67`; `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/mlp.py:47-56`.

**Kit default:** Use the MLP for the measured 1x1 Conv2D path and the FCNN for the convolution path.
Their architectures match those tests.

## C4 — Guard policy and SDK listing

**Original:** The guard's ban list expresses VectorBlox constraints.
Source: `deps/tychon-quantum-sensing/docs/model-to-v250.md:37-41`.

**Probe:** `.venv/bin/python probes/c4_guard_vs_sdk.py`.

**Result:** Command stdout:

```text
SDK OPS.md=64; supported_ops.json=74
OPS.md lists, guard bans: aten.gelu -> GELU, aten.max_pool2d -> MAX_POOL_2D, aten.mul -> MUL, aten.sigmoid -> LOGISTIC, aten.silu -> SILU, aten.softmax -> SOFTMAX, aten.tanh -> TANH, TFLite PACK, TFLite STRIDED_SLICE
guard allows, OPS.md omits: (none)
allowed ATen ops without direct mapping: aten.contiguous, aten.t
supported_ops.json lists, guard bans: aten.gelu -> GELU, aten.log_softmax -> LOG_SOFTMAX, aten.max_pool2d -> MAX_POOL_2D, aten.mul -> MUL, aten.sigmoid -> LOGISTIC, aten.silu -> SILU, aten.softmax -> SOFTMAX, aten.tanh -> TANH, TFLite PACK, TFLite STRIDED_SLICE
guard allows, supported_ops.json omits: (none)
allowed ATen ops without direct mapping: aten.contiguous, aten.t
A listed op is documentation evidence, not proof that every shape or graph compiles.
```

**Corrected:** The PyTorch guard, TFLite guard, and SDK table cover different stages.
Their operator lists differ.
One SDK listing cannot establish that every graph compiles or simulates correctly.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/validation/ops_guard.py:17-80`; `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/validation/tflite_ops.py:22`; `deps/vectorblox-sdk/docs/OPS.md:4-69`.

**Kit default:** Keep the current conservative guard for supplied models.
Use compile and simulator probes to qualify any broader operator claim.
The existing single-input measurements show why a table alone is insufficient.
Source: `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/vnnx_ops_support_probe_2026-07-02.md:44-53`.

## C5 — SDK and IP compatibility

**Original:** SDK 2.0.3 with CoreVectorBlox IP 2.0.1 is mandatory.
Source: `deps/tychon-quantum-sensing/docs/model-to-v250.md:16`; `deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/models/README.md:15-18`.

**Probe:** Vendor statement in Microchip-Vectorblox/VectorBlox-SDK issue #27.

**Result:** The task owner verified that the issue exists.
The stated vendor wording is: “Any 2.0.X core would be compatible with any 2.0.X SDK.”

```text
https://github.com/Microchip-Vectorblox/VectorBlox-SDK/issues/27
```

**Corrected:** SDK 2.0.3 with IP 2.0.1 is the tested profile.
The vendor states compatibility across 2.0.x versions.
This statement does not prove every combination on this kit.

**Kit default:** Pin SDK 2.0.3, IP 2.0.1, and `-c V250` for reproducibility.
Call other 2.0.x pairs vendor-stated compatible until measured.

## C6 — Weight quantization granularity

**Original:** The SDK 2.0.x is per-tensor only.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py:6-14`.

**Probes:** `.venv/bin/python probes/c6_per_channel.py` and `bash probes/c6_compile_sim.sh`.

**Result:** Local command stdout:

```text
per-tensor flag: _experimental_disable_per_channel
probes/out/c6_per_channel.tflite: filter_scales=3; values=[0.0023622, 0.00708661, 0.03149606]
probes/out/c6_per_tensor.tflite: filter_scales=1; values=[0.03149606]
```

Tools-host output from `evidence/2026-10-12-toolshost/probes-c2-c6.log`:

```text
per_channel: compile_exit=0; vnnx=yes
max_raw_int8_difference=0
per_channel: simulator_exit=0
per_tensor: compile_exit=0; vnnx=yes
max_raw_int8_difference=0
per_tensor: simulator_exit=0
```

**Corrected:** The SDK compiler source handles lists of filter and bias scales in a grouped convolution transform.
Source: `deps/vectorblox-sdk/python/vbx/vbx/generate/transform_tflite.py:1177-1210`.
Both measured Conv2D variants compiled and matched TFLite at 0 raw INT8 difference.

**Kit default:** Keep the converter's quantization setting for each adapter.
The inspector reports per-channel weights for information only.

## C7 — QAT parameters after weight-copy export

**Original:** QAT parameters survive export.
The export script describes copying trained Conv2D weights from a QAT checkpoint.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/scripts/fix_fcnn_export.py:57-75,106-116`.

**Probe:** `.venv/bin/python probes/c7_qat_vs_ptq.py`.

**Result:** Command stdout:

```text
weights_copied_exactly=True
QAT activation fake-quant modules=0
TFLite input scale,zero_point=([0.01098039], [18])
QAT weight scale=[0.0023624387104064226]; zero_point=[0]
TFLite weight scale,zero_point=([0.00237606], [0])
TFLite output scale,zero_point=([0.00209511], [-3])
```

**Corrected:** The export strips fake-quant and observer state.
It copies trained weight and bias tensors to Keras.
The TFLite converter generates activation and weight scales and zero points from the copied weights and representative calibration data.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/training/qat.py:92-121`; `deps/tychon-quantum-sensing/workers/odmr-edge-ml/scripts/fix_fcnn_export.py:67-73,106-116,149-167`.
QAT scale and zero-point tensors do not pass through this weight-copy path.
The tiny QAT graph inserted weight fake quantization, but no activation fake quantization.
This is an API behavior observed in this probe, not a general claim about all QAT graphs.

**Kit default:** Treat the export as weight transfer followed by TFLite post-training calibration.
Record calibration data and compare the final INT8 model against the trained model.

## C8 — Fused FULLY_CONNECTED chains

**Probe:** `evidence/2026-10-12-toolshost/probe-c8-fc-chains.md`.
The following result table is copied verbatim from that probe.

```
c8-results.log: A_2d vnnx input_shape [[1, 64]] dtypes [dtype('int8')] out shape [[1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log: B_4d_dense vnnx input_shape [[1, 64, 1, 1]] dtypes [dtype('int8')] out shape [[1, 1, 1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log: C_4d_reshape vnnx input_shape [[1, 64, 1, 1]] dtypes [dtype('int8')] out shape [[1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c9-results.log: D_conv1x1 compile_exit=0
c9-results.log:   D_conv1x1 vnnx in [[1, 64, 1, 1]] out [[1, 1, 1, 1]]
c9-results.log:    sim_raw(first vals) [[44], [7], [7], [-61]]
c9-results.log:    tflite_raw(first vals) [[44], [7], [7], [-61]]
c9-results.log:    maxdiff 0
c9-results.log: E_single_dense compile_exit=0
c9-results.log:   E_single_dense vnnx in [[1, 64]] out [[1, 1]]
c9-results.log:    sim_raw(first vals) [[-40], [-31], [-72], [-4]]
c9-results.log:    tflite_raw(first vals) [[-40], [-31], [-72], [-4]]
c9-results.log:    maxdiff 0
c9-results.log: F_dense_relu compile_exit=0
c9-results.log:   F_dense_relu vnnx in [[1, 64]] out [[1, 32]]
c9-results.log:    sim_raw(first vals) [[-128, -69, -77], [-128, -75, -128], [-128, -67, -45], [-128, -86, -123]]
c9-results.log:    tflite_raw(first vals) [[-128, -69, -77], [-128, -75, -128], [-128, -67, -45], [-128, -86, -123]]
c9-results.log:    maxdiff 0
c9-results.log: == SDK own embedded-input check on A_2d
c9-results.log: A_i compile_exit=0
c9-results.log: input array 0 doesn't match ([ 1 64] != (4, 64))
c9-results.log: DATA_BYTES = 0.01 MB
c9-results.log: ALLOCATE_BYTES = 0.01 MB
c9-results.log: DMA_BYTES = 73
c9-results.log: INSTR_CYCLES = 6
c9-results.log: CHECKSUM = 00000000
c10-results.log: G_fc_relu_fc compile_exit=0
c10-results.log:   G_fc_relu_fc vnnx in [[1, 64]] out [[1, 1]]
c10-results.log:    sim_raw(first vals) [[-128], [-128], [-128], [-128]]
c10-results.log:    tflite_raw(first vals) [[-8], [7], [-90], [-3]]
c10-results.log:    maxdiff 135
c10-results.log: H_fc_fc compile_exit=0
c10-results.log:   H_fc_fc vnnx in [[1, 64]] out [[1, 1]]
c10-results.log:    sim_raw(first vals) [[23], [0], [-68], [45]]
c10-results.log:    tflite_raw(first vals) [[23], [0], [-68], [45]]
c10-results.log:    maxdiff 0
```

A, B, C, and G returned a constant -128 from the SDK 2.0.3 simulator.
E, F, and H matched TFLite exactly. The three-layer Conv2D form D also matched exactly.
The case study ran the Conv2D form on hardware.

**Kit default:** Export MLP Linear layers as 1x1 Conv2D with a flat-vector data contract.
Use `--form fc` only for experiments. The inspector blocks a fused FC chain by default.
