#!/usr/bin/env python3
"""Print compute layer classes for the three model constructors."""
import sys
from pathlib import Path

import torch.nn as nn

SRC = Path(__file__).resolve().parents[1] / "deps/tychon-quantum-sensing/workers/odmr-edge-ml/src"
sys.path.insert(0, str(SRC))

from odmr_edge_ml.models.fcnn import OdmrFCNN
from odmr_edge_ml.models.fcnn_v2 import OdmrFCNNv2
from odmr_edge_ml.models.mlp import OdmrMLP


if __name__ == "__main__":
    for cls in (OdmrFCNN, OdmrFCNNv2, OdmrMLP):
        model = cls()
        types = sorted({type(m).__name__ for m in model.modules() if isinstance(m, (nn.Conv2d, nn.Linear))})
        print(f"{cls.__name__}: {', '.join(types)}")
