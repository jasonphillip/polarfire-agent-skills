#!/usr/bin/env python3
"""Export isolated INT8 PACK, STRIDED_SLICE, and dynamic-batch SHAPE cases."""
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np
import tensorflow as tf

OUT = Path(__file__).resolve().parent / "out"


def export(name, input_layer, output_layer, sample):
    model = tf.keras.Model(input_layer, output_layer)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: ([sample] for _ in range(12))
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    data = converter.convert()
    path = OUT / f"c2_{name}.tflite"
    path.write_bytes(data)
    interpreter = tf.lite.Interpreter(model_content=data)
    interpreter.allocate_tensors()
    ops = sorted({item["op_name"] for item in interpreter._get_ops_details() if item["op_name"] != "DELEGATE"})
    print(f"{path.relative_to(OUT.parent.parent)}: ops={','.join(ops)}")
    if name.upper() not in ops:
        raise RuntimeError(f"{name} did not survive TFLite conversion")


def main():
    tf.random.set_seed(12)
    OUT.mkdir(exist_ok=True)
    sample = np.array([[0.2, -0.4, 0.6, -0.8, 1.0, -1.2]], np.float32)

    x = tf.keras.Input(batch_shape=(1, 6), name="pack_input")
    y = tf.keras.layers.Lambda(lambda t: tf.stack([t, t + 0.125], axis=1), name="pack")(x)
    export("pack", x, y, sample)

    x = tf.keras.Input(batch_shape=(1, 6), name="slice_input")
    y = tf.keras.layers.Lambda(lambda t: t[:, 1:6:2], name="slice")(x)
    export("strided_slice", x, y, sample)

    # Dynamic batch forces a live SHAPE query. Feature width stays static.
    x = tf.keras.Input(shape=(6,), name="shape_input")
    y = tf.keras.layers.Lambda(
        lambda t: t + tf.cast(tf.shape(t)[0], tf.float32) * 0.125,
        name="shape",
    )(x)
    export("shape", x, y, sample)


if __name__ == "__main__":
    main()
