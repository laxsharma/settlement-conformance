"""Validate vendored v0 vectors: shape + JWS."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.jws import (
    load_all_vectors,
    load_manifest,
    validate_vector_shape,
    verify_vector_jws,
)

VECTORS_DIR = Path(__file__).resolve().parent.parent / "vectors" / "v0"


@pytest.fixture(scope="module")
def manifest():
    return load_manifest(VECTORS_DIR)


@pytest.fixture(scope="module")
def vectors():
    return load_all_vectors(VECTORS_DIR)


def test_manifest_lists_all_vectors(manifest, vectors):
    assert len(manifest["vector_ids"]) == len(vectors)
    loaded_ids = {v["vector_id"] for v in vectors}
    assert loaded_ids == set(manifest["vector_ids"])


@pytest.mark.parametrize("vector_id", [
    "cross-ext-v0-escrow-double-release-001",
    "cross-ext-v0-refund-replay-001",
    "cross-ext-v0-dispute-amplification-001",
    "cross-ext-v0-synthetic-artifact-dispute-001",
    "cross-ext-v0-mediator-grooming-001",
])
def test_vector_jws_verifies(vector_id: str):
    from harness.jws import load_vector

    vector = load_vector(VECTORS_DIR, vector_id)
    ok, detail = verify_vector_jws(vector)
    assert ok, f"{vector_id}: {detail}"


@pytest.mark.parametrize("vector_id", [
    "cross-ext-v0-escrow-double-release-001",
    "cross-ext-v0-refund-replay-001",
    "cross-ext-v0-dispute-amplification-001",
    "cross-ext-v0-synthetic-artifact-dispute-001",
    "cross-ext-v0-mediator-grooming-001",
])
def test_vector_shape(vector_id: str):
    from harness.jws import load_vector

    vector = load_vector(VECTORS_DIR, vector_id)
    errors = validate_vector_shape(vector)
    assert not errors, f"{vector_id}: {errors}"


def test_settlement_vectors_are_a2a_se_kind(vectors):
    settlement_ids = {
        "cross-ext-v0-escrow-double-release-001",
        "cross-ext-v0-refund-replay-001",
    }
    for vector in vectors:
        if vector["vector_id"] in settlement_ids:
            assert vector["input_envelope"]["settlement_kind"] == "a2a-se"
