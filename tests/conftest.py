"""Assign local test routes and explain unavailable ML dependencies."""

import importlib

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if not any(item.get_closest_marker(name) for name in
                   ("host", "ml", "fake_driver", "vendor", "hardware")):
            item.add_marker(pytest.mark.host)


def pytest_runtest_setup(item):
    if item.get_closest_marker("ml"):
        try:
            importlib.import_module("torch")
            importlib.import_module("tensorflow")
        except (ImportError, OSError):
            pytest.skip("torch/tensorflow not installed")
