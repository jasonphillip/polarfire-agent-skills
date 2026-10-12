#!/usr/bin/env python3
"""Compare learned QAT fake-quant parameters with a weight-copy TFLite export."""
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np
import tensorflow as tf
import torch
import torch.nn as nn

SRC = Path(__file__).resolve().parents[1] / "deps/tychon-quantum-sensing/workers/odmr-edge-ml/src"
sys.path.insert(0, str(SRC))
from odmr_edge_ml.training.qat import prepare_model_qat, extract_clean_state_dict


class Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 2)

    def forward(self, x):
        return self.fc(x)


def qparams(tensor):
    p = tensor["quantization_parameters"]
    return [round(float(s), 8) for s in p["scales"]], [int(z) for z in p["zero_points"]]


def main():
    torch.manual_seed(7)
    np.random.seed(7)
    sample = np.array([[0.2, -0.4, 0.6, -0.8]], np.float32)
    qat = prepare_model_qat(Tiny(), torch.from_numpy(sample))
    opt = torch.optim.SGD(qat.parameters(), lr=0.01)
    for _ in range(4):
        opt.zero_grad()
        loss = (qat(torch.from_numpy(sample)) ** 2).mean()
        loss.backward()
        opt.step()
    qat.eval()
    qat(torch.from_numpy(sample))
    fake = [(name, module) for name, module in qat.named_modules() if isinstance(module, torch.ao.quantization.FakeQuantize)]
    activation_fake = [(name, module) for name, module in fake if "weight_fake_quant" not in name]
    weight = next(module for name, module in fake if "weight_fake_quant" in name)
    clean = extract_clean_state_dict(qat)
    w = clean["fc.weight"].detach().numpy()
    b = clean["fc.bias"].detach().numpy()
    x = tf.keras.Input(batch_shape=(1, 4))
    y = tf.keras.layers.Dense(2)(x)
    model = tf.keras.Model(x, y)
    model.layers[-1].set_weights([w.T, b])
    copied = np.array_equal(model.layers[-1].get_weights()[0].T, w)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: ([sample * factor] for factor in (0.25, 0.5, 1.0, 2.0) for _ in range(4))
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    interp = tf.lite.Interpreter(model_content=converter.convert())
    interp.allocate_tensors()
    wt = next(item for item in interp.get_tensor_details() if item["dtype"] == np.int8 and tuple(item["shape"]) == (2, 4))
    print(f"weights_copied_exactly={copied}")
    print(f"QAT activation fake-quant modules={len(activation_fake)}")
    print(f"TFLite input scale,zero_point={qparams(interp.get_input_details()[0])}")
    print(f"QAT weight scale={weight.scale.detach().numpy().tolist()}; zero_point={weight.zero_point.detach().numpy().tolist()}")
    print(f"TFLite weight scale,zero_point={qparams(wt)}")
    print(f"TFLite output scale,zero_point={qparams(interp.get_output_details()[0])}")


if __name__ == "__main__":
    main()
