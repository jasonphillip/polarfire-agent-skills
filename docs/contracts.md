# Data and model contracts

Each example has `example.yaml` and `example.py`. The module exports `generate(splits, seed)` and `model()`.
The generator returns train, val and test pairs. Each pair contains float32 inputs and targets.
The saved NPZ uses keys such as `train_x` and `train_y`.
The manifest records each array's shape, dtype and units. It also records split sizes, seed, generator version, normalization and SHA-256.

The input contract fixes batch size 1 for export. It states shape, layout, dtype, units and preprocessing.
An MLP example still accepts a flat `(1,C)` vector in the data contract.
Its default TFLite input tensor is `(1,1,1,C)` in NHWC order.
The 1x1 spatial dimensions leave its byte order equal to the flat vector.
The simulator's NHWC-to-NCHW transpose is the identity on these bytes.
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
