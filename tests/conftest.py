"""Tests run against temporary directories, never the archive's own data.

`scripts/` and `src/` are on sys.path (pyproject [tool.pytest.ini_options]),
so script modules import the way they do when run from the repo root.
"""
import json

import pytest


@pytest.fixture
def manifest_file(tmp_path):
    """A small manifest.json in a temporary directory."""
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps({
        "a": {"acquisition": {"source": None}, "conversion": {"tool": None}},
        "b": {"x": 1},
        "c": {"y": 2},
    }), encoding="utf-8")
    return p
