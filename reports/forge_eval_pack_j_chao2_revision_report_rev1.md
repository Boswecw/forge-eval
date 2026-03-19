# Forge Eval Pack J Chao2 Revision Report (Rev 1)

## 1. Executive verdict

Implemented

All acceptance criteria are met. Chao2 is implemented, wired, schema-locked, tested (all 10 required tests pass), deterministic, documented, and the full 134-test suite passes including downstream Pack K/L/M tests.

## 2. Current Pack J baseline

Before this revision, Pack J computed two hidden-defect estimators:

- **Chao1** (bias-corrected): uses singleton count (f1) and doubleton count (f2) from the incidence histogram. Formula: `hidden = f1 * (f1 - 1) / (2 * (f2 + 1))`.
- **ICE** (Incidence-based Coverage Estimator): uses rare/frequent histogram split, sample coverage, and coefficient of variation (gamma squared). Falls back to Chao1 hidden estimate when coverage collapses.

Selection policy: `max_hidden` -- the estimator with the highest hidden estimate governs downstream.

Artifact shape: `capture_estimate.json` with `estimators.chao1`, `estimators.ice`, and flat selection fields (`selected_method`, `selected_source`, `selected_hidden`, `selected_total`) spread into the `estimators` object.

Counts derivation: the telemetry matrix provides per-defect observation vectors (1/0/null per reviewer). `observed_by` is the incidence count for each defect. The histogram aggregates how many defects have each incidence level. f1 = histogram[1], f2 = histogram[2].

## 3. Chao2 implementation

### Files changed

- **New:** `src/forge_eval/services/chao2.py` -- Chao2 estimator service
- **Modified:** `src/forge_eval/stages/capture_estimate.py` -- stage orchestrator (imports chao2, derives m from k_usable, wires chao2 into selection and summary)
- **Modified:** `src/forge_eval/services/capture_selection.py` -- 3-way selection across chao1/chao2/ice with unavailable tracking
- **Modified:** `src/forge_eval/services/capture_summary.py` -- accepts chao2, emits selection_policy, selected_method (estimator name), unavailable_estimators
- **Modified:** `src/forge_eval/schemas/capture_estimate.schema.json` -- chao2 block, new estimator/summary fields
- **Modified:** `tests/test_capture_estimate_stage.py` -- updated existing assertions, added 10 new tests
- **Modified:** `tests/test_schemas.py` -- updated valid capture_estimate example
- **Modified:** `doc/system/15-capture-estimate-stage.md` -- full documentation of Chao2
- **Modified:** `README.md` -- Pack J description updated
- **Rebuilt:** `doc/feSYSTEM.md` via `BUILD.sh`

### Sampling unit / incidence interpretation

Each reviewer is a sampling unit. Each defect is a species. The Chao2 formula operates on incidence data: how many sampling units (reviewers) detected each species (defect).

### Q1, Q2, m derivation

- **Q1** = f1 (defects seen by exactly 1 reviewer) -- already computed in `capture_counts.py`
- **Q2** = f2 (defects seen by exactly 2 reviewers) -- already computed in `capture_counts.py`
- **m** = `telemetry_summary["k_usable"]` (number of usable reviewers) -- read from the telemetry matrix artifact in the stage orchestrator

No new data structures were invented. All inputs are derived from existing Pack H telemetry data.

### Guard/fallback behavior

- **Q2 > 0:** Standard formula: `hidden = ((m-1)/m) * (Q1^2 / (2*Q2))`
- **Q2 == 0, Q1 > 0:** Conservative fallback: `hidden = ((m-1)/m) * (Q1*(Q1-1)/2)`. Guard flag `q2_zero_fallback` set to `true`.
- **Q1 == 0:** `hidden = 0.0` (no singleton pressure signal). Guard flag `q1_zero_no_signal` set to `true`.
- **m < 2:** Chao2 marked `available: false` with `reason_unavailable` explaining insufficient sampling units. Stage proceeds with Chao1 and ICE only. Chao2 appears in `unavailable_estimators`.
- **Negative/invalid inputs:** Chao2 marked `available: false` with explicit reason. Never emits a hidden estimate from invalid inputs.
- **Numeric validation:** After computation, hidden is checked for negative, NaN, or infinity -- raises StageError if found.

## 4. Schema and artifact changes

### Schema file updated

`src/forge_eval/schemas/capture_estimate.schema.json`

### New fields added to `estimators.chao2`

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean (const true) | Chao2 is always enabled |
| `available` | boolean | Whether Chao2 could compute a result |
| `hidden_estimate` | number or null | Hidden defect estimate (null when unavailable) |
| `total_estimate` | number or null | Total defect estimate (null when unavailable) |
| `guard_flags` | object | `q2_zero_fallback` (bool), `q1_zero_no_signal` (bool) |
| `inputs_used` | object | `q1` (int), `q2` (int), `m` (int) |
| `reason_unavailable` | string or null | Explicit reason when unavailable |

### New fields added to `estimators` (top level)

| Field | Type | Description |
|-------|------|-------------|
| `selection_policy` | string (const "max_hidden") | Fixed selection rule |
| `unavailable_estimators` | array of strings | Estimators that could not compute |

### New fields added to `summary`

| Field | Type | Description |
|-------|------|-------------|
| `selection_policy` | string (const "max_hidden") | Fixed selection rule |
| `selected_method` | string (enum) | Which estimator was selected (was previously "max_hidden", now the estimator name) |
| `unavailable_estimators` | array of strings | Estimators that could not compute |

### Validation behavior

- Schema is `additionalProperties: false` at root and all nested objects
- `chao2` block is required in `estimators`
- Guard flags object is strict: only `q2_zero_fallback` and `q1_zero_no_signal` allowed
- `inputs_used` is strict: only `q1`, `q2`, `m` allowed
- Downstream Pack K still reads `estimators.selected_method` = "max_hidden" -- backward compatible

## 5. Selection policy

### Policy: max_hidden

`selected_hidden = max(chao1_hidden, chao2_hidden, ice_hidden)` among available estimators only.

### How selected source is determined

- All available estimators contribute their hidden estimate as candidates
- The candidate with the highest hidden value wins
- If multiple candidates tie at the maximum, `selected_source` = "tie"
- `selected_source` is recorded in `estimators.selected_source` and `summary.selected_method`

### How unavailable estimators are recorded

- When Chao2 is unavailable (m < 2 or invalid inputs), "chao2" is added to `unavailable_estimators`
- This list appears in both `estimators.unavailable_estimators` and `summary.unavailable_estimators`
- Unavailable estimators are never silently dropped

### Execution evidence in artifact

All three estimator outputs are recorded in full (inputs, outputs, guard flags). The selection policy, selected source, selected hidden value, and unavailable list are all explicit in the artifact.

## 6. Test and verification results

### Exact pytest commands run

```bash
.venv/bin/python -m pytest tests/ -v
```

### Test counts and results

134 passed, 0 failed, 0 skipped.

Breakdown:
- 15 tests in `test_capture_estimate_stage.py` (5 original updated + 10 new Chao2 tests)
- 21 tests in `test_schemas.py` (updated valid example for capture_estimate)
- 98 tests across all other test files (unchanged, all passing)

### New Chao2 tests (10 required)

1. `test_chao2_positive_calculation` -- valid Q1=2, Q2=1, m=3 produces hidden=1.333333
2. `test_chao2_q2_zero_guard` -- Q2=0 uses fallback formula, sets guard flag
3. `test_chao2_unavailable_low_m` -- m=1 marks unavailable with explicit reason
4. `test_selection_policy_chao2_wins` -- Chao2 highest hidden is selected
5. `test_selection_policy_chao1_wins` -- Chao1 highest hidden is selected
6. `test_selection_policy_ice_wins` -- ICE highest hidden is selected (full stage)
7. `test_unavailable_estimator_recording` -- Chao2 unavailable recorded in artifact
8. `test_chao2_schema_validation_accepts_valid` -- full stage output validates against schema
9. `test_chao2_schema_validation_rejects_malformed` -- missing guard_flags fails validation
10. `test_chao2_determinism` -- byte-identical JSON on repeated identical runs

### Determinism check result

Byte-identical `capture_estimate.json` output confirmed on repeated runs with identical inputs (test 10).

## 7. Documentation updates

### Files changed

- `doc/system/15-capture-estimate-stage.md` -- expanded with Chao2 estimator section, Q1/Q2/m interpretation, selection policy details, execution evidence documentation, why Chao2 added, why Chao1 retained
- `README.md` -- Pack J description updated from "Chao1/ICE" to "Chao1/Chao2/ICE", determinism notes updated
- `doc/feSYSTEM.md` -- rebuilt via BUILD.sh

### Doc rebuild command and result

```bash
bash doc/system/BUILD.sh
# Output: feSYSTEM.md rebuilt (1347 lines)
```

## 8. Remaining open items

None. All acceptance criteria are met.

## 9. Recommended next actions

- Run full A-M pipeline integration test against a real target repo to verify end-to-end artifact chain with the revised capture_estimate shape
- Consider adding Chao2 to the `inputs` section of the artifact (e.g. `chao2_min_reviewers: 2`) if config-locking the m threshold becomes desirable
