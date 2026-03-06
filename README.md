# Forge Eval (Packs A-F)

Deterministic, schema-validated, fail-closed foundation for:

- Pack A: Python scaffold + CLI + orchestration
- Pack B: Rust `forge-evidence` canonical JSON/hashing/hashchain
- Pack C: Python wrapper around Rust evidence binary
- Pack D: Strict JSON schemas
- Pack E: Structural risk heatmap stage
- Pack F: Context slice extraction stage

## Build Rust evidence binary

```bash
cd rust/forge-evidence
cargo build --offline
```

Binary path after build:

```text
rust/forge-evidence/target/debug/forge-evidence
```

Use `FORGE_EVIDENCE_BIN` to point Python wrapper to the binary if it is not on `PATH`.

## Install Python package

```bash
pip install -e .
```

## Run pipeline

```bash
forge-eval run --repo /path/to/repo --base <base> --head <head> --config config.yaml --out artifacts/
```

## Validate artifacts

```bash
forge-eval validate --artifacts artifacts/
```

## Determinism notes

- JSON artifacts are written with sorted keys and compact separators.
- Stage order is fixed: `risk_heatmap` then `context_slices`.
- Context extraction uses head-version content with deterministic diff/range processing.
- Cap overflows fail closed (no silent truncation).
