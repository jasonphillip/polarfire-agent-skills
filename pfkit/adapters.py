"""Restricted Torch graph to Keras transliteration."""
from __future__ import annotations

import numpy as np
import torch
from torch import nn
from torch.fx import Tracer, GraphModule
from torch.ao.quantization.fake_quantize import FakeQuantizeBase
from .errors import UnsupportedModelError

SUPPORTED = "Linear, ReLU, ReLU6, Flatten, Conv2d(kernel=(1,k)), AdaptiveAvgPool2d((1,1))"


def _fail(name, obj):
    raise UnsupportedModelError(f"Unsupported model node {name}: {obj}; supported: {SUPPORTED}")


def to_keras(model: nn.Module, input_shape: tuple[int, ...], adapter: str, form: str = "conv1x1"):
    """Return an equivalent fixed-batch Keras model for the restricted graph."""
    import tensorflow as tf
    if adapter not in ("mlp", "conv2d_1k"):
        _fail("adapter", adapter)
    if form not in ("conv1x1", "fc"):
        _fail("form", form)
    class AdapterTracer(Tracer):
        def is_leaf_module(self, module, qualified_name):
            if isinstance(module, (nn.Linear, nn.Conv2d, FakeQuantizeBase)):
                return True
            return super().is_leaf_module(module, qualified_name)
    graph = GraphModule(model, AdapterTracer().trace(model.eval()))
    nodes = list(graph.graph.nodes)
    if sum(n.op == "placeholder" for n in nodes) != 1 or sum(n.op == "output" for n in nodes) != 1:
        _fail("graph", "expected one input and one output")
    if input_shape[0] != 1 or any(int(x) <= 0 for x in input_shape):
        _fail("input", f"fixed batch 1 and positive static dimensions required: {input_shape}")
    conv = adapter == "conv2d_1k"
    if conv and len(input_shape) != 4:
        _fail("input", input_shape)
    if not conv and len(input_shape) < 2:
        _fail("input", input_shape)
    if conv:
        inputs = tf.keras.Input(batch_size=1, shape=(input_shape[2], input_shape[3], input_shape[1]))
    elif form == "conv1x1":
        inputs = tf.keras.Input(batch_size=1, shape=(1, 1, int(np.prod(input_shape[1:]))))
    else:
        inputs = tf.keras.Input(batch_size=1, shape=input_shape[1:])
    x = inputs
    current = None
    seen_linear = False
    for node in nodes:
        if node.op == "placeholder":
            current = node
            continue
        if node.op == "output":
            if node.args[0] is not current:
                _fail(node.name, "nonlinear output graph")
            continue
        if len(node.all_input_nodes) != 1 or node.all_input_nodes[0] is not current:
            _fail(node.name, "branches or extra tensor inputs")
        current = node
        if node.op == "call_module":
            module = graph.get_submodule(node.target)
            if isinstance(module, FakeQuantizeBase):
                pass  # Converter recalibrates after Torch fake quantization is removed.
            elif isinstance(module, nn.Linear):
                if conv and not seen_linear and len(x.shape) > 2:
                    _fail(node.target, "Linear needs explicit Flatten")
                if not conv and form == "conv1x1":
                    layer = tf.keras.layers.Conv2D(module.out_features, (1, 1), use_bias=module.bias is not None)
                    weights = [module.weight.detach().numpy().T.reshape(1, 1, module.in_features, module.out_features)]
                else:
                    layer = tf.keras.layers.Dense(module.out_features, use_bias=module.bias is not None)
                    weights = [module.weight.detach().numpy().T]
                x = layer(x)
                if module.bias is not None:
                    weights.append(module.bias.detach().numpy())
                layer.set_weights(weights)
                seen_linear = True
            elif isinstance(module, (nn.ReLU, nn.ReLU6)):
                x = tf.keras.layers.ReLU(max_value=6.0 if isinstance(module, nn.ReLU6) else None)(x)
            elif isinstance(module, nn.Flatten):
                if module.start_dim != 1 or module.end_dim != -1:
                    _fail(node.target, module)
                if not conv and form == "conv1x1":
                    continue
                if conv and len(x.shape) == 4:
                    x = tf.keras.layers.Permute((3, 1, 2))(x)
                x = tf.keras.layers.Flatten()(x)
            elif isinstance(module, nn.Conv2d) and conv:
                if module.kernel_size[0] != 1 or module.groups != 1 or module.dilation != (1, 1) or module.padding != (0, 0):
                    _fail(node.target, module)
                layer = tf.keras.layers.Conv2D(module.out_channels, module.kernel_size, strides=module.stride,
                    padding="valid", use_bias=module.bias is not None)
                x = layer(x)
                weights = [module.weight.detach().numpy().transpose(2, 3, 1, 0)]
                if module.bias is not None:
                    weights.append(module.bias.detach().numpy())
                layer.set_weights(weights)
            elif isinstance(module, nn.AdaptiveAvgPool2d) and conv and module.output_size in (1, (1, 1)):
                x = tf.keras.layers.GlobalAveragePooling2D(keepdims=True)(x)
            else:
                _fail(node.target, type(module).__name__)
        elif node.op == "call_method" and node.target == "flatten" and node.args[1:] in ((1,), (1, -1)):
            if not conv and form == "conv1x1":
                continue
            if conv and len(x.shape) == 4:
                x = tf.keras.layers.Permute((3, 1, 2))(x)
            x = tf.keras.layers.Flatten()(x)
        elif node.op == "call_function" and node.target in (torch.relu, torch.nn.functional.relu):
            x = tf.keras.layers.ReLU()(x)
        elif node.op == "call_function" and node.target == torch.flatten and node.args[1:] in ((1,), (1, -1)):
            if not conv and form == "conv1x1":
                continue
            if conv and len(x.shape) == 4:
                x = tf.keras.layers.Permute((3, 1, 2))(x)
            x = tf.keras.layers.Flatten()(x)
        else:
            _fail(node.name, f"{node.op} {node.target}")
    if conv and len(x.shape) == 4:
        x = tf.keras.layers.Permute((3, 1, 2))(x)
    if not conv and form == "conv1x1":
        x = tf.keras.layers.Flatten()(x)
    if not conv and len(input_shape) != 2:
        _fail("input", f"flat vector required: {input_shape}")
    return tf.keras.Model(inputs, x)


def verify_transliteration(model, keras_model, sample, adapter, atol=1e-5):
    fake_quants = [m for m in model.modules() if isinstance(m, FakeQuantizeBase)]
    original = [m.fake_quant_enabled.clone() for m in fake_quants]
    try:
        for module in fake_quants:
            module.disable_fake_quant()
        with torch.no_grad():
            expected = model.eval()(torch.from_numpy(np.asarray(sample, dtype=np.float32))).numpy()
    finally:
        for module, state in zip(fake_quants, original):
            module.fake_quant_enabled.copy_(state)
    actual_input = np.asarray(sample, dtype=np.float32)
    if adapter == "conv2d_1k":
        actual_input = actual_input.transpose(0, 2, 3, 1)
    elif adapter == "mlp" and len(keras_model.input_shape) == 4:
        actual_input = actual_input.reshape(1, 1, 1, -1)
    actual = keras_model(actual_input, training=False).numpy()
    if expected.shape != actual.shape or not np.allclose(expected, actual, atol=atol, rtol=atol):
        raise ValueError(f"Torch/Keras mismatch: {expected.shape}, {actual.shape}, max delta {np.max(np.abs(expected-actual))}")
