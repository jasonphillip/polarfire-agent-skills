"""Train the case study FCNN on the same simulated ODMR spectra as odmr-mlp."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from torch import nn

from odmr_edge_ml.models.fcnn import OdmrFCNN


def generate(splits, seed):
    path = Path(__file__).resolve().parents[1] / "odmr-mlp" / "example.py"
    spec = importlib.util.spec_from_file_location("pfkit_odmr_mlp_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generated = module.generate(splits, seed)
    return {split: (x[:, None, None, :], y) for split, (x, y) in generated.items()}


class OdmrFCNNAdapter(nn.Module):
    """Expose the FCNN layers without its vector-to-image view operation."""

    def __init__(self):
        super().__init__()
        self.fcnn = OdmrFCNN(input_dim=100, output_dim=1, channels=[8, 16, 24],
                             kernel_size=5, stride=2)
        self.flatten = nn.Flatten()

    def forward(self, x):
        for conv, relu in zip(self.fcnn.convs, self.fcnn.relus):
            x = relu(conv(x))
        return self.flatten(self.fcnn.conv_head(x))


def model():
    return OdmrFCNNAdapter()
