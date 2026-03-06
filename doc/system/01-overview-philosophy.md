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
