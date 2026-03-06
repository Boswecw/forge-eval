# §15 - Pack J: Capture Estimate Stage

## Stage Contract

Input:

- `telemetry_matrix` artifact (required)
- `occupancy_snapshot` artifact (required)
- normalized capture-estimate config (required)

Output:

- `capture_estimate.json` (schema kind: `capture_estimate`)

## Execution Model

1. Validate telemetry and occupancy artifacts and enforce `run_id` / commit alignment.
2. Cross-check defect sets and per-row observation counts across Pack H and Pack I.
3. Build deterministic incidence counts and frequency-of-frequencies histogram.
4. Compute bias-corrected Chao1 hidden estimate.
5. Compute ICE hidden estimate with explicit low-information fallback.
6. Select conservative hidden burden with `max_hidden`.
7. Emit schema-valid counts, estimator details, summary flags, and provenance.

## Core Semantics

- only positive usable observations contribute to incidence counts.
- `null` is not converted into sampling effort.
- singleton-heavy rows increase hidden-defect concern.
- sparse-data guardrails stay visible in the artifact.

## Model Rules (v1)

- inclusion policy: `include_all`
- Chao1 variant: `bias_corrected`
- ICE rare threshold: config-locked `ice_rare_threshold` (default `10`)
- selection policy: `max_hidden`

When ICE coverage collapses or rare-incidence support is too weak, Pack J uses an explicit fallback path instead of dividing by zero or silently returning zero hidden defects.

## Fail-Closed Behavior

- telemetry/occupancy defect-set mismatch -> stage failure.
- cross-artifact count mismatch (`observed_by`, `missed_by`, `null_by`, `k_eff_defect`) -> stage failure.
- included row with zero positive incidence -> stage failure.
- unsupported inclusion or selection policy -> stage failure.
- invalid histogram keys/counts or negative estimator outputs -> stage failure.
- schema validation failure -> run failure.

## Determinism Notes

- defect rows are counted in canonical `defect_key` order.
- histogram keys are emitted as sorted decimal strings.
- estimator rounding is fixed by `capture_round_digits`.
- selected hidden estimate is explicit and conservative.
