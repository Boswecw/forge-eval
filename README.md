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

Offline local dev note:

- `pyproject.toml` currently requires `jsonschema>=4.10.3` and `PyYAML>=6.0.1`.
- In a networked environment, plain `pip install -e .` is the normal path.
- In an offline environment where those dependencies are already present from system packages or a pre-provisioned venv, use:

```bash
pip install --no-build-isolation -e .
```

This avoids pip's isolated build environment trying to download build requirements.

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

The current A–J runtime path has been verified on a real local target repo:

- emitted artifact set: `config.resolved.json`, `risk_heatmap.json`, `context_slices.json`, `review_findings.json`, `telemetry_matrix.json`, `occupancy_snapshot.json`, `capture_estimate.json`
- `forge-eval validate` passed on the emitted artifacts
- repeated identical runs were byte-identical across all primary artifacts
- fail-closed probes were confirmed for config, validation, reviewer-failure, and cross-artifact mismatch cases

Verification report:

- `reports/forge_eval_a_to_j_verification_report_rev1.md`

Downstream packs such as hazard, merge decision, and evidence bundle assembly are still not implemented.

## Important note on Rust evidence

The Rust evidence subsystem is implemented, callable, and tested, but it is not part of the main A–J stage pipeline in the current runtime. It remains a verified helper boundary until a later slice explicitly wires evidence primitives into emitted artifact handling or downstream bundle assembly.
