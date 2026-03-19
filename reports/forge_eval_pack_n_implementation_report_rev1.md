# Forge Eval Pack N — Localization Pack Implementation Report (Rev 1)

## 1. Executive Verdict

**Implemented** — All 5 slices complete with 50 passing tests (10 + 11 + 11 + 11 + 7). No regressions in existing Forge Eval or NeuroForge test suites.

## 2. Schema and Artifact Contracts

| Artifact | Schema | Status |
|----------|--------|--------|
| `localization_pack.v1` | `localization_pack.schema.json` | Implemented, validates |
| `localization_summary.v1` | `localization_summary.schema.json` | Implemented, validates |
| `PromptSpec.localization_input` | `LocalizationInput` Pydantic model | Implemented |

Both schemas enforce `additionalProperties: false` at all levels. Key vocabulary constraints:
- `detected_language`: per-candidate, not top-level
- `hazard_tier`: Pack K vocabulary (`low|guarded|elevated|high|critical`)
- `root_cause_hypothesis`: locked bounded enum (9 values)
- `provenance.deterministic`: `const: true`

## 3. Pack N Stage Implementation

### Files Added

| File | Purpose |
|------|---------|
| `src/forge_eval/schemas/localization_pack.schema.json` | Pack N artifact schema |
| `src/forge_eval/schemas/localization_summary.schema.json` | Summary artifact schema |
| `src/forge_eval/stages/localization_pack.py` | Stage entry point |
| `src/forge_eval/services/localization_ranker.py` | File/block ranking with configurable weights |
| `src/forge_eval/services/review_scope_compiler.py` | Deterministic scope merge/clamp |
| `src/forge_eval/services/construct_extractor.py` | Language detection, construct extraction, hypothesis derivation |
| `src/forge_eval/services/patch_scope_builder.py` | Patch target passthrough |

### Files Modified

| File | Change |
|------|--------|
| `src/forge_eval/config.py` | Added `localization_pack` to KNOWN_STAGES, 7 config keys, ranking weights normalization |
| `src/forge_eval/stage_runner.py` | Added localization_pack to STAGE_ORDER and dispatch |
| `src/forge_eval/validation/schema_loader.py` | Added schema mappings |

### Ranking

File/block scoring uses 4 configurable weights (normalized to unit sum):
- `support_count` (0.35): max reviewer support across defects
- `defect_density` (0.25): defect count / slice count
- `hazard_contribution` (0.25): max hazard contribution from Pack K
- `churn` (0.15): context slice count as a proxy

Per-candidate confidence: `support_norm * 0.5 + evidence_density * 0.5`
Summary confidence: `min(block confidences)`

### Construct Extraction

Deterministic AST/heuristic pattern matching for 4 languages (Python, Rust, TypeScript, Svelte). Framework detection from file content hints. Root cause hypothesis derived from first-match rules against construct vocabulary.

### Review Scope Compilation

Groups blocks by file, merges overlapping ranges, clamps per-file (`max_scope_lines_per_file=150`) and total (`max_review_scope_lines=500`). Fails closed if no valid scope remains.

## 4. NeuroForge Integration

### Files Added

| File | Purpose |
|------|---------|
| `neuroforge_backend/services/localization_gate.py` | LOC-GATE validation, ref resolution, scope checking, context rendering |

### Files Modified

| File | Change |
|------|--------|
| `neuroforge_backend/services/evaluator.py` | Added `_evaluate_localization_gate` method, wired before `_evaluate_patch_task` |
| `neuroforge_backend/services/prompt_engine.py` | Added localized review mode to `_construct_patch_prompt`, `_render_review_scope_context` static method |
| `neuroforge_backend/rtcfx/models.py` | Added `LocalizationInput` model, `localization_input` field to `PromptSpec` |

### LOC-GATE Codes

| Code | Meaning |
|------|---------|
| `LOC-GATE-MISSING` | Repair requested, no localization artifact supplied |
| `LOC-GATE-INVALID-REF` | Ref cannot resolve under trusted workspace roots |
| `LOC-GATE-SCHEMA-INVALID` | Pack fails shape validation |
| `LOC-GATE-RUN-MISMATCH` | run_id mismatch |
| `LOC-GATE-SCOPE-EMPTY` | review_scope is empty |
| `LOC-GATE-NO-SCOPE` | Patch target outside localization scope |

All codes: `recoverable=False`, `category=LOCALIZATION_CONTRACT`.

### Gate Execution Order

1. LOC-GATE-MISSING through LOC-GATE-NO-SCOPE (6 checks)
2. MAPO-TGT-GATE-* (existing, unchanged)
3. MRPA apply

### Prompt Compiler

When localization pack is loaded:
- Prepends localized review contract text
- Renders only review_scope blocks as bounded context
- Includes `likely_constructs` and `root_cause_hypothesis` per block
- Suppresses out-of-scope file/repo context
- `allow_analysis_only=true` suppresses patch_scope rendering

### Telemetry

Pack N stage logs: model_version, file/block counts, review scope lines, patch scope presence, summary confidence, hazard tier.
NeuroForge LOC-GATE logs: artifact_ref, review mode enabled, blocked reason, downgraded flag, approved region count.

## 5. Test and Verification Results

### Test Counts

| Suite | Tests | Result |
|-------|-------|--------|
| Slice 1 — Schema + scaffold | 10 | All pass |
| Slice 2 — Ranking + scope | 11 | All pass |
| Slice 3 — Constructs + patch | 11 | All pass |
| Slice 4 — LOC-GATE + prompt | 11 | All pass |
| Slice 5 — E2E governed path | 7 | All pass |
| **Total Pack N** | **50** | **All pass** |
| MAPO-TGT-GATE regression | 18 | All pass |

### Commands

```bash
# Forge Eval (39 Pack N tests)
cd forge-eval/repo && .venv/bin/python -m pytest tests/test_localization_pack_stage.py tests/test_localization_ranking.py tests/test_construct_extraction.py tests/test_localization_e2e.py -v

# NeuroForge (11 LOC-GATE tests + 18 MAPO-TGT-GATE regression)
cd NeuroForge && ./venv/bin/python -m pytest neuroforge_backend/tests/test_localization_gate.py neuroforge_backend/tests/test_patch_targets_enforcement.py -v
```

### Golden Artifact Determinism

Repeated runs with identical inputs produce byte-identical `localization_pack.json` artifacts (Slice 3 test 11, Slice 5 test 7).

## 6. DataForge Persistence

Pack N artifacts (`localization_pack.json`) are written to the artifacts directory by the stage runner, following the same pattern as all prior stages. Source artifact refs are embedded in `source_artifacts` for audit trail. NeuroForge LOC-GATE telemetry logs audit-relevant fields (artifact_ref, blocked reason, downgraded flag).

## 7. Documentation Updates

- `doc/system/19-localization-pack-stage.md` written
- `doc/system/_index.md` updated with section 19
- `doc/system/BUILD.sh` executed, `doc/feSYSTEM.md` rebuilt (1511 lines)

## 8. Remaining Open Items

- `localization_summary.json` is not yet emitted as a separate file by the stage runner (summary data is embedded in `localization_pack.json.summary`). Separate file emission can be added if downstream consumers require it.
- DataForge write-back of localization artifacts requires DataForge API endpoints (deferred to ForgeCommand integration).
- Function candidates (`function_candidates`) are emitted as an empty array in v1 (per plan).

## 9. Recommended Next Actions

1. Wire `localization_summary.json` emission in `stage_runner.py` if separate summary artifact is needed by operators.
2. Add DataForge API endpoints for localization artifact storage.
3. Implement function-level candidate extraction in a future revision.
4. Add learned ranking models when sufficient telemetry data is available.
5. Integrate Pack N into ForgeCommand governance workflow.
