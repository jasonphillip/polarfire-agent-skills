# Data and model contracts

Each example has `example.yaml` and `example.py`. The module exports `generate(splits, seed)` and `model()`.
The generator returns train, val and test pairs. Each pair contains float32 inputs and targets.
The saved NPZ uses keys such as `train_x` and `train_y`.
The manifest records each array's shape, dtype and units. It also records split sizes, seed, generator version, normalization and SHA-256.

The input contract fixes batch size 1 for export. It states shape, layout, dtype, units and preprocessing.
An MLP example still accepts a flat `(1,C)` vector in the data contract.
Its default TFLite input tensor is `(1,1,1,C)` in NHWC order.
The 1x1 spatial dimensions leave its byte order equal to the flat vector.
The simulator accepts model-order input only; it does not transpose NHWC input.
The default TFLite output is flattened to `(1,out)`.
ODMR uses 100 PL samples. It normalizes each spectrum to [0,1] by its own minimum and maximum.
The label is field magnitude in microtesla. Training divides that label by 50. Evaluation restores microtesla.
The signal example uses 64 noisy amplitude samples with no normalization. Its label is frequency in hertz.

The model contract names an adapter. Training stores a Torch state dictionary and a loss curve.
Export copies float weights to matching Keras layers. The TFLite converter quantizes those weights.
The converter regenerates all tensor scales and zero points. Calibration sets activation ranges; copied weights set weight ranges.
The export manifest records calibration indices and converter tensor quantization values.
For an MLP, it also records the export form, reason, and C8 probe path.
If Torch fake quantization observers exist, it records their scales and zero points beside converter values.
These observer values are comparison evidence; the converter does not reuse them.

`compare.json` reports three comparisons. Float against dequantized TFLite uses the example's absolute output tolerance.
TFLite against simulator uses a maximum raw INT8 LSB tolerance. Simulator against hardware requires exact raw equality by default.
`--lsb-tolerance` can relax the hardware comparison. A stage without supplied evidence says `not run`.
A failed tolerance returns a nonzero exit code.
Each comparison row has `status`, `pass`, and `exact` when it ran. `pass`
means its requested tolerance passed; `exact` means the measured difference
was zero. The top-level `status` is `no_evidence`, `incomplete`, `failed`,
`stale`, or `passed`. Its `pass` is true only when `status` is `passed`.
`complete` is true only when all three checks ran. A requested-check pass
without `complete` is not full deployment validation. `stale` and `failed`
are never passes. `attempt.json` identifies the active run, so old output
from another attempt cannot support a new pass.

## Quantized payload

`prepare_input` selects at least one dataset sample and writes `input.int8.npy`, `input.int8.bin`, and `input.manifest.json`.
The canonical payload is INT8 in model element order: flat `(K,C)` for MLP or NCHW `(K,C,H,W)` for `conv2d_1k`.
The manifest records sample count, shape, dtype, layout, split, selection method, indices, seed, scale, zero point, and three SHA-256 values.
`payload_sha256` hashes the C-order sample bytes. `npy_sha256` hashes the NumPy container. `bin_sha256` hashes `input.int8.bin`.
The simulator loads `input.int8.npy`; the kit receives `input.int8.bin`. Both paths use the bytes of `input.int8.bin`.
The payload hash appears in `sim.json` and `infer.json` for stages using this manifest, and in `compare.json` when comparison completes.
Whether this element order is correct for a `conv2d_1k` model on the kit has not been run on hardware; both hardware-validated examples are flat MLP inputs.
