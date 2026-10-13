"""Canonical INT8 payload for the simulator, kit, and comparison stages."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from .pipeline import sha256, write_json


LAYOUT = "model (NCHW element order; MLP samples are flat C)"


def quantize(values, scale, zero_point):
    if scale <= 0:
        raise ValueError("TFLite input has no quantization scale")
    return np.clip(np.rint(np.asarray(values, dtype=np.float32) / scale + zero_point),
                   -128, 127).astype(np.int8)


def to_model_layout(samples, adapter, layout_hint="nchw"):
    if layout_hint != "nchw":
        raise ValueError(f"samples must be NCHW; got layout hint {layout_hint}")
    if adapter not in ("mlp", "conv2d_1k"):
        raise ValueError(f"Unsupported adapter: {adapter}")
    array = np.ascontiguousarray(samples)
    if array.dtype != np.int8:
        raise ValueError(f"payload must be int8, got {array.dtype}")
    expected_ndim = 2 if adapter == "mlp" else 4
    if array.ndim != expected_ndim:
        raise ValueError(f"{adapter} payload must have {expected_ndim} dimensions (K first), got shape {array.shape}")
    return array


def payload_sha256(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def write_payload(directory, samples, selection, quantization=None):
    directory = Path(directory)
    array = np.ascontiguousarray(samples)
    if array.ndim < 2 or array.shape[0] < 1:
        raise ValueError("payload must contain K >= 1 int8 samples")
    if array.dtype != np.int8:
        raise ValueError(f"payload must be int8, got {array.dtype}")
    directory.mkdir(parents=True, exist_ok=True)
    np.save(directory / "input.int8.npy", array)
    (directory / "input.int8.bin").write_bytes(array.tobytes())
    manifest = {"samples": int(array.shape[0]), "shape": list(array.shape),
                "dtype": "int8", "layout": LAYOUT, "selection": selection,
                "quantization": quantization or {},
                "payload_sha256": payload_sha256(array),
                "npy_sha256": sha256(directory / "input.int8.npy"),
                "bin_sha256": sha256(directory / "input.int8.bin")}
    write_json(directory / "input.manifest.json", manifest)
    return manifest
