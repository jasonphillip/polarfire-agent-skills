"""Run one-input VectorBlox models using only SDK venv packages (Python 3.10)."""
from __future__ import annotations
import argparse
import numpy as np
import vbx.sim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.model, "rb") as stream:
        model = vbx.sim.Model(stream.read())
    if model.num_inputs != 1 or model.num_outputs != 1:
        raise ValueError("This runner accepts one input and one output")
    samples = np.load(args.input)
    shape = tuple(model.input_shape[0])
    if samples.shape == shape:
        samples = [samples]
    elif samples.ndim > 1 and samples.shape[1:] == shape:
        samples = list(samples)
    elif samples.ndim == 1 and samples.size == np.prod(shape):
        samples = [samples]
    elif samples.ndim == 2 and samples.shape[1] == np.prod(shape):
        samples = list(samples)
    elif len(shape) == 4 and samples.ndim == 3 and samples.transpose(2, 0, 1).shape == shape[1:]:
        samples = [samples]
    elif len(shape) == 4 and samples.ndim == 4 and samples.transpose(0, 3, 1, 2).shape[1:] == shape[1:]:
        samples = list(samples)
    else:
        raise ValueError("Input shape does not match model input shape")
    outputs = []
    for sample in samples:
        if sample.dtype != model.input_dtypes[0]:
            raise ValueError("Input dtype does not match model input dtype")
        if sample.ndim == 3 and len(shape) == 4:
            sample = sample.transpose(2, 0, 1)
        outputs.append(np.asarray(model.run([np.ascontiguousarray(sample).ravel()])[0]).ravel())
    np.savez_compressed(args.output, outputs=np.asarray(outputs),
        input_scale=np.asarray(model.input_scale_factor), input_zero_point=np.asarray(model.input_zeropoint),
        output_scale=np.asarray(model.output_scale_factor), output_zero_point=np.asarray(model.output_zeropoint))


if __name__ == "__main__":
    main()
