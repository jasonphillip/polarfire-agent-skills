import json, subprocess, sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "record_evidence.py"


def _run(src, dest, *extra):
    return subprocess.run([sys.executable, "-I", str(TOOL), str(src), str(dest), *extra], capture_output=True, text=True)


@pytest.mark.host
def test_replaces_known_paths_and_copies_binaries(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    kit_root = f"{Path.home()}/projects/polarfire-agent-skills/hw/vbx_run"
    kit_address = "192." + "168.1.214"
    tools_home = "/mnt/c/Users/" + "ja" + "son/pfkit-work"
    (src / "infer.json").write_text(json.dumps({"argv": ["ssh", f"root@{kit_address}", kit_root], "toolshost": tools_home}))
    (src / "hw.bin").write_bytes(b"\x01\x02")
    result = _run(src, dest)
    assert result.returncode == 0, result.stderr
    text = (dest / "infer.json").read_text()
    assert "<kit>" in text and "<kit-root>" in text and "<tools-host-home>" in text
    assert "192." + "168" not in text and "bad" + "willhunt" not in text and "ja" + "son" not in text.lower()
    assert (dest / "hw.bin").read_bytes() == b"\x01\x02"


@pytest.mark.host
def test_refuses_unscrubbed_text(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    (src / "compare.json").write_text('{"note": "ran on ' + "be" + "e-office at /" + "home/someone/x" + '"}')
    result = _run(src, dest)
    assert result.returncode == 1
    assert "unscrubbed text remains" in result.stderr


@pytest.mark.host
@pytest.mark.parametrize("private_text", [
    "C:" + r"\Users\OtherUser\run",
    "C:" + "/Users/OtherUser/run",
    "10.1.2.3",
    "172.16.0.1",
    "172.31.255.255",
    "192." + "168.2.3",
    "100.64.0.1",
    "100.127.255.255",
])
def test_refuses_windows_user_paths_and_private_ipv4(tmp_path, private_text):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    (src / "compare.json").write_text(json.dumps({"note": private_text}))
    result = _run(src, dest)
    assert result.returncode == 1, (private_text, result.stdout, result.stderr)
    assert "unscrubbed text remains" in result.stderr


@pytest.mark.host
def test_accepts_version_strings_without_dotted_quad(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    (src / "compare.json").write_text(json.dumps({"versions": ["2.0.1", "3.11.17"]}))
    result = _run(src, dest)
    assert result.returncode == 0, result.stderr


@pytest.mark.host
def test_refuses_run_without_known_records(tmp_path):
    src, dest = tmp_path / "empty-run", tmp_path / "out"
    src.mkdir()
    (src / "unrelated.txt").write_text("not a record")
    result = _run(src, dest)
    assert result.returncode == 1, result.stdout
    assert str(src) in result.stderr


@pytest.mark.host
def test_copies_and_scrubs_evaluation_inspection_and_export_records(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    kit_root = f"{Path.home()}/projects/polarfire-agent-skills/hw/vbx_run"
    records = {
        "eval.json": {"mae": 0.12, "rmse": 0.34, "source": kit_root},
        "inspect.json": {"source": kit_root},
        "export.manifest.json": {"source": kit_root},
    }
    for name, record in records.items():
        (src / name).write_text(json.dumps(record))
    result = _run(src, dest)
    assert result.returncode == 0, result.stderr
    assert "recorded 3 files" in result.stdout
    for name, record in records.items():
        copied = json.loads((dest / name).read_text())
        assert copied == {**record, "source": "<kit-root>/hw/vbx_run"}


@pytest.mark.host
def test_extra_root_replaced(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    (src / "summary.md").write_text(f"clone at {tmp_path}/clone/reports/x\n")
    result = _run(src, dest, f"{tmp_path}/clone")
    assert result.returncode == 0, result.stderr
    assert "<kit-root>/reports/x" in (dest / "summary.md").read_text()
