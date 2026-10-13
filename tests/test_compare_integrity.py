import json

import numpy as np
import pytest


@pytest.fixture
def comparison_run(tmp_path, monkeypatch):
    import tensorflow as tf
    import torch
    from pfkit import pipeline
    from pfkit.attempt import manual
    from pfkit.payload import write_payload

    values = np.zeros((2, 4), dtype=np.float32)
    cfg = {"adapter": "mlp", "input": {"shape": [1, 4]},
           "output": {"target_scale": 1},
           "tolerances": {"float_tflite_abs": 0, "tflite_sim_lsb": 0}}
    monkeypatch.setattr(pipeline, "example_module", lambda name: (cfg, None))
    monkeypatch.setattr(pipeline, "load_data", lambda directory: {"test_x": values})

    class Interpreter:
        def __init__(self, **kwargs): pass
        def allocate_tensors(self): pass
        def get_input_details(self):
            return [{"quantization": (1, 0), "shape": [1, 1, 1, 4], "index": 0}]
        def get_output_details(self):
            return [{"quantization": (1, 0), "index": 1}]
        def set_tensor(self, index, value): pass
        def invoke(self): pass
        def get_tensor(self, index): return np.zeros((1, 1), dtype=np.int8)

    class Model:
        def __call__(self, tensor): return torch.zeros((len(tensor), 1))

    monkeypatch.setattr(tf.lite, "Interpreter", Interpreter)
    monkeypatch.setattr(pipeline, "load_model", lambda name, directory: Model())
    manifest = write_payload(tmp_path, np.zeros((2, 4), dtype=np.int8),
                             {"split": "test", "method": "first", "indices": [0, 1]},
                             {"scale": 1.0, "zero_point": 0})
    model = tmp_path / "model.vnnx"
    model.write_bytes(b"model")
    sim = tmp_path / "sim.npz"
    np.savez(sim, outputs=np.zeros((2, 1), dtype=np.int8))
    hw = tmp_path / "hw.bin"
    hw.write_bytes(b"\0\0")
    attempt_id = manual(tmp_path)["attempt_id"]
    for name, output in (("sim", sim), ("infer", hw)):
        pipeline.write_json(tmp_path / f"{name}.json", {
            "status": "completed", "attempt_id": attempt_id,
            "inputs": {"model_sha256": pipeline.sha256(model),
                       "payload_sha256": manifest["payload_sha256"]},
            "output": {"path": str(output), "sha256": pipeline.sha256(output)}})
    return tmp_path, sim, hw, manifest


@pytest.mark.ml
def test_compare_rejects_explicit_payload_conflicting_with_manifest(comparison_run):
    from pfkit import pipeline

    directory, sim, hw, manifest = comparison_run
    other = directory / "other.npy"
    np.save(other, np.ones((2, 4), dtype=np.float32))
    with pytest.raises(ValueError, match="payload hash mismatch"):
        pipeline.compare("signal-freq", directory, inputs=other, sim=sim, hw=hw, scope="full")


@pytest.mark.ml
def test_compare_requires_stage_payload_hash_without_manifest(comparison_run):
    from pfkit import pipeline

    directory, sim, hw, manifest = comparison_run
    (directory / "input.manifest.json").unlink()
    record = json.loads((directory / "infer.json").read_text())
    record["inputs"]["payload_sha256"] = "f" * 64
    pipeline.write_json(directory / "infer.json", record)
    with pytest.raises(ValueError, match="payload hash mismatch"):
        pipeline.compare("signal-freq", directory, sim=sim, hw=hw, scope="full")


@pytest.mark.ml
@pytest.mark.parametrize("failure", ["invalid_payload", "missing_record", "stale_record", "validation_error"])
def test_failed_recompare_replaces_prior_pass_for_every_error(comparison_run, failure):
    from pfkit import pipeline

    directory, sim, hw, manifest = comparison_run
    assert pipeline.compare("signal-freq", directory, sim=sim, hw=hw, scope="full")["pass"]
    if failure == "invalid_payload":
        (directory / "input.int8.npy").write_bytes(b"bad")
    elif failure == "missing_record":
        (directory / "sim.json").unlink()
    elif failure == "stale_record":
        record = json.loads((directory / "sim.json").read_text())
        record["attempt_id"] = "old"
        pipeline.write_json(directory / "sim.json", record)
    else:
        sim.write_bytes(b"invalid archive")
    with pytest.raises(Exception):
        pipeline.compare("signal-freq", directory, sim=sim, hw=hw, scope="full")
    record = json.loads((directory / "compare.json").read_text())
    assert record["status"] in ("stale", "error") and record["pass"] is False
    assert record["reason"] and record["attempt_id"] == json.loads((directory / "attempt.json").read_text())["attempt_id"]


def test_report_never_records_unpassed_compare(tmp_path):
    from pfkit.reporting import report

    (tmp_path / "attempt.json").write_text(json.dumps({"attempt_id": "A1"}))
    (tmp_path / "compare.json").write_text(json.dumps({"attempt_id": "A1", "status": "error", "pass": False}))
    summary = report(tmp_path).read_text()
    assert "compare.json: recorded" not in summary
    assert "compare.json: error" in summary


@pytest.mark.ml
@pytest.mark.parametrize("mutation", ["payload", "stage"])
def test_report_does_not_record_pass_after_payload_changes(comparison_run, mutation):
    from pfkit import pipeline
    from pfkit.reporting import report

    directory, sim, hw, manifest = comparison_run
    assert pipeline.compare("signal-freq", directory, sim=sim, hw=hw, scope="full")["pass"]
    if mutation == "payload":
        (directory / "input.int8.npy").write_bytes(b"changed")
    else:
        record = json.loads((directory / "infer.json").read_text())
        record["attempt_id"] = "old"
        pipeline.write_json(directory / "infer.json", record)
    assert "compare.json: recorded" not in report(directory).read_text()
