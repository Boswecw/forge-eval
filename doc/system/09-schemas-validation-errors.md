# §9 - Schemas, Validation, and Error Model

## Schema Set (Pack D)

Implemented schema files:

- `risk_heatmap.schema.json`
- `context_slices.schema.json`
- `review_findings.schema.json`
- `telemetry_matrix.schema.json`
- `occupancy_snapshot.schema.json`
- `capture_estimate.schema.json`
- `calibration_report.schema.json`
- `hazard_map.schema.json`
- `merge_decision.schema.json`
- `evidence_bundle.schema.json`

All schemas are Draft 2020-12 and strict at root (`additionalProperties: false`).

## Validation Behavior

- Schema loader fails on unknown artifact kind or missing schema files.
- Artifact validator enumerates all violations and reports machine-readable paths.
- `validate` command enforces required artifact presence based on enabled stage list in `config.resolved.json`.

## Structured Error Classes

- `ForgeEvalError` (base)
- `ConfigError`
- `ValidationError`
- `StageError`
- `EvidenceCliError`
- `GitError`

Each error serializes to:

- `code`
- `message`
- `stage`
- `details`

CLI exits non-zero on any structured error.
