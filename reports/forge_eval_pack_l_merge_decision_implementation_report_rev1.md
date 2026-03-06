## Forge Eval Pack L Merge Decision Implementation Report (Rev 1)

## What changed

Pack L extends the fixed Pack K runtime boundary with one new deterministic advisory stage:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map -> merge_decision`

Added artifact:

- `merge_decision.json`

Implemented surfaces:

- `src/forge_eval/schemas/merge_decision.schema.json`
- `src/forge_eval/stages/merge_decision.py`
- `src/forge_eval/services/merge_decision_model.py`
- `src/forge_eval/services/merge_decision_reasons.py`
- `src/forge_eval/services/merge_decision_summary.py`

Updated wiring and contract surfaces:

- `src/forge_eval/config.py`
- `src/forge_eval/stage_runner.py`
- `tests/test_merge_decision_stage.py`
- `tests/test_config.py`
- `tests/test_schemas.py`
- `tests/integration/test_review_findings_repo.py`
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
- `doc/system/16-hazard-map-stage.md`
- `doc/system/17-merge-decision-stage.md`
- `doc/feSYSTEM.md`

## Boundary review

Pack L stays inside the intended boundary.

Inputs actually consumed by Pack L:

- `hazard_map.json`
- normalized config

Intentional minimal dependency decision:

- although Pack L could have read more upstream artifacts, the implemented stage uses `hazard_map.json` only
- this keeps Pack L decision-only and avoids re-deriving Pack E-K semantics downstream

Pack L emits only:

- `merge_decision.json`

Pack L does not:

- assemble evidence bundles
- invoke the Rust evidence binary in runtime
- mutate upstream artifacts
- perform git operations
- redefine Pack K hazard semantics

Code evidence:

- `src/forge_eval/stages/merge_decision.py` accepts only `hazard_map_artifact`
- `src/forge_eval/stage_runner.py` wires `merge_decision` strictly after `hazard_map`
- source search across the Pack L implementation surfaces found no `evidence_bundle` or merge-execution behavior

## Schema and wiring review

Stage registration:

- `KNOWN_STAGES` now includes `merge_decision`
- default enabled stage list now includes `merge_decision`
- `STAGE_ORDER` now ends with `merge_decision`
- `STAGE_TO_ARTIFACT_KIND['merge_decision'] == 'merge_decision'`

Config surface added:

- `merge_decision_model_version` (`merge_rev1`)
- `merge_decision_caution_threshold`
- `merge_decision_block_threshold`
- `merge_decision_block_on_hazard_blocking_signals`

Validation behavior:

- unsupported `merge_decision_model_version` fails closed
- threshold values must stay in `[0,1]`
- caution threshold must be `<=` block threshold
- `merge_decision` requires `hazard_map`

Schema/runtime alignment:

- runtime output keys match `merge_decision.schema.json`
- output is strict and schema-valid
- no undocumented runtime fields were emitted on the verified real run

## Tests run

Commands run:

```bash
python3 -m py_compile \
  src/forge_eval/config.py \
  src/forge_eval/stage_runner.py \
  src/forge_eval/stages/merge_decision.py \
  src/forge_eval/services/merge_decision_model.py \
  src/forge_eval/services/merge_decision_reasons.py \
  src/forge_eval/services/merge_decision_summary.py \
  tests/test_merge_decision_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q \
  tests/test_merge_decision_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py -q

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q -rA
```

Results:

- Python compile check: passed
- Pack L stage/schema/config/integration set: passed
- full Python test suite: passed

## Real run result

Verified real target:

- repo: `/home/charlie/Forge/ecosystem/DataForge`
- base: `eea89609d5e32d61f85e658f05cc8f573fb6fd29`
- head: `c8fe082d8d7c8cdb74c4ec7d0f727af306c40051`

Commands run:

```bash
PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packk-config.yml \
  --out /tmp/forge-eval-packl-smoke1

PYTHONPATH=src python3 -m forge_eval.cli validate \
  --artifacts /tmp/forge-eval-packl-smoke1
```

Run result:

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
      "hazard_map.json",
      "merge_decision.json"
    ],
    "base_commit": "eea89609d5e32d61f85e658f05cc8f573fb6fd29",
    "head_commit": "c8fe082d8d7c8cdb74c4ec7d0f727af306c40051",
    "run_id": "d5420d29d8bc811a"
  },
  "status": "ok"
}
```

Observed Pack L decision from the verified real run:

```json
{
  "blocking_signals_present": true,
  "decision": "block",
  "dominant_hazard_tier": "elevated",
  "hazard_score": 0.571867,
  "reason_codes": [
    "HAZARD_BLOCKING_SIGNAL_PRESENT",
    "HAZARD_TIER_ELEVATED",
    "HAZARD_SCORE_AT_OR_ABOVE_CAUTION_THRESHOLD",
    "HAZARD_UNCERTAINTY_PRESENT",
    "HAZARD_HIDDEN_PRESSURE_ELEVATED"
  ]
}
```

Interpretation of that result:

- Pack L blocked because Pack K already exposed a blocking signal on the verified run surface
- Pack L did not re-score hazard; it applied the rule table to Pack K output as intended

## Determinism result

Commands run:

```bash
PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packk-config.yml \
  --out /tmp/forge-eval-packl-smoke2
```

Byte comparison result:

- `config.resolved.json`: yes
- `risk_heatmap.json`: yes
- `context_slices.json`: yes
- `review_findings.json`: yes
- `telemetry_matrix.json`: yes
- `occupancy_snapshot.json`: yes
- `capture_estimate.json`: yes
- `hazard_map.json`: yes
- `merge_decision.json`: yes

Overall determinism verdict:

- pass

## Fail-closed result

Probes executed:

1. invalid config value / unsupported model version
2. missing `hazard_map.json` during validation
3. malformed upstream `hazard_map.json`
4. invalid merge decision output against schema
5. missing required merge decision field
6. missing stage input (`hazard_map_artifact={}`)

Representative commands/results:

```bash
cat > /tmp/forge-eval-packl-bad-config.yml <<'YAML'
max_total_lines: 2000
merge_decision_model_version: merge_revX
YAML
PYTHONPATH=src python3 -m forge_eval.cli run ...
```

Result:

```json
{"error":{"code":"config_error","details":{},"message":"merge_decision_model_version must be 'merge_rev1'","stage":"config"},"status":"error"}
```

```bash
PYTHONPATH=src python3 -m forge_eval.cli validate --artifacts /tmp/forge-eval-packl-missing-hazard
```

Result:

```json
{"error":{"code":"validation_error","details":{"artifact_kind":"hazard_map","path":"/tmp/forge-eval-packl-missing-hazard/hazard_map.json"},"message":"required artifact is missing","stage":"validation"},"status":"error"}
```

Malformed upstream JSON result:

```json
{"error":{"code":"validation_error","details":{"error":"Expecting property name enclosed in double quotes: line 1 column 2 (char 1)","path":"/tmp/forge-eval-packl-malformed/hazard_map.json"},"message":"artifact file is invalid JSON","stage":"validation"},"status":"error"}
```

Direct schema probes on `merge_decision.json`:

- missing required field -> schema validation failed at `$.decision`
- invalid `decision.result` value -> schema validation failed at `$.decision.result`

Direct stage probe:

- empty hazard stage input -> `merge_decision requires hazard_map artifact`

Overall fail-closed verdict:

- pass

## Documentation alignment

Updated docs now state the implemented Pack L boundary explicitly:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map -> merge_decision`

Docs now state correctly that:

- Pack L = merge decision only
- Pack M = evidence bundle assembly
- Pack L consumes Pack K output and remains advisory
- Rust evidence is still outside the active A-L runtime path

Doc rebuild command:

```bash
bash doc/system/BUILD.sh
```

Result:

- `feSYSTEM.md rebuilt (1171 lines)`

## Implementation report path

- `reports/forge_eval_pack_l_merge_decision_implementation_report_rev1.md`

## Blocking findings

None confirmed for Pack L.

## Non-blocking findings

Current live `DataForge HEAD~1..HEAD` remains an unreliable smoke target because earlier A-J guardrails still fail closed on that live diff. Pack L verification therefore continues to use the previously verified successful `DataForge` range. This is not a Pack L defect.

## Verdict

PASS WITH NON-BLOCKING FINDINGS
