import json
from pathlib import Path

import numpy as np
import pytest

from pfkit.payload import payload_sha256, quantize, to_model_layout, write_payload


ROOT = Path(__file__).resolve().parents[1]


def test_conv_multichannel_round_trip_is_identity_for_nchw():
    values = np.arange(1, 9, dtype=np.int8).reshape(1, 2, 1, 4)
    output = to_model_layout(values, "conv2d_1k")
    assert output.shape == values.shape
    assert output.tobytes() == values.tobytes()
    assert output.flags["C_CONTIGUOUS"]


def test_fortran_order_gives_same_bytes():
    contiguous = np.arange(64 * 64, dtype=np.int8).reshape(64, 64)
    fortran = np.asfortranarray(contiguous)
    assert to_model_layout(fortran, "mlp").tobytes() == to_model_layout(contiguous, "mlp").tobytes()


def test_nhwc_layout_hint_refused():
    with pytest.raises(ValueError, match="got layout hint nhwc"):
        to_model_layout(np.zeros((1, 2, 1, 4), dtype=np.int8), "conv2d_1k", layout_hint="nhwc")


def test_empty_payload_refused(tmp_path):
    with pytest.raises(ValueError, match="K >= 1"):
        write_payload(tmp_path, np.zeros((0, 64), dtype=np.int8),
                      {"split": "test", "method": "first", "indices": []})


def test_manifest_hash_matches_bytes(tmp_path):
    values = np.arange(8, dtype=np.int8).reshape(2, 4)
    manifest = write_payload(tmp_path, values,
                             {"split": "test", "method": "first", "indices": [0, 1]})
    assert manifest["payload_sha256"] == payload_sha256(values)
    assert (tmp_path / "input.int8.bin").read_bytes() == values.tobytes()
    assert json.loads((tmp_path / "input.manifest.json").read_text())["samples"] == 2
    assert manifest["npy_sha256"] != manifest["bin_sha256"]


@pytest.mark.parametrize("name", ["signal-freq", "odmr-mlp"])
def test_byte_identity_with_committed_batch_inputs(name, tmp_path):
    committed = np.load(ROOT / "evidence" / "2026-10-12-hardware" / "batch64" / name / "input.int8.npy")
    flattened = committed.reshape(len(committed), -1)
    manifest = write_payload(tmp_path, to_model_layout(flattened, "mlp"),
                             {"split": "test", "method": "first", "indices": list(range(64))})
    assert (tmp_path / "input.int8.bin").read_bytes() == committed.tobytes()
    assert manifest["samples"] == 64


def test_quantize_is_single_source():
    assert quantize(np.array([[0.5]], dtype=np.float32), 0.25, -3).tolist() == [[-1]]


def test_prepare_input_rejects_zero_samples(tmp_path):
    from pfkit.pipeline import prepare_input
    with pytest.raises(ValueError, match="K >= 1"):
        prepare_input("signal-freq", tmp_path, samples=0)


def test_prepare_and_compare_use_selected_payload(tmp_path, monkeypatch):
    import tensorflow as tf
    import torch
    from pfkit.attempt import manual
    from pfkit import pipeline

    values = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], dtype=np.float32)
    config = {"adapter": "mlp", "input": {"shape": [1, 4]}, "output": {"target_scale": 1},
              "tolerances": {"float_tflite_abs": 0, "tflite_sim_lsb": 0}}
    monkeypatch.setattr(pipeline, "example_module", lambda name: (config, None))
    monkeypatch.setattr(pipeline, "load_data", lambda run_dir: {"test_x": values})

    class FakeInterpreter:
        def __init__(self, **kwargs):
            pass
        def allocate_tensors(self):
            pass
        def get_input_details(self):
            return [{"quantization": (0.5, -2), "shape": [1, 1, 1, 4], "index": 0}]
        def get_output_details(self):
            return [{"quantization": (1, 0), "index": 1}]
        def set_tensor(self, index, value):
            assert value.shape == (1, 1, 1, 4)
        def invoke(self):
            pass
        def get_tensor(self, index):
            return np.zeros((1, 1), dtype=np.int8)

    class ZeroModel:
        def __call__(self, tensor):
            return torch.zeros((len(tensor), 1))

    monkeypatch.setattr(tf.lite, "Interpreter", FakeInterpreter)
    monkeypatch.setattr(pipeline, "load_model", lambda name, run_dir: ZeroModel())
    manifest = pipeline.prepare_input("signal-freq", tmp_path, samples=2,
                                      selection="random", seed=17)
    selected = values[manifest["selection"]["indices"]]
    assert np.array_equal(np.load(tmp_path / "input.int8.npy"), quantize(selected, 0.5, -2))
    assert manifest["quantization"] == {"scale": 0.5, "zero_point": -2}
    sim = tmp_path / "sim.npz"
    np.savez(sim, outputs=np.zeros((2, 1), dtype=np.int8))
    hw = tmp_path / "hw.bin"
    hw.write_bytes(b"\x00\x00")
    model = tmp_path / "model.vnnx"
    model.write_bytes(b"model")
    attempt_id = manual(tmp_path)["attempt_id"]
    for name, output in (("sim", sim), ("infer", hw)):
        pipeline.write_json(tmp_path / f"{name}.json", {
            "status": "completed", "attempt_id": attempt_id,
            "inputs": {"model_sha256": pipeline.sha256(model),
                       "payload_sha256": manifest["payload_sha256"]},
            "output": {"path": str(output), "sha256": pipeline.sha256(output)}})
    report = pipeline.compare("signal-freq", tmp_path, sim=sim, hw=hw, scope="full")
    assert report["pass"] and report["samples"] == 2
    assert report["selection"] == manifest["selection"]
    assert report["payload_sha256"] == manifest["payload_sha256"]
    (tmp_path / "input.int8.bin").write_bytes(b"wrong")
    with pytest.raises(ValueError, match="payload hash mismatch"):
        pipeline.compare("signal-freq", tmp_path, sim=sim, hw=hw)


def test_stage_records_hash_only_for_canonical_input(tmp_path):
    from pfkit.cli import _remote_stage

    values = np.arange(4, dtype=np.int8).reshape(1, 4)
    manifest = write_payload(tmp_path, values,
                             {"split": "test", "method": "first", "indices": [0]})
    for stage, source, config in (
        ("sim", tmp_path / "input.int8.npy", ROOT / "toolshost.yaml"),
        ("infer", tmp_path / "input.int8.bin", ROOT / "kit.yaml"),
    ):
        record = _remote_stage(stage, tmp_path / "model.vnnx", tmp_path / "out.bin",
                               config, tmp_path, dry_run=True, input_file=source,
                               metadata=tmp_path / "hw.json", runner=ROOT / "hw" / "vbx_run")
        assert record["payload_sha256"] == manifest["payload_sha256"]
    other = tmp_path / "other.npy"
    np.save(other, values)
    with pytest.raises(ValueError, match="canonical input"):
        _remote_stage("sim", tmp_path / "model.vnnx", tmp_path / "out.npz",
                      ROOT / "toolshost.yaml", tmp_path, dry_run=True, input_file=other)


def test_empty_manual_sim_input_rejected_before_host_plan(tmp_path, monkeypatch):
    from pfkit.cli import _remote_stage
    from pfkit import remote_ops

    empty = tmp_path / "empty.npy"
    np.save(empty, np.zeros((0, 64), dtype=np.int8))
    monkeypatch.setattr(remote_ops, "sim_plan", lambda *args: pytest.fail("host plan constructed"))
    with pytest.raises(ValueError, match="K >= 1"):
        _remote_stage("sim", tmp_path / "model.vnnx", tmp_path / "out.npz",
                      ROOT / "toolshost.yaml", input_file=empty)
