# Repository Audit — forge-eval

**Date:** 2026-05-31
**Branch:** `claude/repo-audit-eg7AI`
**Scope:** Full repository — Python package `forge_eval`, Rust crate `forge-evidence`, schemas, tests, docs, packaging.
**Method:** Static review of source plus empirical runs of `ruff`, `cargo test`, `cargo clippy`, `cargo fmt`, and `pip install`.

## What this project is

`forge-eval` is a deterministic, schema-validated, fail-closed evaluation pipeline. A
Python package orchestrates a fixed sequence of stages
(`risk_heatmap → context_slices → review_findings → telemetry_matrix →
occupancy_snapshot → capture_estimate → hazard_map → merge_decision →
evidence_bundle`, plus a later `localization_pack`), and a small Rust crate
(`forge-evidence`) provides canonical JSON, SHA-256, artifact IDs, and a hashchain.

- ~97 Python files, ~15.6k LOC; 6 Rust files, ~640 LOC; 13 JSON schemas.
- Core invariants (per README): deterministic byte-stable outputs, sorted-key/compact
  JSON, fixed stage order, fail-closed on error.

## Summary

The codebase is well-structured and the core logic is generally careful about
determinism (sorted keys, explicit ordering, conservative posteriors). The issues
found are mostly **hygiene and tooling-gate** problems rather than logic defects, but
several would block a quality gate, and a couple of unused-variable findings point at
**latent/incomplete logic** worth a closer look.

| # | Severity | Area | Issue |
|---|----------|------|-------|
| 1 | High | Lint gate | `ruff check .` fails with **19 errors** (unused imports/vars) |
| 2 | Med  | Logic smell | Two F841 findings look like **dropped/incomplete logic**, not just style |
| 3 | Med  | Packaging | `requires-python = ">=3.12"`, but no lower-bound CI guarantee; install fails on 3.11 |
| 4 | Med  | Packaging | No declared **test/dev dependencies** (`pytest`, `jsonschema` used by tests) |
| 5 | Med  | Format gate | `ruff format --check` wants to reformat **76 files**; `cargo fmt --check` fails on 5 |
| 6 | Low  | Robustness | Broad `except Exception` in a "fail-closed" pipeline (a few sites) |
| 7 | Low  | Optional dep | `lineage/emitter.py` imports external `forge_lineage_sdk` not in `pyproject` |
| 8 | Info | Tooling | No `[tool.ruff]` / `[tool.mypy]` config; lint/format rules are implicit |

> Two checks I was unable to finish verifying this session due to a tool-output
> stall: (a) a full green `pytest` run, and (b) whether a `.github/` CI workflow
> exists. Both are called out inline below as **unverified** so they can be
> confirmed in a follow-up.

---

## High

### 1. `ruff check .` fails — 19 errors

`ruff 0.15.8 check .` exits non-zero with 19 findings. If lint is (or becomes) a
gate, this is red. Breakdown:

**Source (`src/`):**
- `centipede_runner.py:19` — `stable_json_dumps` imported but unused (F401)
- `services/construct_extractor.py:74` — `lang` assigned but never used (F841)
- `services/evidence_bundle_manifest.py:6` — `typing.Iterable` unused (F401)
- `services/slice_extractor.py:10` — `git_diff.ChangedFile` unused (F401)
- `services/localization_ranker.py:214,215` — `start`, `end` unused (F841) — see #2
- `stages/localization_pack.py:128,133` — `top_reason_codes`, `top_files` unused (F841) — see #2

**Tests (`tests/`):** 11 further F401/E402 (unused `pytest`, `jsonschema`,
`json`, `sys`, `load_schema`, `StageError`, etc.), e.g.
`tests/test_construct_extraction.py`, `tests/test_localization_e2e.py`
(also an E402 module-import-not-at-top).

13 of the 19 are auto-fixable with `ruff check --fix`.

---

## Medium

### 2. Unused locals that look like dropped logic (not just style)

Two of the F841 findings are worth a human look because the *names* imply behavior
that isn't happening:

- **`services/localization_ranker.py:214-215`** extracts `start = slice_entry.get("start_line")`
  and `end = slice_entry.get("end_line")` and then **never uses them** while iterating
  `hazard_map_artifact.rows` to compute a max hazard contribution. This strongly
  suggests a *line-range overlap check was intended* (only count hazard rows that fall
  within `[start, end]`) but the comparison was dropped — so hazard contribution may be
  computed over the whole file rather than the slice.
- **`stages/localization_pack.py:128 & 133`** compute `top_reason_codes` (sorted
  reason-code ranking) and `top_files` (top-3 candidate files) and then **discard
  them**. These look like summary fields that were meant to be emitted into the
  `localization_pack` artifact but never wired into the output dict.

Neither breaks a schema or a test today, but both are behavioral gaps, not cosmetic.
Recommend confirming against the localization spec before deleting the variables.

### 3. `requires-python = ">=3.12"` with no enforced floor

`pyproject.toml` pins `requires-python = ">=3.12"`. On this environment (Python
**3.11.15**) `pip install -e .` fails outright:

```
ERROR: Package 'forge-eval' requires a different Python: 3.11.15 not in '>=3.12'
```

That's correct behavior, but combined with the absence of a verified CI matrix
(**unverified** — see note above) there's nothing guaranteeing contributors actually
run on 3.12. Either document/standardize the 3.12 toolchain or relax the floor if 3.11
is acceptable (the code uses `from __future__ import annotations` and `X | None`
syntax that works under 3.11 anyway).

### 4. No declared test/dev dependencies

`pyproject.toml` declares only runtime deps (`jsonschema`, `PyYAML`). The test suite
imports `pytest` and `jsonschema`, but there is no `[project.optional-dependencies]`
`dev`/`test` group and no `[dependency-groups]`. A fresh checkout can't run the tests
from packaging metadata alone. Add a `test`/`dev` extra (pytest, ruff, and pin
jsonschema for tests).

### 5. Formatting gates fail

- `ruff format --check .` → **76 files would be reformatted** (21 already formatted).
- `cargo fmt --check` (in `rust/forge-evidence`) → fails; 5 files differ
  (`canonical.rs`, `chain.rs`, `main.rs`, `tests/integration_cli.rs`).

The code isn't malformed — it just hasn't been run through the formatters, so any
"format" CI gate is currently red. `ruff format .` + `cargo fmt` resolve all of it.

> Note: `cargo test` **passes** (5 + 5 tests) and `cargo clippy --all-targets`
> is **clean** (exit 0). The Rust side is in good shape apart from formatting.

---

## Low / Info

### 6. Broad `except Exception` in a fail-closed system
A few sites swallow broad exceptions: `services/risk_analysis.py:124`
(`except Exception:`), `lineage/emitter.py:105` (`# noqa: BLE001`),
`contracts/evaluation_spine.py:127,145`, `reviewers/adapters.py:39`. For a system
whose stated invariant is "fail-closed," catch-all handlers deserve scrutiny — confirm
each re-raises a structured `ForgeEvalError` or is deliberately best-effort
(e.g. optional lineage emission), and narrow the exception types where possible.

### 7. Optional external dependency not declared
`lineage/emitter.py` imports `forge_lineage_sdk` (with `# noqa: E402`), which is not in
`pyproject.toml`. If lineage emission is optional, the import should be guarded and the
dependency declared as an extra; otherwise it's an undeclared hard dependency that will
ImportError outside the dev workspace.

### 8. No linter/formatter config in `pyproject.toml`
There's no `[tool.ruff]` (rule selection, line length, per-file-ignores for tests) or
`[tool.mypy]` section. Lint results therefore depend on ruff's defaults and whatever
version a contributor has. Pin tool config so the gate is reproducible — and consider
`per-file-ignores` so test files don't trip F401 on intentional imports.

---

## What's good
- **Determinism discipline:** canonical JSON writer sorts object keys
  (`rust/.../canonical.rs`), Python `stable_json_dumps` uses `sort_keys=True` +
  compact separators, directory walks are explicitly `sort()`ed, config normalization
  sorts/normalizes lists and reviewer ordering. Repeated-run byte-stability is
  plausible by construction.
- **Fail-closed structure:** `stage_runner` validates every stage's artifact `kind`
  against the expected kind *and* against its JSON schema before writing; missing
  prerequisite artifacts raise `StageError`.
- **Strong config validation:** `config.py` rejects unknown keys, enforces numeric
  ranges, normalizes weights to a unit sum, and validates stage-dependency ordering.
- **Rust crate:** clean clippy, passing tests, idempotent canonicalization with an
  explicit non-finite-float guard.

## Recommended order
1. `ruff check --fix .` then hand-fix the remaining F841s — but for the four in
   `localization_ranker.py` / `localization_pack.py`, decide whether the *logic*
   should be completed rather than the variables deleted (#2).
2. `ruff format .` and `cargo fmt` (#5).
3. Add a `dev`/`test` dependency extra and `[tool.ruff]` config; reconcile the
   Python-version floor (#3, #4, #8).
4. Declare/guard `forge_lineage_sdk` and tighten broad excepts (#6, #7).
