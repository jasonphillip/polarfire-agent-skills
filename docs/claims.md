# Claims and probes

These findings use the pinned source snapshots under `deps/`.
Local commands run in the kit's Python 3.11 environment.
Compiler and simulator results remain pending until an x86 Linux tools host runs them.

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

Compile result: pending tools host.

**Corrected:** The SDK operator table lists `PACK` and `STRIDED_SLICE`.
It does not list `SHAPE`.
Source: `deps/vectorblox-sdk/docs/OPS.md:38,61`; `deps/vectorblox-sdk/python/vbx/vbx/generate/supported_ops.json`.
Compile outcomes for these small graphs are pending.

**Kit default:** Use a fixed batch and static spatial shapes for the provided exports.
Inspect the generated TFLite operators, then compile on the target SDK.
This keeps the known export path while isolated operator support is measured.

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
`OdmrMLP` contains `torch.nn.Linear` layers, which map to Dense during Keras export.
Source: `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/fcnn_v2.py:54-67`; `deps/tychon-quantum-sensing/workers/odmr-edge-ml/src/odmr_edge_ml/models/mlp.py:47-56`.

**Kit default:** Use the MLP for the Dense path and the FCNN for the Conv2D path.
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

Compile and simulator results: pending tools host.

**Corrected:** The SDK compiler source handles lists of filter and bias scales in a grouped convolution transform.
Source: `deps/vectorblox-sdk/python/vbx/vbx/generate/transform_tflite.py:1177-1210`.
That code makes the blanket per-tensor-only claim doubtful.
It does not establish per-channel success for this Conv2D graph.

**Kit default:** Export per-tensor weights until both variants compile and simulate on the tools host.
This preserves the existing cascade contract while the SDK capability is measured.

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
