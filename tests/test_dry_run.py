import hashlib
import json
import shlex
import subprocess
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def infer_args(tmp_path, npy):
    return ["infer", "m.vnnx", "--input", str(npy), "--output", str(tmp_path / "hw.bin"),
            "--json", str(tmp_path / "hw.json"), "--config", str(ROOT / "kit.yaml")]


def test_dry_run_preserves_existing_bin_and_runs_nothing(tmp_path, monkeypatch, capsys):
    from pfkit import cli, remote_ops
    calls = []
    monkeypatch.setattr(remote_ops.subprocess, "run", lambda *a, **k: calls.append(a) or pytest.fail("subprocess ran"))
    npy = tmp_path / "input.int8.npy"
    values = np.arange(8, dtype=np.int8).reshape(2, 4)
    np.save(npy, values)
    existing = npy.with_suffix(".bin")
    existing.write_bytes(b"KEEP")
    assert cli.main([*infer_args(tmp_path, npy), "--dry-run"]) == 0
    assert existing.read_bytes() == b"KEEP" and calls == []
    assert f"would write {existing} (2 samples, 8 bytes, sha256 {hashlib.sha256(values.tobytes()).hexdigest()})" in capsys.readouterr().out


def test_execution_refuses_to_overwrite_different_bin(tmp_path, monkeypatch, capsys):
    from pfkit import cli, remote_ops
    monkeypatch.setattr(remote_ops.subprocess, "run", lambda *a, **k: pytest.fail("subprocess ran"))
    npy = tmp_path / "input.int8.npy"
    np.save(npy, np.arange(8, dtype=np.int8).reshape(2, 4))
    binary = npy.with_suffix(".bin")
    binary.write_bytes(b"OTHER")
    assert cli.main(infer_args(tmp_path, npy)) == 1
    assert binary.read_bytes() == b"OTHER"
    assert "pass --overwrite-payload" in capsys.readouterr().err


def test_empty_npy_rejected_before_host_plan(tmp_path, monkeypatch, capsys):
    from pfkit import cli, remote_ops
    monkeypatch.setattr(remote_ops.subprocess, "run", lambda *a, **k: pytest.fail("subprocess ran"))
    npy = tmp_path / "input.int8.npy"
    np.save(npy, np.zeros((0, 4), dtype=np.int8))
    assert cli.main([*infer_args(tmp_path, npy), "--dry-run"]) == 1
    assert not npy.with_suffix(".bin").exists()
    assert "K >= 1" in capsys.readouterr().err


def test_execution_allows_identical_bin_and_explicit_overwrite(tmp_path, monkeypatch, capsys):
    from pfkit import cli, remote_ops
    monkeypatch.setattr(remote_ops, "run_plan", lambda commands, **kwargs: [])
    npy = tmp_path / "input.int8.npy"
    values = np.arange(8, dtype=np.int8).reshape(2, 4)
    np.save(npy, values)
    binary = npy.with_suffix(".bin")
    binary.write_bytes(values.tobytes())
    assert cli.main(infer_args(tmp_path, npy)) == 1
    assert "output missing after transfer" in capsys.readouterr().err
    assert binary.read_bytes() == values.tobytes()
    binary.write_bytes(b"OTHER")
    # A mocked command sequence cannot produce an output; conversion still occurs first.
    assert cli.main([*infer_args(tmp_path, npy), "--overwrite-payload"]) == 1
    assert binary.read_bytes() == values.tobytes()


def test_remote_dir_with_space_is_quoted(tmp_path):
    from pfkit.remote_ops import compile_plan, infer_plan, sim_plan
    kit = tmp_path / "kit.yaml"
    kit.write_text(yaml.safe_dump({"ssh_target": "kit", "remote_dir": "/tmp/pf kit"}))
    plan = infer_plan("m.vnnx", "in.bin", "hw.bin", "hw.json", "vbx_run", kit, 1000, attempt_id="A1")
    assert "'/tmp/pf kit/A1'" in plan[0][2]
    assert plan[1][-1] == "kit:'/tmp/pf kit/A1/'"
    assert "'/tmp/pf kit/A1/vbx_run'" in plan[2][2]
    assert plan[3][1] == "kit:'/tmp/pf kit/A1/hw.bin'"
    tools = tmp_path / "toolshost.yaml"
    tools.write_text(yaml.safe_dump({"ssh_target": "tools", "remote_work_dir": "/tmp/pf kit", "size_config": "V250"}))
    sim = sim_plan("m.vnnx", "in.npy", "out.npz", tools, attempt_id="A1")
    assert sim[1][-1] == "tools:'/tmp/pf kit/A1/'"
    assert sim[3][1] == "tools:'/tmp/pf kit/A1/out.npz'"
    inner = shlex.split(sim[2][2])[-1]
    assert "mkdir -p '/tmp/pf kit/A1'" in inner
    assert "'/tmp/pf kit/A1/vbx_sim_run.py'" in inner
    compiled = compile_plan("m.tflite", "m.vnnx", tools, attempt_id="A1")
    assert compiled[1][-1] == "tools:'/tmp/pf kit/A1/m.tflite'"
    assert compiled[3][1] == "tools:'/tmp/pf kit/A1/m.vnnx'"
    assert "mkdir -p '/tmp/pf kit/A1'" in shlex.split(compiled[2][2])[-1]


def test_config_validation_names_file_and_key(tmp_path):
    from pfkit.remote_ops import load_config
    cfg = tmp_path / "toolshost.yaml"
    cfg.write_text("ssh_target: tools-host\n")
    with pytest.raises(ValueError, match=r"toolshost.yaml: missing key 'remote_work_dir' for a toolshost config"):
        load_config(cfg, "toolshost")
    cfg.write_text("ssh_target: k\nremote_dir: /tmp/x\ntimeouts: {infer: -5}\n")
    with pytest.raises(ValueError, match="timeouts.infer"):
        load_config(cfg, "kit")
    cfg.write_text("ssh_target: k\nremote_dir: /tmp/x\ntimeouts: {infer: true}\n")
    with pytest.raises(ValueError, match="timeouts.infer"):
        load_config(cfg, "kit")


def test_timeout_is_recorded_and_fails(tmp_path, monkeypatch):
    from pfkit import remote_ops
    from pfkit.errors import RemoteCommandError
    def hang(argv, text=True, capture_output=True, timeout=None):
        raise subprocess.TimeoutExpired(argv, timeout, output="partial", stderr="")
    monkeypatch.setattr(remote_ops.subprocess, "run", hang)
    manifest = tmp_path / "sim.json"
    with pytest.raises(RemoteCommandError):
        remote_ops.run_plan([["ssh", "h", "sleep"]], manifest=manifest, timeout_s=7)
    record = json.loads(manifest.read_text())["commands"][0]
    assert record["exit_code"] == "timeout" and "7 s" in record["error"] and record["stdout"] == "partial"


def test_compile_timeout_default_is_unbounded():
    from pfkit.remote_ops import load_config
    assert load_config(ROOT / "toolshost.yaml", "toolshost")["timeouts"]["compile"] is None


def test_stage_uses_configured_timeout(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops
    cfg = tmp_path / "kit.yaml"
    cfg.write_text("ssh_target: kit\nremote_dir: /tmp/pfkit\ntimeouts: {infer: 7}\n")
    observed = []
    monkeypatch.setattr(remote_ops, "run_plan", lambda commands, **kwargs: observed.append(kwargs["timeout_s"]) or [])
    cli._remote_stage("infer", "m.vnnx", tmp_path / "hw.bin", cfg, dry_run=True,
                      input_file="in.bin", metadata=tmp_path / "hw.json", runner="vbx_run")
    assert observed == [7]


def test_execution_creates_output_directories_only_when_running(tmp_path, monkeypatch):
    from pfkit import cli, remote_ops
    monkeypatch.setattr(remote_ops, "run_plan", lambda commands, **kwargs: [])
    output = tmp_path / "outputs" / "hw.bin"
    metadata = tmp_path / "metadata" / "hw.json"
    kwargs = dict(input_file="in.bin", metadata=metadata, runner="vbx_run")
    cli._remote_stage("infer", "m.vnnx", output, ROOT / "kit.yaml", dry_run=True, **kwargs)
    assert not output.parent.exists() and not metadata.parent.exists()
    with pytest.raises(ValueError, match="output missing"):
        cli._remote_stage("infer", "m.vnnx", output, ROOT / "kit.yaml", **kwargs)
    assert output.parent.is_dir() and metadata.parent.is_dir()
