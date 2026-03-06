# Forge Eval System Documentation

> BDS Documentation Protocol v1.0 - modular reference for deterministic Packs A-F

| Part | File | Contents |
|------|------|----------|
| §1 | [01-overview-philosophy.md](01-overview-philosophy.md) | Scope, governance principles, invariants |
| §2 | [02-architecture.md](02-architecture.md) | Python/Rust architecture and execution flow |
| §3 | [03-tech-stack.md](03-tech-stack.md) | Runtime dependencies and toolchain |
| §4 | [04-project-structure.md](04-project-structure.md) | Repository layout and module responsibilities |
| §5 | [05-cli-config-artifacts.md](05-cli-config-artifacts.md) | CLI contracts, config normalization, artifact writing |
| §6 | [06-evidence-subsystem.md](06-evidence-subsystem.md) | Rust evidence binary and Python wrapper contract |
| §7 | [07-risk-heatmap-stage.md](07-risk-heatmap-stage.md) | Pack E deterministic structural risk scoring |
| §8 | [08-context-slices-stage.md](08-context-slices-stage.md) | Pack F deterministic context slice extraction |
| §9 | [09-schemas-validation-errors.md](09-schemas-validation-errors.md) | Strict schemas, validation, structured failures |
| §10 | [10-testing-determinism.md](10-testing-determinism.md) | Test matrix and repeatability checks |
| §11 | [11-handover-runbook.md](11-handover-runbook.md) | Build/run/validate runbook and constraints |

## Quick Assembly

```bash
bash doc/system/BUILD.sh   # Assembles all parts into doc/feSYSTEM.md
```

*Last updated: 2026-03-05*

---

# §1 - Overview and Philosophy

## Purpose

`forge-eval` is a deterministic, fail-closed evaluation foundation implementing Packs A-F:

- Pack A: Python scaffold, CLI, orchestration, error model.
- Pack B: Rust evidence binary (`forge-evidence`) for canonical JSON/hash/hashchain primitives.
- Pack C: Python subprocess wrapper around the Rust binary.
- Pack D: Strict JSON schema contracts for current and future artifacts.
- Pack E: Structural risk heatmap generation from git-derived features.
- Pack F: Context slice extraction from git diff hunks.

## Current Pipeline Boundary

Implemented path:

`config -> risk_heatmap -> context_slices`

Planned downstream (not implemented here): reviewers, telemetry, occupancy, hidden defect estimates, hazard, merge decision, bundle assembly.

## Governing Principles

1. Deterministic output for identical repo/config/base/head inputs.
2. Fail closed on ambiguity, unsupported state, and cap overflow.
3. Strict schema contracts with `additionalProperties: false` on primary objects.
4. No silent truncation; explicit policy-driven behavior only.
5. Stable artifact serialization on Python side (`sort_keys=True`, compact JSON).
6. Evidence-grade canonicalization delegated to Rust tooling.

---

# §2 - Architecture

## High-Level Components

1. CLI layer (`src/forge_eval/cli.py`)
2. Config normalization (`src/forge_eval/config.py`)
3. Stage orchestration (`src/forge_eval/stage_runner.py`)
4. Stage services (`src/forge_eval/stages/*`, `src/forge_eval/services/*`)
5. Schema loading/validation (`src/forge_eval/validation/*`)
6. Evidence subsystem (Rust binary under `rust/forge-evidence`, Python wrapper in `evidence_cli.py`)

## Runtime Flow (`forge-eval run`)

1. Parse CLI args.
2. Load + normalize config (`JSON` or `YAML`).
3. Resolve base/head commits (`git rev-parse`).
4. Compute deterministic `run_id = sha256(repo_abs_path::base_commit::head_commit)[:16]`.
5. Write `config.resolved.json`.
6. Execute stages in fixed order:
   - `risk_heatmap`
   - `context_slices`
7. Validate each stage artifact against strict schema.
8. Write schema-valid artifacts to output directory.

## Runtime Flow (`forge-eval validate`)

1. Load all known schemas.
2. Read `config.resolved.json` when present.
3. Derive required artifacts from enabled stages.
4. Fail if required artifacts are missing.
5. Validate any present known artifact kind.

## Python/Rust Boundary

- Python owns orchestration and stage logic.
- Rust owns deterministic evidence primitives.
- Cross-language integration is subprocess-based only.
- No Python fallback implementation for evidence primitives.

---

# §3 - Tech Stack

## Python

- Python `>=3.12`
- `jsonschema` (Draft 2020-12 validation)
- `PyYAML` (config loading)
- stdlib for subprocess, JSON, path, hashing, regex, argparse

## Rust (`forge-evidence`)

- stable Rust toolchain
- `serde`, `serde_json`
- `sha2`, `hex`
- `clap`
- `anyhow`

## Git Interface

Git is invoked through subprocess with explicit commands:

- `git rev-parse`
- `git diff --name-status --find-renames`
- `git diff --numstat`
- `git diff --no-color --unified=0`
- `git show <ref:path>`
- `git ls-files`

## Build and Test Tooling

- `cargo build --offline`, `cargo test --offline`
- `pytest` for Python unit/integration coverage

---

# §4 - Project Structure

## Repository Tree (Core)

```text
repo/
  pyproject.toml
  README.md
  src/forge_eval/
    cli.py
    config.py
    stage_runner.py
    errors.py
    evidence_cli.py
    stages/
      risk_heatmap.py
      context_slices.py
    services/
      git_diff.py
      risk_analysis.py
      range_ops.py
      slice_extractor.py
    schemas/
      *.schema.json
    validation/
      schema_loader.py
      validate_artifact.py
  tests/
    test_cli.py
    test_config.py
    test_evidence_cli.py
    test_risk_heatmap.py
    test_range_ops.py
    test_slice_extractor.py
    test_context_slices_stage.py
    test_schemas.py
    integration/
      test_risk_heatmap_repo.py
      test_context_slices_repo.py
      golden/
        context_single_hunk.json
        context_distant_hunks.json
  rust/forge-evidence/
    src/
      main.rs
      canonical.rs
      hash.rs
      artifact_id.rs
      chain.rs
    tests/
      integration_cli.rs
```

## Responsibility Split

- `stages/`: stage entrypoints that produce artifact objects.
- `services/`: deterministic helpers (git access, scoring, range math, extraction).
- `validation/`: schema lookup + JSON-schema enforcement.
- `schemas/`: locked contracts for implemented and future artifacts.
- `rust/forge-evidence/`: canonical evidence primitives.

---

# §5 - CLI, Config, and Artifacts

## CLI Commands

```bash
forge-eval run --repo /path/to/repo --base <base> --head <head> --config config.yaml --out artifacts/
forge-eval validate --artifacts artifacts/
```

## Config Loading and Normalization

- Accepted formats: `.json`, `.yaml`, `.yml`
- Unknown keys are rejected.
- Stage list is validated against known stage set.
- Risk weights are normalized to a deterministic unit sum.
- File-extension and excluded-path lists are normalized and sorted.

Default stage order and enabled set:

1. `risk_heatmap`
2. `context_slices`

## Pack F Config Keys (Current)

- `context_radius_lines` (int, >=0)
- `merge_gap_lines` (int, >=0)
- `max_slices_per_target` (int, >=1)
- `max_lines_per_slice` (int, >=1)
- `max_total_lines` (int, >=1)
- `fail_on_slice_truncation` (bool)
- `include_file_extensions` (normalized unique list)
- `exclude_paths` (normalized unique list, trailing `/`)
- `binary_file_policy` (`fail` or `ignore`)

## Artifacts Written by `run`

- `config.resolved.json`
- `risk_heatmap.json` (if enabled)
- `context_slices.json` (if enabled)

All Python-written artifacts use deterministic JSON encoding:

- sorted keys
- compact separators
- single trailing newline

---

# §6 - Evidence Subsystem

## Rust Binary: `forge-evidence`

CLI commands:

```bash
forge-evidence canonicalize <input.json>
forge-evidence sha256 <input-file>
forge-evidence artifact-id <input.json> --kind <artifact-kind>
forge-evidence hashchain <directory-or-manifest>
```

## Deterministic Policies

- Canonical JSON:
  - sorted object keys
  - compact output (no pretty print)
  - UTF-8 bytes
  - arrays preserve order
  - non-finite floats rejected
- SHA-256 output as lowercase 64-char hex.
- Artifact ID: `sha256(kind + NUL + canonical_json_bytes)`.
- Hashchain seed: `sha256("forge-evidence-chain-v1")`, then chained left-to-right.

## Python Wrapper: `evidence_cli.py`

Wrapper behavior is fail-closed:

- explicit subprocess calls only
- non-zero exit -> `EvidenceCliError`
- parse and validate output shape (length, JSON object)
- no fallback to Python-native canonicalization/hashing

Environment override:

- `FORGE_EVIDENCE_BIN` can point to a non-PATH binary.

---

# §7 - Pack E: Risk Heatmap Stage

## Stage Contract

Input:

- repo path
- base ref
- head ref
- normalized config

Output:

- `risk_heatmap.json` (schema kind: `risk_heatmap`)

## Feature Construction

Per changed, in-scope file:

1. Churn from `git diff --numstat` (`added + deleted`).
2. Change magnitude via `log1p(churn)`.
3. Lightweight connectivity centrality from import/use/require relations across tracked files.
4. Optional path weighting using longest matching configured prefix.

## Scoring

- Each raw feature vector is normalized to `[0,1]` deterministically.
- Raw risk:

`w_churn * churn_norm + w_centrality * centrality + w_change_magnitude * magnitude_norm`

- Path weight multiplier applied after weighted sum.
- Final `risk_score` is normalized to `[0,1]` across targets.
- Targets are sorted by `file_path`.

## Provenance

- `algorithm: structural_risk_v1`
- `deterministic: true`

---

# §8 - Pack F: Context Slices Stage

## Stage Contract

Input:

- repo path
- base ref
- head ref
- normalized config
- optional target subset (wired from risk stage targets)

Output:

- `context_slices.json` (schema kind: `context_slices`)

## Deterministic Extraction Procedure

For each changed target file (non-deleted, extension-allowed, non-excluded):

1. Parse unified diff hunks (`--unified=0`) into changed ranges in head-line coordinates.
2. Expand each range by `context_radius_lines`.
3. Clamp expanded ranges to `[1, file_line_count]`.
4. Merge overlap/adjacency using `merge_gap_lines` (left-to-right after sort).
5. Split oversized merged ranges by `max_lines_per_slice`.
6. Build stable slice objects (`slice_id = file_path:start:end`) from head file content.
7. Sort slices by `(file_path, start_line, end_line)`.
8. Enforce `max_total_lines` globally.

## Cap and Failure Policy

- If binary file is changed and `binary_file_policy=fail`, stage fails closed.
- If `max_slices_per_target` is exceeded and `fail_on_slice_truncation=true`, stage fails closed.
- If `max_total_lines` is exceeded, stage fails closed.
- No silent line dropping.

## v1 Decisions Locked in Code

- Head-version content is the extraction source.
- Deleted files are excluded.
- Rename handling follows post-rename path from git diff parsing.
- Provenance marks source as `git_diff_head_version`.

---

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

---

# §10 - Testing and Determinism

## Python Test Coverage (Packs A-F)

- CLI smoke + failure behavior
- config normalization and rejection cases
- schema loader + schema positive/negative validation
- risk stage logic/unit + integration on temporary git repos
- range operations and hunk parsing
- context-slice extraction unit + integration + cap-overflow behavior
- golden-file checks for context slices
- repeatability checks using byte-equality of serialized artifacts

## Rust Test Coverage (Pack B)

- canonicalization key-order invariance
- canonicalization idempotence
- SHA-256 known vector
- artifact-id stability
- hashchain stability

## Determinism Controls in Code

- explicit stage order constant
- sorted file/range/artifact iteration
- stable JSON serialization
- no runtime clock fields in primary stage artifacts
- fail-closed cap handling instead of opportunistic truncation

---

# §11 - Handover and Runbook

## Build and Install

```bash
cd /home/charlie/Forge/ecosystem/forge-eval/repo

# Rust evidence binary
cd rust/forge-evidence
cargo build --offline

# Python package
cd ../../
pip install -e .
```

If the evidence binary is not on `PATH`:

```bash
export FORGE_EVIDENCE_BIN=/abs/path/to/rust/forge-evidence/target/debug/forge-evidence
```

## Execute Pipeline

```bash
forge-eval run \
  --repo /abs/path/to/target/repo \
  --base <base-ref> \
  --head <head-ref> \
  --config /abs/path/to/config.yaml \
  --out /abs/path/to/artifacts
```

## Validate Artifacts

```bash
forge-eval validate --artifacts /abs/path/to/artifacts
```

## Deterministic Acceptance Checks

1. Run the same `forge-eval run` command twice on identical inputs.
2. Compare produced artifacts byte-for-byte.
3. Run Python and Rust tests before merge.

## Guardrails for Next Packs

1. Keep schema-first contracts; add new artifact kinds in `schemas/` before stage logic.
2. Preserve fail-closed defaults unless governance text explicitly allows deterministic reduction.
3. Keep evidence primitives centralized in Rust; do not duplicate them in Python.
4. Do not add reviewer/telemetry/occupancy logic into Pack F modules.

---
