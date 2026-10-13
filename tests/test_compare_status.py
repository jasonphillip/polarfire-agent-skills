import numpy as np
import pytest

from pfkit.pipeline import compare_arrays


F = np.array([[1.0, 2.0]])
T = np.array([[1.1, 1.8]])
RAW = np.array([[10, -2]], dtype=np.int8)
CLOSE = np.array([[11, -2]], dtype=np.int8)


def test_no_evidence_is_not_a_pass():
    report = compare_arrays(None, None)
    assert report["status"] == "no_evidence"
    assert report["pass"] is False
    assert report["complete"] is False
    assert report["checks_run"] == []


def test_partial_requested_passes_but_is_incomplete():
    report = compare_arrays(F, T, float_tolerance=0.3)
    assert report["status"] == "passed"
    assert report["complete"] is False
    assert report["tflite_vs_sim"] == {"status": "not run"}


def test_full_scope_with_missing_check_is_incomplete():
    report = compare_arrays(
        F, T, float_tolerance=0.3,
        required=("float_vs_tflite", "tflite_vs_sim", "sim_vs_hw"),
    )
    assert report["status"] == "incomplete"
    assert report["pass"] is False


def test_failed_check_fails_whole_report():
    report = compare_arrays(F, T, RAW, RAW, CLOSE, 0.3, 1, 0)
    assert report["status"] == "failed"
    assert report["sim_vs_hw"]["status"] == "failed"
    assert report["checks_failed"] == ["sim_vs_hw"]


def test_complete_pass_reports_exact_separately():
    report = compare_arrays(F, T, RAW, CLOSE, CLOSE, 0.3, 1, 0)
    assert report["status"] == "passed"
    assert report["complete"] is True
    assert report["tflite_vs_sim"]["pass"] is True
    assert report["tflite_vs_sim"]["exact"] is False
    assert report["sim_vs_hw"]["exact"] is True


@pytest.mark.parametrize("bad", [
    (np.array([[np.nan, 1.0]]), T, None, None, None),
    (np.zeros((0, 2)), np.zeros((0, 2)), None, None, None),
    (F, T, np.array([[300, 0]], dtype=np.int16), RAW, None),
    (F, T, RAW, np.array([[10, -2]], dtype=np.float32), None),
    (F, np.array([[1.0, 2.0, 3.0]]), None, None, None),
])
def test_malformed_inputs_raise(bad):
    with pytest.raises(ValueError):
        compare_arrays(*bad)


def test_compare_cli_accepts_explicit_scope():
    from pfkit.cli import parser

    args = parser().parse_args(["compare", "signal-freq", "--run-dir", "run", "--scope", "full"])
    assert args.scope == "full"
