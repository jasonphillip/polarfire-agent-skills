import pytest

from pfkit import pipeline


pytestmark = pytest.mark.ml


def test_odmr_fcnn_example_exists():
    cfg, module = pipeline.example_module("odmr-fcnn")
    assert cfg["adapter"] == "conv2d_1k"
    assert cfg["name"] == "odmr-fcnn"
