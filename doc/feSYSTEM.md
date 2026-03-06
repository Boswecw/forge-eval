# Forge Eval System Documentation

**Document version:** 1.1 (2026-03-06) — Implemented Pack K hazard stage and normalized to Forge Documentation Protocol v1
**Protocol:** Forge Documentation Protocol v1

This `doc/system/` tree uses explicit truth classes:
- Canonical facts define Forge Eval's CLI boundary, stage order, artifact contracts, and fail-closed doctrine.
- Snapshot facts define audit-derived counts such as tests, reviewer inventories, or implementation surface metrics.

Repo deviation:
- Forge Eval is a standalone CLI subsystem with local artifacts, not a resident HTTP service in the current runtime.

Assembly contract:
- Command: `bash doc/system/BUILD.sh`
- Output: `doc/feSYSTEM.md`

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
| §12 | [12-reviewer-execution-stage.md](12-reviewer-execution-stage.md) | Pack G deterministic reviewer execution and findings |
| §13 | [13-telemetry-matrix-stage.md](13-telemetry-matrix-stage.md) | Pack H deterministic telemetry matrix and conservative `k_eff` |
| §14 | [14-occupancy-snapshot-stage.md](14-occupancy-snapshot-stage.md) | Pack I deterministic occupancy posterior (`psi_post`) |
| §15 | [15-capture-estimate-stage.md](15-capture-estimate-stage.md) | Pack J deterministic hidden-defect estimation via Chao1 and ICE |
| §16 | [16-hazard-map-stage.md](16-hazard-map-stage.md) | Pack K deterministic hazard mapping from risk, telemetry, occupancy, and capture pressure |

## Quick Assembly

```bash
bash doc/system/BUILD.sh   # Assembles all parts into doc/feSYSTEM.md
```

*Last updated: 2026-03-06*

---

# §1 - Overview and Philosophy

## Purpose

`forge-eval` is a deterministic, fail-closed evaluation foundation implementing Packs A-K:

- Pack A: Python scaffold, CLI, orchestration, error model.
- Pack B: Rust evidence binary (`forge-evidence`) for canonical JSON/hash/hashchain primitives.
- Pack C: Python subprocess wrapper around the Rust binary.
- Pack D: Strict JSON schema contracts for current and future artifacts.
- Pack E: Structural risk heatmap generation from git-derived features.
- Pack F: Context slice extraction from git diff hunks.
- Pack G: Deterministic reviewer execution, normalized findings, stable defect identity.
- Pack H: Deterministic telemetry matrix with reviewer-truth preservation and conservative `k_eff`.
- Pack I: Deterministic occupancy posterior estimation (`psi_post`) with conservative null handling.
- Pack J: Deterministic hidden-defect estimation (`capture_estimate`) with Chao1/ICE and conservative selection.
- Pack K: Deterministic hazard assessment (`hazard_map`) combining structural risk, observed burden, residual occupancy concern, and hidden-defect pressure.

## Current Pipeline Boundary

Implemented path:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map`

Planned downstream (not implemented here): merge decision, bundle assembly.

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
6. Reviewer subsystem (`src/forge_eval/reviewers/*` + finding normalization/identity services)
7. Telemetry subsystem (`services/reviewer_health.py`, `services/applicability.py`, `services/telemetry_builder.py`, `services/k_eff.py`)
8. Occupancy subsystem (`services/occupancy_priors.py`, `services/occupancy_model.py`, `services/occupancy_rows.py`, `services/occupancy_summary.py`)
9. Hidden-defect subsystem (`services/capture_counts.py`, `services/chao1.py`, `services/ice.py`, `services/capture_selection.py`, `services/capture_summary.py`)
10. Hazard subsystem (`services/hazard_model.py`, `services/hazard_rows.py`, `services/hazard_summary.py`)
11. Evidence subsystem (Rust binary under `rust/forge-evidence`, Python wrapper in `evidence_cli.py`)

## Runtime Flow (`forge-eval run`)

1. Parse CLI args.
2. Load + normalize config (`JSON` or `YAML`).
3. Resolve base/head commits (`git rev-parse`).
4. Compute deterministic `run_id = sha256(repo_abs_path::base_commit::head_commit)[:16]`.
5. Write `config.resolved.json`.
6. Execute stages in fixed order:
   - `risk_heatmap`
   - `context_slices`
   - `review_findings`
   - `telemetry_matrix`
   - `occupancy_snapshot`
   - `capture_estimate`
   - `hazard_map`
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
- Current A-K runtime boundary: the stage pipeline does not invoke `evidence_cli.py`; Rust evidence remains a verified helper subsystem until a later slice wires it into emitted artifact handling.

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
    reviewers/
      base.py
      registry.py
      adapters.py
      changed_lines.py
      structural_risk.py
      documentation_consistency.py
    stages/
      risk_heatmap.py
      context_slices.py
      reviewer_execution.py
      telemetry_matrix.py
      occupancy_snapshot.py
      capture_estimate.py
      hazard_map.py
    services/
      git_diff.py
      risk_analysis.py
      range_ops.py
      slice_extractor.py
      finding_normalizer.py
      defect_identity.py
      reviewer_health.py
      applicability.py
      telemetry_builder.py
      k_eff.py
      occupancy_priors.py
      occupancy_model.py
      occupancy_rows.py
      occupancy_summary.py
      capture_counts.py
      chao1.py
      ice.py
      capture_selection.py
      capture_summary.py
      hazard_model.py
      hazard_rows.py
      hazard_summary.py
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
    test_reviewer_execution_stage.py
    test_telemetry_matrix_stage.py
    test_occupancy_snapshot_stage.py
    test_capture_estimate_stage.py
    test_hazard_map_stage.py
    test_finding_normalizer.py
    test_defect_identity.py
    test_schemas.py
    integration/
      test_risk_heatmap_repo.py
      test_context_slices_repo.py
      test_review_findings_repo.py
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
- `services/`: deterministic helpers (git access, scoring, range math, extraction, finding normalization, defect identity, reviewer health/applicability, telemetry matrix building, occupancy prior/posterior computation, hidden-defect counting/estimation).
- `reviewers/`: deterministic reviewer adapters and execution wrappers.
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
3. `review_findings`
4. `telemetry_matrix`
5. `occupancy_snapshot`
6. `capture_estimate`
7. `hazard_map`

Stage dependency constraints:

- `context_slices` requires `risk_heatmap`
- `review_findings` requires `context_slices`
- `telemetry_matrix` requires `review_findings`
- `occupancy_snapshot` requires `telemetry_matrix`
- `capture_estimate` requires `occupancy_snapshot`
- `hazard_map` requires `capture_estimate`

## Pack F/G/H/I/J/K Config Keys (Current)

- `context_radius_lines` (int, >=0)
- `merge_gap_lines` (int, >=0)
- `max_slices_per_target` (int, >=1)
- `max_lines_per_slice` (int, >=1)
- `max_total_lines` (int, >=1)
- `fail_on_slice_truncation` (bool)
- `include_file_extensions` (normalized unique list)
- `exclude_paths` (normalized unique list, trailing `/`)
- `binary_file_policy` (`fail` or `ignore`)
- `reviewer_failure_policy` (`fail_stage` or `record_and_continue`)
- `reviewers` (deterministically sorted reviewer config objects)
- `telemetry_applicability_mode` (`reviewer_kind_scope_v1`)
- `telemetry_k_eff_mode` (`global_min_per_defect`)
- `occupancy_model_version` (`occupancy_rev1`)
- `occupancy_prior_base` (float in `[0,1]`)
- `occupancy_support_uplift` (float in `[0,1]`)
- `occupancy_detection_assumption` (float in `[0,1]`)
- `occupancy_miss_penalty_strength` (float in `[0,1]`)
- `occupancy_null_uncertainty_boost` (float in `[0,1]`)
- `occupancy_round_digits` (int in `[0,12]`)
- `capture_inclusion_policy` (`include_all`)
- `capture_selection_policy` (`max_hidden`)
- `ice_rare_threshold` (int, >=1)
- `capture_round_digits` (int in `[0,12]`)
- `hazard_model_version` (`hazard_rev1`)
- `hazard_round_digits` (int in `[0,12]`)
- `hazard_hidden_uplift_strength` (float in `[0,1]`)
- `hazard_structural_risk_strength` (float in `[0,1]`)
- `hazard_occupancy_strength` (float in `[0,1]`)
- `hazard_support_uplift_strength` (float in `[0,1]`)
- `hazard_uncertainty_boost` (float in `[0,1]`)
- `hazard_blocking_threshold` (float in `[0,1]`)

## Artifacts Written by `run`

- `config.resolved.json`
- `risk_heatmap.json` (if enabled)
- `context_slices.json` (if enabled)
- `review_findings.json` (if enabled)
- `telemetry_matrix.json` (if enabled)
- `occupancy_snapshot.json` (if enabled)
- `capture_estimate.json` (if enabled)
- `hazard_map.json` (if enabled)

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

## Current Runtime Posture

- `forge-evidence` and `evidence_cli.py` are implemented, directly callable, and covered by Rust/Python tests.
- Current A-K pipeline stages do not invoke the evidence wrapper during `forge-eval run` or `forge-eval validate`.
- This is the active boundary by design in the current repo state:
  - evidence primitives are available
  - mainline artifact emission remains Python-owned
  - downstream evidence-bundle assembly remains out of scope

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

## Schema Set (Pack D + Pack G/H/I/J/K Extensions)

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

`review_findings.schema.json` enforces Pack G layout:

- `artifact_version`, `kind`, `run`
- reviewer execution summaries with status enum: `ok | failed | skipped`
- normalized findings with strict severity/category enums
- required deterministic `defect_key` format (`dfk_<sha256hex>`)
- summary counters and provenance inputs/failure policy fields

`telemetry_matrix.schema.json` enforces Pack H layout:

- `artifact_version`, `kind`, `run`, `reviewers`, `defects`, `matrix`, `summary`, `provenance`
- tri-state matrix cells limited to `1 | 0 | null`
- reviewer status/health fields (`eligible`, `usable`, `failed`, `skipped`)
- deterministic `k_eff` and per-defect `k_eff_defect`
- locked provenance modes (`reviewer_kind_scope_v1`, `global_min_per_defect`)

`occupancy_snapshot.schema.json` enforces Pack I layout:

- `artifact_version`, `kind`, `run`, `rows`, `summary`, `model`, `provenance`
- bounded posterior values (`psi_post` in `[0,1]`)
- deterministic row counts (`observed_by`, `missed_by`, `null_by`, `k_eff_defect`)
- explicit model metadata (`prior_policy`, `null_policy`, `suppression_policy`, locked parameters)
- provenance locked to telemetry input and model version (`occupancy_rev1`)

`capture_estimate.schema.json` enforces Pack J layout:

- `artifact_version`, `kind`, `run`, `inputs`, `counts`, `estimators`, `summary`, `provenance`
- deterministic incidence counts (`f1`, `f2`, histogram, ICE rare/frequent split)
- structured Chao1 and ICE outputs with explicit guard flags
- conservative selected hidden estimate (`max_hidden`)
- provenance locked to telemetry + occupancy inputs

`hazard_map.schema.json` enforces Pack K layout:

- `artifact_version`, `kind`, `run`, `inputs`, `summary`, `rows`, `model`, `provenance`
- deterministic per-defect hazard rows joined to structural `risk_score`
- bounded row and summary outputs (`hazard_contribution`, `hazard_score` in `[0,1]`)
- locked hazard tiers (`low`, `guarded`, `elevated`, `high`, `critical`)
- explicit uncertainty and blocking reason flags
- provenance locked to risk + telemetry + occupancy + capture inputs and `hazard_rev1`

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

## Python Test Coverage (Packs A-K)

- CLI smoke + failure behavior
- config normalization and rejection cases
- schema loader + schema positive/negative validation
- risk stage logic/unit + integration on temporary git repos
- range operations and hunk parsing
- context-slice extraction unit + integration + cap-overflow behavior
- reviewer execution stage behavior (`ok`, `failed`, `skipped`)
- finding normalization and fail-closed malformed finding handling
- deterministic defect identity (`defect_key`) behavior
- telemetry matrix stage behavior (`1`/`0`/`null`, reviewer health, conservative `k_eff`, cross-reviewer defect coalescing)
- telemetry ghost-coverage guard behavior (`failed`/`skipped` reviewer => `null`)
- fail-closed telemetry checks for same-reviewer duplicates and incompatible canonical metadata collisions
- occupancy snapshot stage behavior (bounded `psi_post`, conservative null handling, stronger-coverage suppression)
- occupancy fail-closed behavior for illegal telemetry cells, count mismatches, and invalid model config
- capture estimate stage behavior (`f1`/`f2`, Chao1, ICE, conservative selection)
- capture fail-closed behavior for inconsistent defect sets, invalid selection policy, and mismatched cross-artifact counts
- hazard map stage behavior (row hazard calculation, tier mapping, conservative summary aggregation)
- hazard fail-closed behavior for missing risk mapping, run/commit mismatch, inconsistent defect sets, and invalid model version
- golden-file checks for context slices
- repeatability checks using byte-equality of serialized artifacts
- integration proof that pipeline emits deterministic `review_findings.json`, `telemetry_matrix.json`, `occupancy_snapshot.json`, `capture_estimate.json`, and `hazard_map.json`

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
- explicit tri-state telemetry semantics (`1` observed, `0` eligible miss, `null` unavailable/inapplicable)
- reviewer-independent canonical defect identity with deterministic cross-reviewer coalescing
- explicit occupancy semantics (`null` contributes uncertainty, usable misses drive suppression)
- explicit hidden-defect semantics (singletons elevate caution, sparse guards stay visible)

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

Offline dev install path when dependencies are already provisioned in the environment:

```bash
pip install --no-build-isolation -e .
```

Current verified lower bound from the live repo test surface:

- `jsonschema>=4.10.3`
- `PyYAML>=6.0.1`

Reason for the offline flag:

- plain `pip install -e .` uses an isolated build environment
- offline installs will fail unless build requirements are available from an index or wheel cache
- `--no-build-isolation` is the truthful local/offline path when build dependencies are already present

If the evidence binary is not on `PATH`:

```bash
export FORGE_EVIDENCE_BIN=/abs/path/to/rust/forge-evidence/target/debug/forge-evidence
```

Current evidence boundary:

- the Rust evidence binary is verified and callable
- `forge-eval run` / `forge-eval validate` do not currently invoke it in the main A-K stage path

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
3. Confirm reviewer execution statuses are explicit (`ok`/`failed`/`skipped`) in `review_findings.json`.
4. Confirm telemetry cells are explicit (`1`/`0`/`null`) in `telemetry_matrix.json`.
5. Confirm shared canonical defects can produce `reported_by` length > 1 and `support_count` > 1 in `telemetry_matrix.json`.
6. Confirm same-reviewer duplicates and metadata collisions fail closed in tests.
7. Confirm occupancy rows are bounded (`psi_post` in `[0,1]`) in `occupancy_snapshot.json`.
8. Confirm capture outputs include Chao1, ICE, and selected hidden estimate in `capture_estimate.json`.
9. Confirm hazard output includes bounded `hazard_score`, deterministic `hazard_tier`, and explicit uncertainty flags in `hazard_map.json`.
10. Run Python and Rust tests before merge.

## Guardrails for Next Packs

1. Keep schema-first contracts; add new artifact kinds in `schemas/` before stage logic.
2. Preserve fail-closed defaults unless governance text explicitly allows deterministic reduction.
3. Keep evidence primitives centralized in Rust; do not duplicate them in Python.
4. Keep Pack G reviewer logic deterministic and isolated from Pack H+ telemetry/occupancy/hazard logic.
5. Preserve ghost-coverage guard: failed/skipped/inapplicable reviewer states must never be coerced to clean misses.
6. Preserve occupancy conservatism: weak/null-heavy coverage must not be treated as strong suppression.
7. Preserve capture conservatism: singleton-heavy sparse evidence must not collapse to low hidden-defect estimates.
8. Preserve hazard conservatism: hidden-defect pressure and uncertainty must not be converted into a clean-looking change set.

---

# §12 - Pack G: Reviewer Execution Stage

## Stage Contract

Input:

- `context_slices` artifact (required)
- `risk_heatmap` artifact (optional but used by `structural_risk` reviewer)
- normalized reviewer config

Output:

- `review_findings.json` (schema kind: `review_findings`)
- Downstream consumer: Pack H `telemetry_matrix` stage

## Execution Model

1. Load configured reviewers and sort by `reviewer_id`.
2. Apply deterministic scope filtering per reviewer.
3. Execute reviewer adapter with isolated input state.
4. Capture reviewer execution truth with explicit status:
   - `ok`
   - `failed`
   - `skipped`
5. Normalize raw findings into a strict contract.
6. Generate stable `defect_key` from canonical identity fields.
7. Sort findings deterministically and emit schema-valid artifact.

## Defect Identity

- `defect_key` is reviewer-independent canonical identity.
- Matching findings from different reviewers keep the same `defect_key`.
- Repeated `defect_key` values from the same reviewer still fail closed upstream.
- Pack H owns cross-reviewer coalescing and compatibility enforcement.

## Built-in Deterministic Reviewers

- `changed_lines`: deterministic rule checks over changed slices.
- `documentation_consistency`: code/docs pairing checks from slice set.
- `structural_risk`: threshold-based findings from Pack E risk scores.

## Fail-Closed Behavior

- Invalid reviewer config/kind -> stage failure.
- Malformed reviewer output/finding fields -> stage failure.
- Reviewer execution error:
  - `reviewer_failure_policy=fail_stage` -> fail stage.
  - `reviewer_failure_policy=record_and_continue` -> record reviewer `failed`.
- Artifact schema validation failure -> run failure.

## Determinism Notes

- Reviewer specs sorted by `reviewer_id`.
- Slices sorted by file/range before dispatch.
- Findings sorted by reviewer/file/slice/category/title/line anchor/`defect_key`.
- `defect_key` is deterministic hash (`dfk_<sha256hex>`) over reviewer-independent normalized identity fields.

---

# §13 - Pack H: Telemetry Matrix Stage

## Stage Contract

Input:

- `review_findings` artifact (required)
- normalized reviewer config (required)

Output:

- `telemetry_matrix.json` (schema kind: `telemetry_matrix`)
- Downstream consumer: Pack I `occupancy_snapshot` stage

## Execution Model

1. Validate `review_findings` shape and enforce `run_id` consistency.
2. Build canonical reviewer-health entries from reviewer execution truth.
3. Build canonical defect catalog from normalized findings, coalescing shared `defect_key` values across reviewers.
4. Compute reviewer-defect applicability deterministically.
5. Build tri-state observation matrix with strict cell values:
   - `1` = reviewer observed defect
   - `0` = reviewer was usable/applicable but did not report defect
   - `null` = reviewer failed, skipped, or was inapplicable
6. Compute per-defect `k_eff_defect` and conservative global `k_eff`.
7. Emit schema-valid `telemetry_matrix.json` with deterministic ordering.

## Reviewer Truth Preservation

- `status=failed` and `status=skipped` are never converted to clean misses.
- `usable` is derived conservatively (`status=ok` and `slices_seen > 0`).
- `eligible` and `usable` are explicit fields in each reviewer entry.

## Defect Coalescing Rule

- one `defect_key` represents one canonical defect identity.
- different reviewers may report that same canonical defect.
- telemetry merges distinct reviewers into `reported_by` and sets `support_count` to unique reviewer count.
- same-reviewer duplicate `defect_key` values still fail closed.
- incompatible repeated `defect_key` metadata (`file_path`, `category`, `severity`) still fails closed.

## Applicability Rule (v1)

`telemetry_applicability_mode=reviewer_kind_scope_v1`:

- extension/path scope checks from reviewer config are applied first
- `documentation_consistency` is limited to Markdown defects
- `structural_risk` excludes Markdown defects
- `changed_lines` applies broadly after scope checks

## `k_eff` Rule (v1)

`telemetry_k_eff_mode=global_min_per_defect`:

- per defect: `k_eff_defect = count(observation != null)`
- global: `k_eff = min(k_eff_defect over all matrix rows)`

This keeps Pack H conservative for downstream occupancy stages.

## Fail-Closed Behavior

- Invalid reviewer status or malformed reviewer entry -> stage failure.
- Duplicate reviewer IDs -> stage failure.
- Same-reviewer duplicate `defect_key` or incompatible repeated `defect_key` metadata -> stage failure.
- Findings that reference unknown reviewers -> stage failure.
- Unsupported applicability or `k_eff` modes -> stage failure.
- Illegal cell values (anything outside `1/0/null`) -> stage failure.
- Schema validation failure -> run failure.

## Determinism Notes

- Reviewer rows sorted by `reviewer_id`.
- Defects and matrix rows sorted by `defect_key`.
- Observation maps emitted in stable reviewer order.
- No clock-based fields in primary payload.

---

# §14 - Pack I: Occupancy Snapshot Stage

## Stage Contract

Input:

- `telemetry_matrix` artifact (required)
- normalized occupancy model config (required)

Output:

- `occupancy_snapshot.json` (schema kind: `occupancy_snapshot`)
- Downstream consumer: Pack J `capture_estimate` stage

## Execution Model

1. Validate telemetry artifact shape and enforce `run_id` consistency.
2. Build canonical per-defect occupancy rows from telemetry defects + matrix.
3. Derive deterministic priors from support/severity using config-locked policy.
4. Compute deterministic posterior occupancy (`psi_post`) with:
   - positive retention from observed detections,
   - suppression only from usable misses,
   - uncertainty guard from `null` coverage.
5. Emit bounded, schema-valid rows sorted by `defect_key`.
6. Emit deterministic summary + model metadata for auditability.

## Core Semantics

- `null` is uncertainty, not a clean miss.
- suppression requires usable miss evidence (`0` cells).
- sparse usable coverage does not over-suppress occupancy.
- `psi_post` is always bounded in `[0,1]`.

## Model Rule (v1)

`occupancy_model_version=occupancy_rev1` with deterministic conservative rule:

- prior = `occupancy_prior_base + occupancy_support_uplift(if support_count>0) + severity_uplift`
- observed retention from `occupancy_detection_assumption`
- miss penalty from usable miss ratio and coverage ratio
- uncertainty guard from null ratio and low coverage
- bounded posterior: `clamp(..., 0.02, 0.995)`

All parameters are config-locked and emitted in `model.parameters`.

## Fail-Closed Behavior

- telemetry artifact kind mismatch -> stage failure.
- run mismatch or missing telemetry fields -> stage failure.
- duplicate or inconsistent defect/matrix keys -> stage failure.
- illegal matrix cell values (outside `1/0/null`) -> stage failure.
- impossible row counts or `k_eff_defect` mismatch -> stage failure.
- unsupported model version or out-of-range model params -> stage failure.
- schema validation failure -> run failure.

## Determinism Notes

- rows sorted by `defect_key`.
- fixed rounding policy via `occupancy_round_digits`.
- no clock-based fields in primary payload.
- model metadata is explicit and version-locked.

---

# §15 - Pack J: Capture Estimate Stage

## Stage Contract

Input:

- `telemetry_matrix` artifact (required)
- `occupancy_snapshot` artifact (required)
- normalized capture-estimate config (required)

Output:

- `capture_estimate.json` (schema kind: `capture_estimate`)
- Downstream consumer: Pack K `hazard_map` stage

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

---

# §16 - Pack K: Hazard Map Stage

## Stage Contract

Input:

- `risk_heatmap` artifact (required)
- `telemetry_matrix` artifact (required)
- `occupancy_snapshot` artifact (required)
- `capture_estimate` artifact (required)
- normalized hazard config block (required)

Output:

- `hazard_map.json` (schema kind: `hazard_map`)

## Execution Model

1. Validate all upstream artifacts and enforce deterministic run alignment.
2. Join telemetry defects to occupancy rows by canonical `defect_key`.
3. Join each defect row to structural `risk_score` by `file_path`.
4. Compute deterministic per-defect hazard contribution from severity, residual occupancy, structural risk, and reviewer support.
5. Aggregate row contributions with a bounded union score.
6. Apply conservative hidden-defect uplift from Pack J and uncertainty uplift from sparse/null-heavy evidence.
7. Clamp final `hazard_score` to `[0,1]` and map to a deterministic tier.
8. Emit schema-valid summary, rows, model metadata, and provenance.

## Core Signals

Pack K combines four conservative signals:

- structural risk pressure from `risk_heatmap`
- observed defect burden from `telemetry_matrix`
- residual occupancy concern from `occupancy_snapshot`
- hidden-defect pressure from `capture_estimate`

## Model Rules (Rev 1)

- model version: `hazard_rev1`
- row policy: `severity_plus_uplifts_v1`
- summary policy: `bounded_union_hidden_uncertainty_v1`
- tier set: `low`, `guarded`, `elevated`, `high`, `critical`

Row contributions are deterministic and conservative:

- severity sets the base weight
- higher `psi_post` increases concern
- higher structural `risk_score` amplifies the same defect evidence
- cross-reviewer support can only increase concern; it never reduces it

Summary hazard remains bounded and interpretable:

- row contributions are merged with a bounded union score
- `selected_hidden` from Pack J applies hidden-defect uplift
- sparse/null-heavy evidence applies uncertainty uplift
- final `hazard_score` is clamped to `[0,1]`

## Fail-Closed Behavior

- missing upstream artifact -> stage failure
- run or commit mismatch across Pack H/I/J/K inputs -> stage failure
- defect-set mismatch between telemetry and occupancy -> stage failure
- missing structural risk mapping for a defect file -> stage failure
- unsupported `hazard_model_version` -> stage failure
- out-of-range hazard config params -> stage failure
- duplicate risk target or duplicate defect rows -> stage failure
- schema validation failure -> run failure

## Determinism Notes

- defect rows iterate in canonical `defect_key` order
- file-risk joins are exact on normalized `file_path`
- row flags and summary flags are emitted in deterministic order
- rounding is fixed by `hazard_round_digits`
- repeated identical inputs must produce byte-identical `hazard_map.json`
