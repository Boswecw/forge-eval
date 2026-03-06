## Forge Eval Pack K Hazard Implementation Report (Rev 1)

### 1. Executive verdict
Implemented

### 2. Baseline starting point
Forge Eval started from a verified and hardened A-J baseline:

- implemented pipeline boundary: `config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate`
- real A-J runtime had already been verified on a local `DataForge` target repo
- emitted artifacts were schema-valid and byte-stable across identical reruns
- fail-closed behavior was already verified across config, validation, and upstream stage-contract cases

Pack K extended that boundary to:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map`

### 3. Schema and config work
Files changed:

- `src/forge_eval/config.py`
- `src/forge_eval/stage_runner.py`
- `src/forge_eval/schemas/hazard_map.schema.json`
- `tests/test_config.py`
- `tests/test_schemas.py`

Config additions:

- `hazard_model_version` (`hazard_rev1` only)
- `hazard_round_digits`
- `hazard_hidden_uplift_strength`
- `hazard_structural_risk_strength`
- `hazard_occupancy_strength`
- `hazard_support_uplift_strength`
- `hazard_uncertainty_boost`
- `hazard_blocking_threshold`

Validation behavior:

- `hazard_map` is now a known stage and enabled by default in the resolved config
- `hazard_map` requires `capture_estimate` to be enabled
- unsupported `hazard_model_version` fails closed during config normalization
- out-of-range hazard parameters fail closed during config normalization
- `hazard_map.schema.json` is loaded into the validation registry and enforced by both `run` and `validate`

Representative fail-closed command:

```bash
cat > /tmp/forge-eval-packk-bad-config.yml <<'YAML'
hazard_model_version: hazard_revX
YAML
PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packk-bad-config.yml \
  --out /tmp/forge-eval-packk-bad-run
```

Result:

```json
{"error":{"code":"config_error","details":{},"message":"hazard_model_version must be 'hazard_rev1'","stage":"config"},"status":"error"}
```

### 4. Hazard stage implementation
Files changed:

- `src/forge_eval/stages/hazard_map.py`
- `src/forge_eval/services/hazard_model.py`
- `src/forge_eval/services/hazard_rows.py`
- `src/forge_eval/services/hazard_summary.py`
- `tests/test_hazard_map_stage.py`

Model summary:

Pack K combines four conservative signals:

- structural risk pressure from `risk_heatmap`
- observed defect burden from `telemetry_matrix`
- residual occupancy concern from `occupancy_snapshot`
- hidden-defect pressure from `capture_estimate`

Per-defect hazard rows are computed deterministically from:

- severity base weight
- `psi_post`
- file-level `risk_score`
- reviewer support count and `k_eff_defect`

Summary hazard uses:

- bounded union aggregation of row contributions
- conservative hidden-defect uplift from `selected_hidden`
- uncertainty uplift from sparse/null-heavy evidence
- deterministic tier mapping to `low`, `guarded`, `elevated`, `high`, `critical`

The stage fails closed on:

- missing upstream artifacts
- run or commit mismatch across Pack H/I/J/K inputs
- defect-set mismatch between telemetry and occupancy
- missing structural risk mapping for a defect file
- unsupported hazard model version
- duplicate or inconsistent upstream rows
- schema validation failure

Emitted artifact shape:

- `artifact_version`
- `kind`
- `run`
- `inputs`
- `summary`
- `rows`
- `model`
- `provenance`

Real emitted artifact summary from the successful smoke run:

```json
{
  "blocking_reason_flags": ["hidden_pressure_on_high_risk_surface"],
  "blocking_signals_present": true,
  "defect_count": 2,
  "hazard_score": 0.571867,
  "hazard_tier": "elevated",
  "selected_hidden": 1.0,
  "uncertainty_flags": [
    "sparse_capture_data",
    "low_doubleton_support",
    "ice_low_coverage",
    "estimator_guard_applied",
    "null_heavy_occupancy"
  ]
}
```

### 5. Test and verification results
Exact commands:

```bash
python3 -m py_compile \
  src/forge_eval/config.py \
  src/forge_eval/stage_runner.py \
  src/forge_eval/stages/hazard_map.py \
  src/forge_eval/services/hazard_model.py \
  src/forge_eval/services/hazard_rows.py \
  src/forge_eval/services/hazard_summary.py \
  tests/test_hazard_map_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q \
  tests/test_hazard_map_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py -q

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q -rA

cat > /tmp/forge-eval-packk-config.yml <<'YAML'
max_total_lines: 2000
YAML

PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packk-config.yml \
  --out /tmp/forge-eval-packk-smoke1

PYTHONPATH=src python3 -m forge_eval.cli validate \
  --artifacts /tmp/forge-eval-packk-smoke1

PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packk-config.yml \
  --out /tmp/forge-eval-packk-smoke2
```

Test results:

- Python compile check: passed
- targeted Pack K pytest set: passed
- full Python test suite: passed
- real Pack K smoke run: passed
- `forge-eval validate` on emitted Pack K artifacts: passed

Successful real run result:

```json
{
  "result": {
    "artifacts_written": [
      "config.resolved.json",
      "risk_heatmap.json",
      "context_slices.json",
      "review_findings.json",
      "telemetry_matrix.json",
      "occupancy_snapshot.json",
      "capture_estimate.json",
      "hazard_map.json"
    ],
    "base_commit": "eea89609d5e32d61f85e658f05cc8f573fb6fd29",
    "head_commit": "c8fe082d8d7c8cdb74c4ec7d0f727af306c40051",
    "run_id": "d5420d29d8bc811a"
  },
  "status": "ok"
}
```

Determinism results:

Byte comparison across the two identical Pack K smoke runs returned `yes` for every primary artifact:

- `config.resolved.json`
- `risk_heatmap.json`
- `context_slices.json`
- `review_findings.json`
- `telemetry_matrix.json`
- `occupancy_snapshot.json`
- `capture_estimate.json`
- `hazard_map.json`

Fail-closed results proved during Pack K implementation:

- invalid hazard model version: failed closed at config normalization
- missing `hazard_map.json` during `validate`: failed closed with `validation_error`
- unit-tested run mismatch between upstream Pack H/I/J/K artifacts: failed closed
- unit-tested commit mismatch between upstream Pack H/I/J/K artifacts: failed closed
- unit-tested missing structural risk mapping for a defect file: failed closed
- unit-tested telemetry/occupancy defect-set mismatch: failed closed

Representative missing-artifact validation command:

```bash
mkdir -p /tmp/forge-eval-packk-missing-hazard
python3 - <<'PY'
from pathlib import Path
src = Path('/tmp/forge-eval-packk-smoke1')
dst = Path('/tmp/forge-eval-packk-missing-hazard')
for path in src.iterdir():
    if path.name == 'hazard_map.json':
        continue
    dst.joinpath(path.name).write_bytes(path.read_bytes())
print('copied')
PY
PYTHONPATH=src python3 -m forge_eval.cli validate \
  --artifacts /tmp/forge-eval-packk-missing-hazard
```

Result:

```json
{"error":{"code":"validation_error","details":{"artifact_kind":"hazard_map","path":"/tmp/forge-eval-packk-missing-hazard/hazard_map.json"},"message":"required artifact is missing","stage":"validation"},"status":"error"}
```

Note on real-target verification scope:

- current `HEAD~1..HEAD` runs on the live `DataForge` worktree still fail closed in earlier packs under existing A-J guardrails (`max_total_lines` and a Pack J positive-incidence contract)
- those failures were reproducible before Pack K smoke verification and are not regressions caused by Pack K
- Pack K verification therefore used the previously verified real `DataForge` commit range that completes successfully end-to-end

### 6. Documentation updates
Files changed:

- `README.md`
- `doc/system/_index.md`
- `doc/system/01-overview-philosophy.md`
- `doc/system/02-architecture.md`
- `doc/system/04-project-structure.md`
- `doc/system/05-cli-config-artifacts.md`
- `doc/system/06-evidence-subsystem.md`
- `doc/system/09-schemas-validation-errors.md`
- `doc/system/10-testing-determinism.md`
- `doc/system/11-handover-runbook.md`
- `doc/system/15-capture-estimate-stage.md`
- `doc/system/16-hazard-map-stage.md`
- `doc/feSYSTEM.md`

New implemented boundary:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map`

Doc rebuild command:

```bash
bash doc/system/BUILD.sh
```

Result:

- `feSYSTEM.md rebuilt (1053 lines)`

### 7. Remaining open items
None confirmed for Pack K.

Downstream packs remain intentionally out of scope:

- merge decision
- evidence bundle assembly

### 8. Recommended next actions
1. Implement Pack L merge decision against `hazard_map.json` rather than re-deriving hazard semantics downstream.
2. Keep using the historical verified `DataForge` range for end-to-end regression smoke tests until the separate upstream Pack J positive-incidence contract issue on current diffs is addressed.
