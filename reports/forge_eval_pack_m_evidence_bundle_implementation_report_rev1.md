## Forge Eval Pack M Evidence Bundle Implementation Report (Rev 1)

### 1. Executive verdict
Implemented

### 2. Baseline starting point
Pack M started from the fixed A-L runtime boundary already implemented and verified on the documented verification surface:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map -> merge_decision`

At start of this slice:
- Pack L `merge_decision.json` existed and was verified
- Rust `forge-evidence` existed, was callable, and was tested
- active runtime through Pack L did not yet invoke `forge-evidence`

### 3. Schema and config work
Files changed:
- `src/forge_eval/schemas/evidence_bundle.schema.json`
- `src/forge_eval/config.py`
- `src/forge_eval/stage_runner.py`

Config additions:
- `evidence_bundle_model_version` with locked supported value `evidence_bundle_rev1`

Validation behavior:
- `evidence_bundle` added to the known stage set, default enabled stages, stage order, and stage-to-artifact mapping
- `evidence_bundle` strictly requires `merge_decision`
- unsupported `evidence_bundle_model_version` fails closed with `config_error`
- emitted `evidence_bundle.json` is validated against a strict schema with `additionalProperties: false`

### 4. Evidence bundle stage implementation
Files changed:
- `src/forge_eval/stages/evidence_bundle.py`
- `src/forge_eval/services/evidence_bundle_model.py`
- `src/forge_eval/services/evidence_bundle_manifest.py`
- `src/forge_eval/services/evidence_bundle_summary.py`
- `src/forge_eval/evidence_cli.py`

Chosen Rust evidence runtime boundary:
- Path B: runtime `forge-evidence` integration begins at Pack M

Current truthful posture after this slice:
- Packs A-L remain Python-owned stage logic
- Pack M invokes `forge-evidence` only for canonical JSON, artifact ID, and hashchain work
- Pack M does not sign, publish, upload, deploy, or perform git actions

Emitted artifact:
- `evidence_bundle.json`

Artifact contents:
- deterministic run metadata
- explicit upstream input inventory
- ordered artifact list with `canonical_sha256`, `artifact_id`, and `file_size_bytes`
- bounded decision reference from `merge_decision.json`
- manifest with `forge-evidence-chain-v1` seed, chain hashes, and `final_chain_hash`
- explicit model/provenance showing `forge_evidence_cli` runtime integration

### 5. Test and verification results
Commands run:

```bash
python3 -m py_compile \
  src/forge_eval/evidence_cli.py \
  src/forge_eval/config.py \
  src/forge_eval/stage_runner.py \
  src/forge_eval/services/evidence_bundle_model.py \
  src/forge_eval/services/evidence_bundle_manifest.py \
  src/forge_eval/services/evidence_bundle_summary.py \
  src/forge_eval/stages/evidence_bundle.py \
  tests/_evidence_test_helper.py \
  tests/test_evidence_bundle_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q \
  tests/test_evidence_bundle_stage.py \
  tests/test_config.py \
  tests/test_schemas.py \
  tests/integration/test_review_findings_repo.py

cargo build --offline

FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packm-config.yml \
  --out /tmp/forge-eval-packm-smoke1

FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
PYTHONPATH=src python3 -m forge_eval.cli validate --artifacts /tmp/forge-eval-packm-smoke1

FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
PYTHONPATH=src python3 -m forge_eval.cli run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-packm-config.yml \
  --out /tmp/forge-eval-packm-smoke2

PYTHONPATH=src:/usr/lib/python3/dist-packages \
  /home/charlie/Forge/ecosystem/DataForge/.venv/bin/pytest -q -rA
```

Results:
- compile checks: pass
- scoped Pack M tests: pass
- full Python test suite: pass
- Rust evidence build: pass
- real A-M run: pass
- `forge-eval validate`: pass
- repeated identical runs: byte-identical across all primary artifacts, including `evidence_bundle.json`

Real Pack M emitted artifact set:
- `config.resolved.json`
- `risk_heatmap.json`
- `context_slices.json`
- `review_findings.json`
- `telemetry_matrix.json`
- `occupancy_snapshot.json`
- `capture_estimate.json`
- `hazard_map.json`
- `merge_decision.json`
- `evidence_bundle.json`

Observed real Pack M bundle summary:
- `final_decision = block`
- `artifact_count = 9`
- `dominant_hazard_tier = elevated`
- `final_chain_hash = 8b6396c58451fd82b2a3b3fb1080000f9ec9458886f1ed522ddaf2e05eaea457`

Fail-closed probes executed:
- invalid config model version -> `config_error`
- missing `merge_decision.json` during validate -> `validation_error`
- malformed `hazard_map.json` during validate -> `validation_error`
- invalid `evidence_bundle.json` shape (artifact list too short) -> `validation_error`
- missing runtime evidence binary -> `evidence_cli_error`

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
- `doc/system/17-merge-decision-stage.md`
- `doc/system/18-evidence-bundle-stage.md`
- `doc/feSYSTEM.md`

New implemented boundary documented:

`config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate -> hazard_map -> merge_decision -> evidence_bundle`

Doc rebuild command:

```bash
bash doc/system/BUILD.sh
```

Rebuild result:
- `feSYSTEM.md rebuilt (1293 lines)`

### 7. Remaining open items
None confirmed inside the Pack M scope.

### 8. Recommended next actions
1. Verify and document the next post-Pack-M boundary before adding any governance execution behavior.
2. Keep release/publish/signing behavior out of Forge Eval unless a later pack explicitly owns it.
