from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inference_skill_describes_batch_input_bytes():
    text = (ROOT / "skills" / "kit-run-inference" / "SKILL.md").read_text()
    assert "K * input_bytes" in text
    assert "K >= 1" in text
    assert "selected sample count" in text
