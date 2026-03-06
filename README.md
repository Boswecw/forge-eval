# Forge Eval

Deterministic, schema-validated, fail-closed evaluation subsystem for the Forge ecosystem.

## Documentation Contract

- **Repo type:** Standalone CLI subsystem
- **Authority boundary:** Deterministic evaluation of sibling repositories and local artifact emission; not governance authority and not the durable truth store
- **Deep reference:** `doc/system/_index.md`, `doc/feSYSTEM.md`, `../../docs/canonical/ecosystem_canonical.md`
- **README role:** CLI entrypoint overview
- **Truth note:** Pack listings and emitted-artifact inventory in this README describe the current implementation snapshot unless explicitly marked as canonical invariants

Forge Eval is an **independent repository** within the local Forge ecosystem workspace. It evaluates other independent sibling repositories as target repos. It is not a child subsystem of DataForge, NeuroForge, or forge-smithy.

Current implemented packs:

* **Pack A**: Python scaffold + CLI + orchestration
* **Pack B**: Rust `forge-evidence` canonical JSON / hashing / hashchain
* **Pack C**: Python wrapper around Rust evidence binary
* **Pack D**: Strict JSON schemas
* **Pack E**: Structural risk heatmap stage
* **Pack F**: Context slice extraction stage
* **Pack G**: Deterministic reviewer execution + normalized findings + defect identity
* **Pack H**: Telemetry matrix + reviewer health + tri-state outcomes + `k_eff`
* **Pack I**: Occupancy snapshot + deterministic conservative `psi_post`
* **Pack J**: Hidden-defect capture estimate + Chao1/ICE + conservative selected hidden burden

## Repo role

Forge Eval implements the deterministic eval pipeline foundation:

```text
risk -> context slices -> reviewer findings -> telemetry matrix -> occupancy snapshot -> capture estimate
```

Core invariants:

* deterministic outputs
* schema-locked artifacts
* fail-closed behavior
* fixed stage order
* byte-stable repeated runs on identical inputs

## Build Rust evidence binary

```bash
cd rust/forge-evidence
cargo build --offline
```

Binary path after build:

```text
rust/forge-evidence/target/debug/forge-evidence
```

Use `FORGE_EVIDENCE_BIN` to point the Python wrapper to the binary if it is not on `PATH`.

## Install Python package

```bash
pip install -e .
```

## Run pipeline

```bash
forge-eval run --repo /path/to/target-repo --base <base> --head <head> --config config.yaml --out artifacts/
```

## Validate artifacts

```bash
forge-eval validate --artifacts artifacts/
```

## Current emitted artifacts

Depending on enabled stages, Forge Eval currently emits:

* `config.resolved.json`
* `risk_heatmap.json`
* `context_slices.json`
* `review_findings.json`
* `telemetry_matrix.json`
* `occupancy_snapshot.json`
* `capture_estimate.json`

## Current fixed stage order

```text
risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate
```

## Determinism notes

* JSON artifacts are written with sorted keys and compact separators.
* Stage order is fixed and deterministic.
* Context extraction uses head-version content with deterministic diff/range processing.
* Cap overflows fail closed with explicit error behavior.
* Reviewer failures are fail-closed by default (`reviewer_failure_policy=fail_stage`).
* `defect_key` is canonical across reviewers for matching identity fields.
* Cross-reviewer findings coalesce in telemetry; same-reviewer duplicates and metadata collisions fail closed.
* Telemetry uses strict tri-state semantics: `1`, `0`, or `null`.
* Failed, skipped, or inapplicable reviewers do not count as clean misses.
* Occupancy uses conservative posterior semantics: usable misses suppress, `null` adds uncertainty.
* Hidden-defect estimation uses deterministic Chao1/ICE outputs with conservative `max_hidden` selection.

## Status

Forge Eval Packs A–J are implemented in the current repo state.

A–F were operationally verified on a real target repo. Pack G was integrated and smoke-validated. Pack H telemetry semantics are covered by unit and integration tests, including fail-closed and tri-state behavior. Pack I occupancy semantics are covered by unit/integration tests and real local smoke runs. Pack J hidden-defect estimation is covered by stage tests, integration determinism, and real local smoke runs.

## Important note on Rust evidence

The Rust evidence subsystem is implemented and wrapped, but live runtime activation in the main evaluation path is still a follow-on hardening item unless explicitly wired into emitted artifact handling.
