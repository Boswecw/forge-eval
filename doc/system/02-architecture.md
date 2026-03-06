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
