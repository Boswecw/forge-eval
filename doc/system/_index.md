# Forge Eval System Documentation

**Document version:** 1.2 (2026-03-06) — Implemented Pack L merge decision stage and normalized to Forge Documentation Protocol v1
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
| §17 | [17-merge-decision-stage.md](17-merge-decision-stage.md) | Pack L deterministic advisory merge decision from Pack K hazard evidence |

## Quick Assembly

```bash
bash doc/system/BUILD.sh   # Assembles all parts into doc/feSYSTEM.md
```

*Last updated: 2026-03-06*
