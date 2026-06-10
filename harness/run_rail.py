"""Optional HTTP runner for settlement vectors against a live rail.

Usage:
    export RAIL_BASE_URL=https://exchange.a2a-settlement.org/api/v1
    export RAIL_REQUESTER_API_KEY=...
    python -m harness.run_rail --vectors vectors/v0

Exits 0 if all runnable vectors pass; skips vectors without a runner mapping.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

from harness.jws import load_all_vectors, load_manifest

SETTLEMENT_RUNNERS = {
    "escrow_double_release",
    "refund_replay",
}


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def run_escrow_double_release(client: httpx.Client, api_key: str) -> tuple[bool, str]:
    """Create escrow, release twice; second release must be blocked."""
    reg = client.post(
        "/accounts/register",
        json={
            "bot_name": "ConfProvider",
            "developer_id": "conf",
            "developer_name": "Conf",
            "contact_email": "conf@test.dev",
            "skills": ["conformance"],
        },
    )
    if reg.status_code != 200:
        return False, f"provider register failed: {reg.status_code} {reg.text}"
    provider_id = reg.json()["account"]["id"]
    provider_key = reg.json()["api_key"]

    req = client.post(
        "/accounts/register",
        json={
            "bot_name": "ConfRequester",
            "developer_id": "conf",
            "developer_name": "Conf",
            "contact_email": "conf2@test.dev",
            "skills": ["conformance"],
        },
    )
    if req.status_code != 200:
        return False, f"requester register failed: {req.status_code} {req.text}"
    requester_key = req.json()["api_key"]

    escrow = client.post(
        "/exchange/escrow",
        headers=_headers(requester_key),
        json={"provider_id": provider_id, "amount": 10},
    )
    if escrow.status_code != 200:
        return False, f"escrow create failed: {escrow.status_code} {escrow.text}"
    escrow_id = escrow.json()["escrow_id"]

    first = client.post(
        "/exchange/release",
        headers=_headers(requester_key),
        json={"escrow_id": escrow_id},
    )
    if first.status_code != 200:
        return False, f"first release failed: {first.status_code} {first.text}"

    second = client.post(
        "/exchange/release",
        headers=_headers(requester_key),
        json={"escrow_id": escrow_id},
    )
    if second.status_code != 400:
        return False, f"expected 400 on double release, got {second.status_code}"
    if "already released" not in second.json().get("detail", "").lower():
        return False, f"unexpected detail: {second.json()}"
    return True, "PASS"


def run_refund_replay(client: httpx.Client, api_key: str) -> tuple[bool, str]:
    """Refund terminal escrow twice; replay must be blocked."""
    reg = client.post(
        "/accounts/register",
        json={
            "bot_name": "ConfProvider2",
            "developer_id": "conf",
            "developer_name": "Conf",
            "contact_email": "conf3@test.dev",
            "skills": ["conformance"],
        },
    )
    if reg.status_code != 200:
        return False, f"provider register failed: {reg.status_code}"
    provider_id = reg.json()["account"]["id"]

    req = client.post(
        "/accounts/register",
        json={
            "bot_name": "ConfRequester2",
            "developer_id": "conf",
            "developer_name": "Conf",
            "contact_email": "conf4@test.dev",
            "skills": ["conformance"],
        },
    )
    if req.status_code != 200:
        return False, f"requester register failed: {req.status_code}"
    requester_key = req.json()["api_key"]

    escrow = client.post(
        "/exchange/escrow",
        headers=_headers(requester_key),
        json={"provider_id": provider_id, "amount": 10},
    )
    escrow_id = escrow.json()["escrow_id"]

    client.post(
        "/exchange/refund",
        headers=_headers(requester_key),
        json={"escrow_id": escrow_id},
    )
    replay = client.post(
        "/exchange/refund",
        headers=_headers(requester_key),
        json={"escrow_id": escrow_id},
    )
    if replay.status_code != 400:
        return False, f"expected 400 on refund replay, got {replay.status_code}"
    if "already refunded" not in replay.json().get("detail", "").lower():
        return False, f"unexpected detail: {replay.json()}"
    return True, "PASS"


RUNNERS = {
    "escrow_double_release": run_escrow_double_release,
    "refund_replay": run_refund_replay,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run settlement vectors against a live rail")
    parser.add_argument(
        "--vectors",
        type=Path,
        default=Path("vectors/v0"),
        help="Path to vector directory",
    )
    args = parser.parse_args(argv)

    base_url = os.environ.get("RAIL_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("RAIL_REQUESTER_API_KEY", "")
    if not base_url:
        print("RAIL_BASE_URL not set — nothing to run", file=sys.stderr)
        return 1

    manifest = load_manifest(args.vectors)
    vectors = load_all_vectors(args.vectors)
    failures: list[str] = []
    skipped = 0

    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for vector in vectors:
            attack = vector["attack_class"]
            if attack not in SETTLEMENT_RUNNERS:
                print(f"SKIP {vector['vector_id']} ({attack}) — no HTTP runner")
                skipped += 1
                continue
            runner = RUNNERS[attack]
            ok, detail = runner(client, api_key)
            status = "PASS" if ok else "FAIL"
            print(f"{status} {vector['vector_id']}: {detail}")
            if not ok:
                failures.append(vector["vector_id"])

    print(f"\nartefact={manifest['artefact_id']} ran={len(vectors) - skipped} skipped={skipped}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
