"""Local data, training, evaluation, export and comparison stages."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "TF_NUM_INTRAOP_THREADS", "TF_NUM_INTEROP_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def example_config(name):
    path = ROOT / "examples" / name / "example.yaml"
    if not path.is_file():
        raise ValueError(f"Unknown example: {name}")
    cfg = yaml.safe_load(path.read_text())
    return cfg, path.parent


def example_module(name):
    cfg, directory = example_config(name)
    spec = importlib.util.spec_from_file_location(f"pfkit_example_{name.replace('-', '_')}", directory / cfg["module"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cfg, module


def dataset_path(run_dir):
    return Path(run_dir) / "dataset.npz"


def load_data(run_dir):
    with np.load(dataset_path(run_dir)) as source:
        return {k: np.array(source[k]) for k in source.files}


def data(name, run_dir, full=False, import_path=None):
    cfg, mod = example_module(name)
    run_dir = Path(run_dir); run_dir.mkdir(parents=True, exist_ok=True)
    if import_path:
        with np.load(import_path) as source:
            parts = {k: np.asarray(source[k]) for k in source.files}
    else:
        generated = mod.generate(cfg["full" if full else "default"]["splits"], cfg["data_seed"])
        parts = {f"{split}_{suffix}": np.asarray(value, dtype=np.float32)
                 for split, pair in generated.items() for suffix, value in zip(("x", "y"), pair)}
    for split in ("train", "val", "test"):
        x, y = parts[f"{split}_x"], parts[f"{split}_y"]
        if x.dtype != np.float32 or y.dtype != np.float32 or len(x) != len(y) or tuple(x.shape[1:]) != tuple(cfg["input"]["shape"][1:]):
            raise ValueError(f"Dataset contract failed for {split}")
    np.savez_compressed(dataset_path(run_dir), **parts)
    manifest = {"example": name, "generator_version": "pinned case study 646d575" if name == "odmr-mlp" else "pfkit 0.1.0",
                "seed": cfg["data_seed"], "split_sizes": {s: len(parts[f"{s}_x"]) for s in ("train", "val", "test")},
                "arrays": {k: {"shape": list(v.shape), "dtype": str(v.dtype),
                               "units": cfg["input" if k.endswith("_x") else "output"]["units"]} for k, v in parts.items()},
                "normalization": cfg["input"]["normalization"], "sha256": sha256(dataset_path(run_dir))}
    write_json(run_dir / "dataset.manifest.json", manifest)
    return manifest


def load_model(name, run_dir):
    import torch
    cfg, mod = example_module(name)
    model = mod.model()
    checkpoint = torch.load(Path(run_dir) / "model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model


def train(name, run_dir, full=False, epochs=None):
    import torch
    cfg, mod = example_module(name)
    data_arrays = load_data(run_dir)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg["model_seed"])
    model = mod.model()
    optimizer = torch.optim.Adam(model.parameters(), lr=float(cfg["learning_rate"]))
    x = torch.from_numpy(data_arrays["train_x"])
    y = torch.from_numpy(data_arrays["train_y"]) / float(cfg["output"]["target_scale"])
    vx = torch.from_numpy(data_arrays["val_x"])
    vy = torch.from_numpy(data_arrays["val_y"]) / float(cfg["output"]["target_scale"])
    curve = []
    for _ in range(epochs or cfg["full" if full else "default"]["epochs"]):
        model.train(); optimizer.zero_grad(set_to_none=True)
        loss = torch.mean((model(x) - y) ** 2)
        loss.backward(); optimizer.step()
        curve.append(float(loss.item()))
    model.eval()
    with torch.no_grad():
        val_loss = float(torch.mean((model(vx) - vy) ** 2).item())
    torch.save({"state_dict": model.state_dict(), "example": name}, Path(run_dir) / "model.pt")
    report = {"example": name, "epochs": len(curve), "loss_curve": curve, "val_mse_scaled": val_loss,
              "seeds": {"data": cfg["data_seed"], "model": cfg["model_seed"]},
              "versions": {"torch": torch.__version__, "numpy": np.__version__}, "sha256": sha256(Path(run_dir) / "model.pt")}
    write_json(Path(run_dir) / "training.json", report)
    return report


def evaluate(name, run_dir):
    import torch
    cfg, _ = example_module(name)
    parts = load_data(run_dir)
    model = load_model(name, run_dir)
    with torch.no_grad():
        pred = model(torch.from_numpy(parts["test_x"])).numpy() * float(cfg["output"]["target_scale"])
    delta = pred - parts["test_y"]
    report = {"mae": float(np.mean(np.abs(delta))), "rmse": float(np.sqrt(np.mean(delta ** 2))),
              "units": cfg["output"]["units"], "samples": int(len(pred))}
    write_json(Path(run_dir) / "eval.json", report)
    return report


def export(name, run_dir, form="conv1x1"):
    import tensorflow as tf
    from .adapters import to_keras, verify_transliteration
    from .inspect import inspect_model
    cfg, _ = example_module(name)
    parts = load_data(run_dir)
    model = load_model(name, run_dir)
    shape = tuple(cfg["input"]["shape"])
    keras_model = to_keras(model, shape, cfg["adapter"], form=form)
    verify_transliteration(model, keras_model, parts["test_x"][:1], cfg["adapter"])
    spec = cfg["calibration"]
    source = parts[f"{spec['split']}_x"]
    rng = np.random.default_rng(spec["seed"])
    indices = rng.choice(len(source), min(len(source), int(spec["samples"])), replace=False)
    def representatives():
        for idx in indices:
            value = source[idx:idx+1]
            if cfg["adapter"] == "conv2d_1k":
                value = value.transpose(0, 2, 3, 1)
            elif cfg["adapter"] == "mlp" and form == "conv1x1":
                value = value.reshape(1, 1, 1, -1)
            yield [value.astype(np.float32)]
    def convert(new_quantizer):
        converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representatives
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        converter.experimental_new_quantizer = new_quantizer
        return converter.convert()
    fallback = False
    primary_error = None
    try:
        blob = convert(True)
    except Exception as first:
        primary_error = str(first)
        fallback = True
        try:
            blob = convert(False)
        except Exception as second:
            raise RuntimeError(f"INT8 conversion failed: {first}; fallback experimental_new_quantizer=False: {second}") from second
    path = Path(run_dir) / "model.tflite"
    path.write_bytes(blob)
    result = inspect_model(path)
    qats = {}
    for module_name, module in model.named_modules():
        if "fake_quant" in type(module).__name__.lower() or "observer" in type(module).__name__.lower():
            qats[module_name] = {key: getattr(module, key).detach().cpu().numpy().tolist()
                                 for key in ("scale", "zero_point") if hasattr(module, key)}
    manifest = {"adapter": cfg["adapter"], "size_bytes": len(blob), "sha256": sha256(path),
                "calibration": {**spec, "indices": [int(i) for i in indices]}, "fallback_quantizer": fallback, "primary_quantizer_error": primary_error,
                "weight_transfer": "Torch float weights copied to Keras; converter quantizes them",
                "training_quantization_survival": "No Torch scales or zero points are reused; converter regenerates all tensor scales and zero points. Calibration sets activation ranges; copied weights set weight ranges.",
                "qat_fake_quant_observers": qats,
                "converter_quantization": {t["name"]: t["quantization"] for t in result["tensors"] if t["quantization"]["scales"]}}
    if cfg["adapter"] == "mlp":
        manifest.update({"export_form": form,
                         "export_form_reason": "SDK 2.0.3 simulator returns a constant for a fused ReLU FULLY_CONNECTED chain; Conv2D 1x1 matches TFLite.",
                         "export_form_probe": "evidence/2026-10-12-toolshost/probe-c8-fc-chains.md"})
    write_json(Path(run_dir) / "export.manifest.json", manifest)
    return manifest


def compare_arrays(float_values, tflite_values, tflite_raw=None, sim_values=None, hw_values=None,
                   float_tolerance=1.0, sim_tolerance=1, hw_tolerance=0):
    report = {"float_vs_tflite": "not run", "tflite_vs_sim": "not run", "sim_vs_hw": "not run", "pass": True}
    for left, right, label in ((float_values, tflite_values, "float/TFLite"), (tflite_raw, sim_values, "TFLite/simulator"), (sim_values, hw_values, "simulator/hardware")):
        if left is not None and right is not None and np.shape(left) != np.shape(right):
            raise ValueError(f"{label} shape mismatch: {np.shape(left)} != {np.shape(right)}")
    if float_values is not None and tflite_values is not None:
        delta = float(np.max(np.abs(np.asarray(float_values) - np.asarray(tflite_values))))
        ok = delta <= float_tolerance
        report["float_vs_tflite"] = {"max_abs": delta, "tolerance": float_tolerance, "pass": ok}
        report["pass"] &= ok
    if sim_values is not None and tflite_raw is not None:
        delta = int(np.max(np.abs(np.asarray(tflite_raw, dtype=np.int16) - np.asarray(sim_values, dtype=np.int16))))
        ok = delta <= sim_tolerance
        report["tflite_vs_sim"] = {"max_abs_lsb": delta, "tolerance_lsb": sim_tolerance, "pass": ok}
        report["pass"] &= ok
    if hw_values is not None and sim_values is not None:
        delta = int(np.max(np.abs(np.asarray(sim_values, dtype=np.int16) - np.asarray(hw_values, dtype=np.int16))))
        ok = delta <= hw_tolerance
        report["sim_vs_hw"] = {"max_abs_lsb": delta, "tolerance_lsb": hw_tolerance, "pass": ok}
        report["pass"] &= ok
    return report


def load_hardware_outputs(path, shape):
    raw = np.fromfile(path, dtype=np.int8)
    expected = int(np.prod(shape))
    if raw.size != expected:
        raise ValueError(f"hardware output size mismatch: got {raw.size} bytes, expected {expected}")
    return raw.reshape(shape)


def compare(name, run_dir, inputs=None, sim=None, hw=None, lsb_tolerance=0):
    import tensorflow as tf
    import torch
    cfg, _ = example_module(name)
    parts = load_data(run_dir)
    sim_raw = np.load(sim)["outputs"] if sim else None
    sample_count = len(sim_raw) if sim_raw is not None else 1
    x = np.load(inputs) if inputs else parts["test_x"][:sample_count]
    if len(x) != sample_count and sim_raw is not None:
        raise ValueError(f"input/simulator sample count mismatch: {len(x)} != {sample_count}")
    if len(x.shape) == len(cfg["input"]["shape"]) - 1:
        x = x[None, ...]
    x = np.asarray(x, dtype=np.float32)
    with torch.no_grad():
        floated = load_model(name, run_dir)(torch.from_numpy(x)).numpy() * cfg["output"]["target_scale"]
    interpreter = tf.lite.Interpreter(model_path=str(Path(run_dir) / "model.tflite"), num_threads=1)
    interpreter.allocate_tensors()
    i, o = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    tflite_raw, tflite_float = [], []
    for sample in x:
        value = sample[None]
        if cfg["adapter"] == "conv2d_1k":
            value = value.transpose(0, 2, 3, 1)
        elif cfg["adapter"] == "mlp" and len(i["shape"]) == 4:
            value = value.reshape(i["shape"])
        scale, zero = i["quantization"]
        quantized = np.clip(np.rint(value / scale + zero), -128, 127).astype(np.int8)
        interpreter.set_tensor(i["index"], quantized); interpreter.invoke()
        raw = interpreter.get_tensor(o["index"])
        tflite_raw.append(raw[0]); tflite_float.append((raw[0].astype(np.float32) - o["quantization"][1]) * o["quantization"][0] * cfg["output"]["target_scale"])
    raw = np.asarray(tflite_raw)
    hw_raw = load_hardware_outputs(hw, raw.shape) if hw else None
    report = compare_arrays(floated, np.asarray(tflite_float), raw, sim_raw, hw_raw,
                            cfg["tolerances"]["float_tflite_abs"], cfg["tolerances"]["tflite_sim_lsb"], lsb_tolerance)
    write_json(Path(run_dir) / "compare.json", report)
    return report
