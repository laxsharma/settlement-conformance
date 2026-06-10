# A2A-SE conformance results

Rail: [a2a-settlement exchange](https://exchange.a2a-settlement.org)  
Artefact: cross-extension v0 (schema_version 1.1, revised 2026-06-01)

## Summary

| Vector | Expected | Result |
|--------|----------|--------|
| escrow_double_release | BLOCK | **PASS** |
| refund_replay | BLOCK | **PASS** |
| dispute_amplification | BLOCK | N/A |
| synthetic_artifact_dispute | REVIEW | N/A |
| mediator_grooming | REVIEW | N/A |

2 PASS, 3 N/A. Partial results are intentional — we have not built every gate in v0 yet.

## How we ran this

In-process pytest against the exchange app (`tests/conformance/test_cross_extension_v0.py` in the a2a-settlement repo). Same code path as production deploy at commit `8cdcae4`. No state-mutating calls against the live rail.

```bash
cd a2a-settlement
python -m pytest tests/conformance/test_cross_extension_v0.py -v
```

## Adapter notes

- `expected_error_code` strings from the AlgoVoi envelope are not emitted literally. We match on HTTP 400 + `detail` substring.
- Settlement vectors (`settlement_kind: a2a-se`) are the subset this rail owns. Dispute-amplification and mediator-grooming need separate gates or mediator integration.

Full write-up: [conformance-results.md](https://github.com/a2a-settlement/a2a-settlement/blob/main/docs/conformance-results.md)
