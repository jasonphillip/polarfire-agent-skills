# Model adapters

`mlp` accepts a one-input, one-output Torch graph with Linear, ReLU, ReLU6 and Flatten layers.
It also accepts functional ReLU and a static flatten call. Torch fake quantization modules are omitted; the converter recalibrates them. A module such as `OdmrMLP` works through Torch FX tracing.
It exports each Linear layer as a 1x1 Conv2D by default. It copies each weight matrix exactly into a `(1,1,in,out)` kernel.
Use `--form fc` to export FULLY_CONNECTED operators for experiments.
The default follows the measured SDK 2.0.3 simulator result in `evidence/2026-10-12-toolshost/probe-c8-fc-chains.md`.

`conv2d_1k` accepts Conv2d layers with kernel `(1,k)`, ReLU or ReLU6, optional global AdaptiveAvgPool2d, optional Flatten, and optional Linear head.
Convolutions require one group, unit dilation and zero padding. A linear head needs explicit Flatten.
The adapter changes NCHW input to NHWC for Keras. It preserves Torch flatten order when a convolution precedes Flatten.

Each adapter copies weights into Keras and checks one sample against Torch before conversion.
A branch, extra tensor input, dynamic input shape or other module raises `UnsupportedModelError`.
The error names the offending node and lists supported layers. Conv1d and Sigmoid are rejected.

To add an adapter, extend `to_keras` with a restricted graph rule and weight transform.
Add a Torch and Keras output agreement test. Add an INT8 export and inspector test for the new operator set.
Check the result against the pinned SDK's `docs/OPS.md` before claiming SDK support.
The operator table comes from the pinned SDK. It is a filter, not proof that compilation succeeds.
