import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def fake_run_factory(fail_at, stdout="built", stderr="boom"):
    calls = []

    def fake_run(argv, text=True, capture_output=True, timeout=None):
        calls.append(argv)
        code = 1 if len(calls) == fail_at else 0
        return subprocess.CompletedProcess(argv, code, stdout, stderr if code else "")

    return fake_run, calls


def test_run_plan_keeps_diagnostics_on_failure(tmp_path, monkeypatch):
    from pfkit import remote_ops
    from pfkit.errors import RemoteCommandError

    fake, calls = fake_run_factory(fail_at=2)
    monkeypatch.setattr(remote_ops.subprocess, "run", fake)
    manifest = tmp_path / "compile.json"
    with pytest.raises(RemoteCommandError) as info:
        remote_ops.run_plan([["ssh", "h", "a"], ["ssh", "h", "b"], ["ssh", "h", "c"]], manifest=manifest)
    records = json.loads(manifest.read_text())["commands"]
    assert len(calls) == 2
    assert [r["executed"] for r in records] == [True, True]
    assert records[1]["exit_code"] == 1 and records[1]["stderr"] == "boom"
    assert records[1]["argv"] == ["ssh", "h", "b"]
    assert records[1]["started_utc"] and records[1]["finished_utc"]
    assert info.value.records == records


def test_run_plan_dry_run_is_recorded_but_not_executed(tmp_path, monkeypatch):
    from pfkit import remote_ops

    monkeypatch.setattr(remote_ops.subprocess, "run", lambda *a, **k: pytest.fail("executed"))
    manifest = tmp_path / "sim.json"
    records = remote_ops.run_plan([["ssh", "h", "a"]], dry_run=True, manifest=manifest)
    assert records[0]["executed"] is False and records[0]["exit_code"] == "not run"
    assert json.loads(manifest.read_text())["commands"] == records


def test_run_plan_keeps_timeout_diagnostics(tmp_path, monkeypatch):
    from pfkit import remote_ops
    from pfkit.errors import RemoteCommandError

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, 1, output=b"partial", stderr=b"late")

    monkeypatch.setattr(remote_ops.subprocess, "run", timeout)
    manifest = tmp_path / "compile.json"
    with pytest.raises(RemoteCommandError) as info:
        remote_ops.run_plan([["ssh", "h", "a"]], manifest=manifest, timeout_s=1)
    record = json.loads(manifest.read_text())["commands"][0]
    assert record["exit_code"] == "timeout" and record["stdout"] == "partial"
    assert record["stderr"] == "late" and info.value.records[0] == record


def test_run_plan_marks_launch_error_unexecuted(tmp_path, monkeypatch):
    from pfkit import remote_ops
    from pfkit.errors import RemoteCommandError

    def unavailable(argv, **kwargs):
        raise FileNotFoundError("ssh unavailable")

    monkeypatch.setattr(remote_ops.subprocess, "run", unavailable)
    manifest = tmp_path / "compile.json"
    with pytest.raises(RemoteCommandError):
        remote_ops.run_plan([["ssh", "h", "a"]], manifest=manifest)
    record = json.loads(manifest.read_text())["commands"][0]
    assert record["executed"] is False and "ssh unavailable" in record["error"]


def test_cli_infer_failure_writes_status_and_keeps_primary_error(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops

    fake, calls = fake_run_factory(fail_at=3)
    monkeypatch.setattr(remote_ops.subprocess, "run", fake)
    payload = tmp_path / "input.int8.bin"
    payload.write_bytes(bytes(range(4)))
    code = cli.main(["infer", "m.vnnx", "--input", str(payload), "--output", str(tmp_path / "hw.bin"),
                     "--json", str(tmp_path / "hw.json"), "--config", str(ROOT / "kit.yaml"),
                     "--run-dir", str(tmp_path)])
    assert code == 1
    record = json.loads((tmp_path / "infer.json").read_text())
    assert record["status"] == "failed" and "exit 1" in record["error"]
    assert record["retrieval"]["attempted"] is True
    assert record["retrieval"]["exit_code"] in (0, 1)
    assert record["config"]["values"]["ssh_target"] == "kit"
    assert "output" not in record
    assert len(calls) == 4


def test_missing_output_after_success_is_failed(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops

    fake, _ = fake_run_factory(fail_at=99)
    monkeypatch.setattr(remote_ops.subprocess, "run", fake)
    payload = tmp_path / "input.int8.bin"
    payload.write_bytes(bytes(range(4)))
    code = cli.main(["infer", "m.vnnx", "--input", str(payload), "--output", str(tmp_path / "hw.bin"),
                     "--json", str(tmp_path / "hw.json"), "--config", str(ROOT / "kit.yaml"),
                     "--run-dir", str(tmp_path)])
    assert code == 1
    record = json.loads((tmp_path / "infer.json").read_text())
    assert record["status"] == "failed" and "output missing" in record["error"]


def test_partial_completion_is_failed(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops

    hw_json = tmp_path / "hw.json"
    hw_bin = tmp_path / "hw.bin"

    def fake(argv, text=True, capture_output=True, timeout=None):
        if argv[0] == "scp" and str(hw_json) in argv[-1]:
            hw_json.write_text(json.dumps({"exit_code": 0, "samples": 4, "completed": 2, "npu_error": 0}))
        if argv[0] == "scp" and str(hw_bin) in argv[-1]:
            hw_bin.write_bytes(b"\x00\x00")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(remote_ops.subprocess, "run", fake)
    payload = tmp_path / "input.int8.bin"
    payload.write_bytes(bytes(range(4)))
    code = cli.main(["infer", "m.vnnx", "--input", str(payload), "--output", str(hw_bin),
                     "--json", str(hw_json), "--config", str(ROOT / "kit.yaml"), "--run-dir", str(tmp_path)])
    assert code == 1
    record = json.loads((tmp_path / "infer.json").read_text())
    assert "completed 2 of 4" in record["error"] and "output" not in record
    from pfkit import pipeline

    comparison = pipeline.compare("signal-freq", tmp_path, hw=hw_bin, scope="full")
    assert comparison["status"] == "incomplete" and comparison["pass"] is False


def test_example_run_failure_report(tmp_path, monkeypatch):
    from pfkit import cli, pipeline, reporting

    monkeypatch.setattr(pipeline, "data", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("dataset contract")))
    monkeypatch.setattr(reporting, "report", lambda d: (_ for _ in ()).throw(OSError("disk")))
    run_dir = tmp_path / "run"
    code = cli.main(["example", "run", "signal-freq", "--until", "data", "--run-dir", str(run_dir)])
    assert code == 1
    failure = json.loads((run_dir / "failure.json").read_text())
    assert failure["stage"] == "data" and "dataset contract" in failure["error"]
    assert "disk" in failure["report_error"] and failure["attempt_id"] is None


def test_report_marks_failed_stage(tmp_path):
    from pfkit.reporting import report

    (tmp_path / "compile.json").write_text(json.dumps({"status": "failed", "commands": []}))
    (tmp_path / "sim.json").write_text(json.dumps({"status": "not run", "commands": []}))
    summary = report(tmp_path).read_text()
    assert "compile.json: failed" in summary
    assert "sim.json: not run" in summary
