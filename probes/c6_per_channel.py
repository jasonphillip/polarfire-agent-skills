#!/usr/bin/env python3
"""Export one Conv2D as per-channel and per-tensor weight INT8 TFLite."""
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np
import tensorflow as tf

OUT = Path(__file__).resolve().parent / "out"


def main():
    tf.random.set_seed(6)
    np.random.seed(6)
    OUT.mkdir(exist_ok=True)
    x = tf.keras.Input(batch_shape=(1, 1, 8, 1))
    y = tf.keras.layers.Conv2D(3, (1, 3), use_bias=True, padding="valid")(x)
    model = tf.keras.Model(x, y)
    weights = np.array([[[[0.1, 0.9, 4.0]], [[-0.2, -0.7, 2.0]], [[0.3, 0.5, -3.0]]]], np.float32)
    model.layers[-1].set_weights([weights, np.array([0.01, -0.02, 0.03], np.float32)])
    sample = np.array([[[[0.1], [-0.2], [0.3], [-0.4], [0.5], [-0.6], [0.7], [-0.8]]]], np.float32)
    np.save(OUT / "c6_input.npy", sample)
    probe_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    if not hasattr(probe_converter, "_experimental_disable_per_channel"):
        raise RuntimeError("TensorFlow converter lacks _experimental_disable_per_channel")
    print("per-tensor flag: _experimental_disable_per_channel")
    for name, disable in (("per_channel", False), ("per_tensor", True)):
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = lambda: ([sample * factor] for factor in (0.5, 1.0, 1.5, 2.0) for _ in range(4))
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        converter._experimental_disable_per_channel = disable
        data = converter.convert()
        path = OUT / f"c6_{name}.tflite"
        path.write_bytes(data)
        interp = tf.lite.Interpreter(model_content=data)
        interp.allocate_tensors()
        filters = [t for t in interp.get_tensor_details() if len(t["shape"]) == 4 and t["dtype"] == np.int8 and "Conv2D" in t["name"]]
        if len(filters) != 1:
            raise RuntimeError(f"{name}: expected one Conv2D weight tensor, got {len(filters)}")
        scales = filters[0]["quantization_parameters"]["scales"]
        print(f"{path.relative_to(OUT.parent.parent)}: filter_scales={len(scales)}; values={[round(float(s), 8) for s in scales]}")
        if len(scales) != (1 if disable else 3):
            raise RuntimeError(f"{name}: unexpected weight scale count")


if __name__ == "__main__":
    main()
