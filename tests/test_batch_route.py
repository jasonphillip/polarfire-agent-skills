"""The CLI carries one selected batch through preparation and comparison."""
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize("samples,selection,seed", [(1, "first", None), (64, "random", 3)])
def test_example_run_carries_sample_count_and_payload(tmp_path, monkeypatch, capsys,
                                                       samples, selection, seed):
    from pfkit import cli, pipeline

    seen = []
    run_dir = tmp_path / "run"
    monkeypatch.setattr(pipeline, "data", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "train", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "evaluate", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "export", lambda *a, **k: None)
    monkeypatch.setattr("pfkit.inspect.inspect_model", lambda *a, **k: {
        "unsupported": [], "limit_violations": [], "blocking_flags": []})
    monkeypatch.setattr(cli, "_stamp_local_stage", lambda *a, **k: None)
    monkeypatch.setattr("pfkit.reporting.report", lambda path: Path(path) / "summary.md")

    def prepare(name, directory, samples=1, split="test", selection="first", seed=None):
        from pfkit.payload import write_payload

        seen.append(("prepare", samples, split, selection, seed))
        return write_payload(directory, np.arange(samples * 4, dtype=np.int8).reshape(samples, 4),
                             {"split": split, "method": selection,
                              "indices": list(range(samples)), "seed": seed})

    def remote(stage, model, output, config, directory, **kwargs):
        seen.append((stage, kwargs.get("input_file")))
        if stage == "compile":
            output.write_bytes(b"model")
        elif stage == "sim":
            np.savez(output, outputs=np.zeros((samples, 1), dtype=np.int8))
        else:
            output.write_bytes(bytes(samples))
        if stage in ("sim", "infer"):
            manifest = json.loads((directory / "input.manifest.json").read_text())
            pipeline.write_json(directory / f"{stage}.json", {
                "inputs": {"payload_sha256": manifest["payload_sha256"]}})
        return {"status": "completed"}

    monkeypatch.setattr(pipeline, "prepare_input", prepare)
    monkeypatch.setattr(cli, "_remote_stage", remote)
    args = ["example", "run", "signal-freq", "--until", "infer", "--samples", str(samples),
            "--selection", selection, "--run-dir", str(run_dir)]
    if seed is not None:
        args.extend(["--seed", str(seed)])
    assert cli.main(args) == 0
    manifest = json.loads((run_dir / "input.manifest.json").read_text())
    assert manifest["samples"] == samples
    assert ("prepare", samples, "test", selection, seed) in seen
    assert ("sim", run_dir / "input.int8.npy") in seen
    assert ("infer", run_dir / "input.int8.bin") in seen
    for stage in ("sim", "infer"):
        record = json.loads((run_dir / f"{stage}.json").read_text())
        assert record["inputs"]["payload_sha256"] == manifest["payload_sha256"]
    expected = f"samples: {samples}" + (" (one-sample fast path)" if samples == 1 else "")
    assert expected in capsys.readouterr().out


def test_prepare_input_cli_forwards_selection(tmp_path, monkeypatch, capsys):
    from pfkit import cli, pipeline

    received = []

    def prepare(name, directory, samples=1, split="test", selection="first", seed=None):
        received.append((name, directory, samples, split, selection, seed))
        return {"samples": samples, "selection": {"method": selection, "seed": seed}}

    monkeypatch.setattr(pipeline, "prepare_input", prepare)
    assert cli.main(["prepare-input", "signal-freq", "--run-dir", str(tmp_path),
                     "--samples", "8", "--split", "test", "--selection", "random",
                     "--seed", "3"]) == 0
    assert received == [("signal-freq", tmp_path, 8, "test", "random", 3)]
    assert '"samples": 8' in capsys.readouterr().out


@pytest.mark.parametrize("until", ["infer", "compare"])
def test_example_preflights_missing_runner_before_remote_stages(tmp_path, monkeypatch, capsys, until):
    from pfkit import cli, pipeline

    monkeypatch.setattr(cli, "ROOT", tmp_path / "missing-root")
    monkeypatch.setattr(cli, "_remote_stage", lambda *a, **k: pytest.fail("remote stage started"))
    monkeypatch.setattr("pfkit.reporting.report", lambda directory: tmp_path / "summary.md")
    monkeypatch.setattr(pipeline, "data", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "train", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "evaluate", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "export", lambda *a, **k: None)
    monkeypatch.setattr("pfkit.inspect.inspect_model", lambda *a, **k: {
        "unsupported": [], "limit_violations": [], "blocking_flags": []})
    monkeypatch.setattr(cli, "_stamp_local_stage", lambda *a, **k: None)
    code = cli.main(["example", "run", "signal-freq", "--until", until,
                     "--run-dir", str(tmp_path / "run")])
    assert code == 1
    assert "runner not found: hw/vbx_run; build it on the tools host (docs/hardware.md, Runner)" in capsys.readouterr().err


@pytest.mark.ml
def test_compare_reports_batch_metadata(tmp_path, monkeypatch):
    import tensorflow as tf
    import torch
    from pfkit import pipeline

    values = np.arange(32, dtype=np.float32).reshape(8, 4)
    config = {"adapter": "mlp", "input": {"shape": [1, 4]},
              "output": {"target_scale": 1, "units": "hertz"},
              "tolerances": {"float_tflite_abs": 0, "tflite_sim_lsb": 1}}
    monkeypatch.setattr(pipeline, "example_module", lambda name: (config, None))
    monkeypatch.setattr(pipeline, "load_data", lambda directory: {"test_x": values})

    class FakeInterpreter:
        def __init__(self, **kwargs):
            pass
        def allocate_tensors(self):
            pass
        def get_input_details(self):
            return [{"quantization": (0.5, 0), "shape": [1, 1, 1, 4], "index": 0}]
        def get_output_details(self):
            return [{"quantization": (1, 0), "index": 1}]
        def set_tensor(self, index, value):
            pass
        def invoke(self):
            pass
        def get_tensor(self, index):
            return np.zeros((1, 1), dtype=np.int8)

    class ZeroModel:
        def __call__(self, tensor):
            return torch.zeros((len(tensor), 1))

    monkeypatch.setattr(tf.lite, "Interpreter", FakeInterpreter)
    monkeypatch.setattr(pipeline, "load_model", lambda name, directory: ZeroModel())
    manifest = pipeline.prepare_input("signal-freq", tmp_path, samples=8,
                                      selection="random", seed=3)
    repeated = pipeline.prepare_input("signal-freq", tmp_path, samples=8,
                                      selection="random", seed=3)
    assert repeated["selection"]["indices"] == manifest["selection"]["indices"]
    assert len(set(manifest["selection"]["indices"])) == 8
    report = pipeline.compare("signal-freq", tmp_path, lsb_tolerance=2)
    assert report["samples"] == 8
    assert report["split"] == "test"
    assert report["selection"] == manifest["selection"]
    assert report["payload_sha256"] == manifest["payload_sha256"]
    assert report["units"] == "hertz"
    assert report["tolerances"] == {"float_tflite_abs": 0, "tflite_sim_lsb": 1,
                                    "sim_hw_lsb": 2}
    assert json.loads((tmp_path / "compare.json").read_text())["units"] == "hertz"
