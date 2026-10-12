from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pytest

for key in ("OMP_NUM_THREADS", "TF_NUM_INTRAOP_THREADS", "TF_NUM_INTEROP_THREADS"):
    os.environ.setdefault(key, "1")


def test_adapters_accept_and_reject():
    import torch
    from torch import nn
    from pfkit.adapters import to_keras, verify_transliteration
    from pfkit.errors import UnsupportedModelError
    mlp = nn.Sequential(nn.Linear(4, 3), nn.ReLU(), nn.Linear(3, 1))
    keras = to_keras(mlp, (1, 4), "mlp")
    verify_transliteration(mlp, keras, np.random.default_rng(1).normal(size=(1, 4)), "mlp")
    conv = nn.Sequential(nn.Conv2d(1, 2, (1, 3)), nn.ReLU(), nn.Flatten(), nn.Linear(12, 1))
    keras_conv = to_keras(conv, (1, 1, 1, 8), "conv2d_1k")
    verify_transliteration(conv, keras_conv, np.random.default_rng(2).normal(size=(1, 1, 1, 8)), "conv2d_1k")
    qat = nn.Sequential(nn.Linear(4, 1), torch.ao.quantization.FakeQuantize())
    verify_transliteration(qat, to_keras(qat, (1, 4), "mlp"), np.ones((1, 4)), "mlp")
    with pytest.raises(UnsupportedModelError, match="Sigmoid.*supported"):
        to_keras(nn.Sequential(nn.Linear(4, 3), nn.Sigmoid()), (1, 4), "mlp")
    with pytest.raises(UnsupportedModelError, match="Conv1d.*supported"):
        to_keras(nn.Sequential(nn.Conv1d(1, 2, 3)), (1, 1, 8), "mlp")


def test_compare_math():
    from pfkit.pipeline import compare_arrays
    a = np.array([[1.0, 2.0]])
    b = np.array([[1.1, 1.8]])
    raw = np.array([[10, -2]], dtype=np.int8)
    same = np.array([[10, -2]], dtype=np.int8)
    close = np.array([[11, -2]], dtype=np.int8)
    report = compare_arrays(a, b, raw, same, same, 0.3, 1, 0)
    assert report["pass"] and report["sim_vs_hw"]["max_abs_lsb"] == 0
    assert not compare_arrays(a, b, raw, same, close, 0.3, 1, 0)["pass"]
    assert compare_arrays(a, b)["tflite_vs_sim"] == "not run"


def test_remote_dry_runs(tmp_path, capsys):
    from pfkit.remote_ops import compile_plan, sim_plan, infer_plan, run_plan
    root = Path(__file__).resolve().parents[1]
    for commands in (
        compile_plan("m.tflite", "m.vnnx", root / "toolshost.yaml"),
        sim_plan("m.vnnx", "in.npy", "out.npz", root / "toolshost.yaml"),
        infer_plan("m.vnnx", "in.bin", "out.bin", "meta.json", "vbx_run", root / "kit.yaml", 1000),
    ):
        records = run_plan(commands, dry_run=True)
        assert all(record["exit_code"] == "not run" for record in records)
    output = capsys.readouterr().out
    assert "vnnx_compile -c V250 -t" in output
    assert "vbx_sim_run.py" in output
    assert "--timeout-ms 1000 --json" in output


def test_inspect_flags_shape_and_float(tmp_path):
    import tensorflow as tf
    from pfkit.inspect import inspect_model
    @tf.function(input_signature=[tf.TensorSpec([None, 64], tf.float32)])
    def shape_model(x):
        return tf.shape(x)
    concrete = shape_model.get_concrete_function()
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete], shape_model)
    model = converter.convert()
    path = tmp_path / "shape.tflite"; path.write_bytes(model)
    result = inspect_model(path)
    assert any("SHAPE" in flag for flag in result["flags"])
    assert any("float tensor" in flag for flag in result["flags"])
    assert "SHAPE" in result["unsupported"]


@pytest.mark.parametrize("name", ["signal-freq", "odmr-mlp"])
def test_examples_through_inspect(name, tmp_path):
    import tensorflow as tf
    from pfkit.pipeline import data, train, evaluate, export
    from pfkit.inspect import inspect_model
    run_dir = tmp_path / name
    # Small training sets keep the test short while exercising each stage.
    from pfkit.pipeline import example_module, write_json, sha256
    cfg, mod = example_module(name)
    splits = {"train": 24, "val": 8, "test": 8}
    generated = mod.generate(splits, cfg["data_seed"])
    run_dir.mkdir()
    np.savez_compressed(run_dir / "dataset.npz", **{f"{split}_{part}": array.astype(np.float32)
        for split, pair in generated.items() for part, array in zip(("x", "y"), pair)})
    report = train(name, run_dir, epochs=2)
    assert len(report["loss_curve"]) == 2
    metric = evaluate(name, run_dir)
    assert np.isfinite(metric["mae"])
    manifest = export(name, run_dir)
    result = inspect_model(run_dir / "model.tflite")
    assert not result["unsupported"]
    assert result["tensors"][result["operators"][0]["inputs"][0]]["shape"][0] == 1
    interpreter = tf.lite.Interpreter(model_path=str(run_dir / "model.tflite"))
    interpreter.allocate_tensors()
    assert interpreter.get_input_details()[0]["dtype"] == np.int8
    assert interpreter.get_output_details()[0]["dtype"] == np.int8
    assert len(manifest["sha256"]) == 64


def test_cli_remote_dry_runs(tmp_path):
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    cases = [
        (["compile", "m.tflite", "--output", "m.vnnx", "--dry-run"], "vnnx_compile -c V250 -t"),
        (["sim", "m.vnnx", "--input", "in.npy", "--output", "out.npz", "--dry-run"], "vbx_sim_run.py"),
        (["infer", "m.vnnx", "--input", "in.bin", "--output", "out.bin", "--json", "meta.json", "--dry-run"], "--timeout-ms 5000 --json"),
    ]
    for args, expected in cases:
        completed = subprocess.run([sys.executable, "-m", "pfkit", *args], cwd=root, text=True, capture_output=True)
        assert completed.returncode == 0, completed.stderr
        assert expected in completed.stdout
        assert "scp " in completed.stdout and "ssh " in completed.stdout


def test_inspect_missing_sdk_table(tmp_path):
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    sdk_root = tmp_path / "empty-sdk"
    sdk_root.mkdir()
    completed = subprocess.run(
        [sys.executable, "-m", "pfkit", "inspect", str(tmp_path / "model.tflite"),
         "--sdk-root", str(sdk_root)],
        cwd=root, text=True, capture_output=True,
    )
    assert completed.returncode == 1
    assert "VectorBlox operator table missing" in completed.stderr
    assert str(sdk_root / "docs" / "OPS.md") in completed.stderr
    assert "pfkit deps fetch" in completed.stderr
