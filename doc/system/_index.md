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
