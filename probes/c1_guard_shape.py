#!/usr/bin/env python3
"""Compare the guard example with the two-channel FCNN input contract."""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "deps/tychon-quantum-sensing/workers/odmr-edge-ml/src"
sys.path.insert(0, str(SRC))

from odmr_edge_ml.models.fcnn import OdmrFCNN
from odmr_edge_ml.validation.ops_guard import check_model_ops


def probe(label, model, shape):
    try:
        result = check_model_ops(model, input_shape=shape)
        print(f"{label} {shape}: compatible={result.is_compatible}; allowed={result.allowed}; disallowed={result.disallowed}; unknown={result.unknown}")
    except Exception as exc:
        print(f"{label} {shape}: export failed: {type(exc).__name__}: {str(exc).splitlines()[0]}")


if __name__ == "__main__":
    for label, model in (("default FCNN", OdmrFCNN()), ("two-channel FCNN", OdmrFCNN(in_channels=2))):
        for shape in ((1, 100), (1, 200)):
            probe(label, model, shape)
