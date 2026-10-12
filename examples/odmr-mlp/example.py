"""Use the pinned case study generator, loader, and model."""
from __future__ import annotations
import tempfile
from pathlib import Path
import numpy as np
from nv_sensor_sim.pipelines.batch_generate import generate_dataset
from odmr_edge_ml.data.loaders import DatasetLoader
from odmr_edge_ml.models.mlp import OdmrMLP


def generate(splits, seed):
    result = {}
    with tempfile.TemporaryDirectory(prefix="pfkit-odmr-") as directory:
        generate_dataset(output_dir=directory, n_train=splits["train"], n_val=splits["val"],
            n_test=splits["test"], master_seed=seed, n_freq_points=100,
            freq_range_Hz=(2.866e9, 2.874e9), noise_mode="deterministic",
            field_sampling="spherical", shift_test_ranges=False)
        loader = DatasetLoader(directory, normalize=True)
        for split in splits:
            data = loader.load_split(split)
            result[split] = (np.asarray(data.spectra, dtype=np.float32),
                             (np.linalg.norm(data.labels, axis=1) * 1e6).astype(np.float32)[:, None])
    return result


def model():
    return OdmrMLP(input_dim=100, output_dim=1, hidden_dims=[64, 64])
