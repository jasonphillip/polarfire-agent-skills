import json
import subprocess
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_example_run_refuses_nonempty_run_dir(tmp_path):
    from pfkit import cli

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "compare.json").write_text('{"pass": true}')
    assert cli.main(["example", "run", "signal-freq", "--until", "data", "--run-dir", str(run_dir)]) == 1
    assert (run_dir / "compare.json").read_text() == '{"pass": true}'
    assert not (run_dir / "attempt.json").exists()


def test_report_marks_leftover_compare_as_stale(tmp_path):
    from pfkit.attempt import new
    from pfkit.reporting import report

    new(tmp_path, ["example", "run"])
    (tmp_path / "compare.json").write_text(json.dumps({
        "status": "passed", "pass": True, "attempt_id": "20260101-000000-deadbeef"}))
    summary = report(tmp_path).read_text()
    assert "compare.json: stale (attempt 20260101-000000-deadbeef)" in summary


def test_two_runs_same_basename_get_distinct_remote_paths():
    from pfkit.remote_ops import infer_plan

    a = infer_plan("m.vnnx", "in.bin", "hw.bin", "hw.json", "vbx_run", ROOT / "kit.yaml", 1000,
                   attempt_id="A1")
    b = infer_plan("m.vnnx", "in.bin", "hw.bin", "hw.json", "vbx_run", ROOT / "kit.yaml", 1000,
                   attempt_id="B2")
    assert "/tmp/pfkit/A1/" in " ".join(a[1])
    assert "/tmp/pfkit/B2/" in " ".join(b[1])
    assert a[2] != b[2]


def test_compare_refuses_sim_from_other_model(tmp_path):
    from pfkit import pipeline

    (tmp_path / "model.vnnx").write_bytes(b"new model")
    (tmp_path / "sim.json").write_text(json.dumps({
        "status": "completed", "inputs": {"model_sha256": "0" * 64,
                                          "payload_sha256": "1" * 64}}))
    with pytest.raises(ValueError, match="stale"):
        pipeline.check_prerequisites(tmp_path, sim=tmp_path / "sim.npz")


def test_git_revision_resolves_worktree(tmp_path):
    from pfkit.reporting import git_revision

    main = tmp_path / "main" / ".git"
    (main / "worktrees" / "wt").mkdir(parents=True)
    (main / "refs" / "heads").mkdir(parents=True)
    (main / "refs" / "heads" / "feature").write_text("abc123\n")
    (main / "worktrees" / "wt" / "HEAD").write_text("ref: refs/heads/feature\n")
    (main / "worktrees" / "wt" / "commondir").write_text("../..\n")
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {main / 'worktrees' / 'wt'}\n")
    assert git_revision(wt) == "abc123"


def test_manual_stages_share_attempt_and_record_input_hashes(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops
    from pfkit.pipeline import sha256

    model = tmp_path / "model.vnnx"
    model.write_bytes(b"model")
    payload = tmp_path / "input.int8.npy"
    np.save(payload, np.array([[1, 2]], dtype=np.int8))
    binary = tmp_path / "input.int8.bin"
    binary.write_bytes(b"\x01\x02")
    np.savez(tmp_path / "sim.npz", outputs=np.zeros((1, 1), dtype=np.int8))
    (tmp_path / "hw.bin").write_bytes(b"\0")
    (tmp_path / "hw.json").write_text(json.dumps({
        "samples": 1, "completed": 1, "npu_error": 0, "exit_code": 0,
        "outputs": [{"offset": 0, "bytes": 1}]}))
    monkeypatch.setattr(remote_ops, "run_plan", lambda commands, **kwargs: [])
    for stage, extra in (("sim", ["--input", str(payload)]),
                         ("infer", ["--input", str(binary), "--json", str(tmp_path / "hw.json")])):
        output = tmp_path / ("sim.npz" if stage == "sim" else "hw.bin")
        config = ROOT / ("toolshost.yaml" if stage == "sim" else "kit.yaml")
        args = [stage, str(model), *extra, "--output", str(output), "--config", str(config),
                "--run-dir", str(tmp_path)]
        assert cli.main(args) == 0
    sim = json.loads((tmp_path / "sim.json").read_text())
    infer = json.loads((tmp_path / "infer.json").read_text())
    assert sim["attempt_id"] == infer["attempt_id"]
    assert sim["inputs"]["model_sha256"] == sha256(model)
    assert infer["inputs"]["model_sha256"] == sha256(model)


def test_compare_writes_stale_result_before_raising(tmp_path):
    from pfkit import pipeline

    (tmp_path / "model.vnnx").write_bytes(b"new model")
    (tmp_path / "sim.json").write_text(json.dumps({
        "status": "completed", "inputs": {"model_sha256": "0" * 64}}))
    with pytest.raises(ValueError, match="stale"):
        pipeline.compare("signal-freq", tmp_path, sim=tmp_path / "sim.npz")
    result = json.loads((tmp_path / "compare.json").read_text())
    assert result["status"] == "stale" and result["pass"] is False


def test_changed_payload_invalidates_sim_and_infer(tmp_path):
    from pfkit import pipeline

    (tmp_path / "model.vnnx").write_bytes(b"model")
    (tmp_path / "input.manifest.json").write_text(json.dumps({"payload_sha256": "2" * 64}))
    for name in ("sim", "infer"):
        (tmp_path / f"{name}.json").write_text(json.dumps({
            "status": "completed", "inputs": {
                "model_sha256": pipeline.sha256(tmp_path / "model.vnnx"),
                "payload_sha256": "1" * 64}}))
        with pytest.raises(ValueError, match="stale.*payload"):
            pipeline.check_prerequisites(tmp_path, **{("sim" if name == "sim" else "hw"): tmp_path / "output"})


def test_failed_sim_does_not_use_leftover_output(tmp_path):
    from pfkit import pipeline

    (tmp_path / "sim.json").write_text(json.dumps({"status": "failed"}))
    result = pipeline.compare("signal-freq", tmp_path, sim=tmp_path / "sim.npz", scope="full")
    assert result["status"] == "incomplete" and result["pass"] is False
    assert result["reason"] == "simulation stage failed"


def test_not_run_sim_cannot_authorize_leftover_output(tmp_path):
    from pfkit import pipeline

    (tmp_path / "sim.json").write_text(json.dumps({"status": "not run"}))
    with pytest.raises(ValueError, match="stale.*not completed"):
        pipeline.compare("signal-freq", tmp_path, sim=tmp_path / "sim.npz", scope="full")


def test_changed_output_invalidates_stage_record(tmp_path):
    from pfkit import pipeline

    model = tmp_path / "model.vnnx"
    model.write_bytes(b"model")
    output = tmp_path / "sim.npz"
    output.write_bytes(b"changed")
    (tmp_path / "sim.json").write_text(json.dumps({
        "status": "completed", "inputs": {"model_sha256": pipeline.sha256(model)},
        "output": {"path": str(output), "sha256": "0" * 64}}))
    with pytest.raises(ValueError, match="stale.*output"):
        pipeline.check_prerequisites(tmp_path, sim=output)


def test_running_stage_manifest_keeps_attempt_identity(tmp_path, monkeypatch):
    from pfkit.attempt import manual
    from pfkit import cli, remote_ops

    model = tmp_path / "model.tflite"
    model.write_bytes(b"model")
    manual(tmp_path)
    observed = []

    def fake_run(argv, **kwargs):
        record = json.loads((tmp_path / "compile.json").read_text())
        observed.append((record.get("attempt_id"), record.get("inputs", {}).get("model_sha256")))
        return subprocess.CompletedProcess(argv, 1, "", "failed")

    monkeypatch.setattr(remote_ops.subprocess, "run", fake_run)
    code = cli.main(["compile", str(model), "--output", str(tmp_path / "model.vnnx"),
                     "--config", str(ROOT / "toolshost.yaml"), "--run-dir", str(tmp_path)])
    assert code == 1
    assert observed == [(json.loads((tmp_path / "attempt.json").read_text())["attempt_id"],
                         json.loads((tmp_path / "compile.json").read_text())["inputs"]["model_sha256"])]


def test_compare_requires_stage_record_for_external_artifact(tmp_path):
    from pfkit import pipeline

    with pytest.raises(ValueError, match="stale.*sim.json is missing"):
        pipeline.compare("signal-freq", tmp_path, sim=tmp_path / "sim.npz", scope="full")
    result = json.loads((tmp_path / "compare.json").read_text())
    assert result["status"] == "stale" and result["pass"] is False


def test_completed_sim_requires_model_and_output_hash(tmp_path):
    from pfkit import pipeline

    output = tmp_path / "sim.npz"
    output.write_bytes(b"result")
    (tmp_path / "sim.json").write_text(json.dumps({"status": "completed", "inputs": {}}))
    with pytest.raises(ValueError, match="stale.*model"):
        pipeline.check_prerequisites(tmp_path, sim=output)
    model = tmp_path / "model.vnnx"
    model.write_bytes(b"model")
    (tmp_path / "sim.json").write_text(json.dumps({
        "status": "completed", "inputs": {"model_sha256": pipeline.sha256(model)}}))
    with pytest.raises(ValueError, match="stale.*output hash"):
        pipeline.check_prerequisites(tmp_path, sim=output)
