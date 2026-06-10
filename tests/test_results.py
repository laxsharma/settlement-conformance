"""Validate results submissions match vector catalogue."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.jws import load_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
VECTORS_DIR = REPO_ROOT / "vectors" / "v0"
RESULTS_PATH = REPO_ROOT / "results" / "a2a-se" / "results.json"


@pytest.fixture(scope="module")
def results():
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    return load_manifest(VECTORS_DIR)


def test_a2a_se_results_cover_all_vectors(results, manifest):
    result_ids = {v["vector_id"] for v in results["vectors"]}
    assert result_ids == set(manifest["vector_ids"])


def test_a2a_se_results_have_valid_verdicts(results):
    for entry in results["vectors"]:
        assert entry["expected_verdict"] in ("BLOCK", "REVIEW")
        assert entry["result"] in ("PASS", "FAIL", "N/A")
        if entry["result"] == "N/A":
            assert "reason" in entry
        if entry["result"] == "PASS":
            assert "observed" in entry
