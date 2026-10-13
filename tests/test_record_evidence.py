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
def test_extra_root_replaced(tmp_path):
    src, dest = tmp_path / "run", tmp_path / "out"
    src.mkdir()
    (src / "summary.md").write_text(f"clone at {tmp_path}/clone/reports/x\n")
    result = _run(src, dest, f"{tmp_path}/clone")
    assert result.returncode == 0, result.stderr
    assert "<kit-root>/reports/x" in (dest / "summary.md").read_text()
