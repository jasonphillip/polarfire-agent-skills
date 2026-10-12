"""Seeded noisy sine windows and a small regression MLP."""
from __future__ import annotations
import numpy as np
from torch import nn


def generate(splits, seed):
    rng = np.random.default_rng(seed)
    out = {}
    times = np.arange(64, dtype=np.float32) / 64.0
    for name, count in splits.items():
        frequency = rng.uniform(1.0, 10.0, (count, 1)).astype(np.float32)
        phase = rng.uniform(0.0, 2 * np.pi, (count, 1)).astype(np.float32)
        amplitude = rng.uniform(0.7, 1.0, (count, 1)).astype(np.float32)
        signal = amplitude * np.sin(2 * np.pi * frequency * times[None, :] + phase)
        signal += rng.normal(0.0, 0.05, signal.shape).astype(np.float32)
        out[name] = (signal.astype(np.float32), frequency)
    return out


def model():
    return nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
