# Forge Eval A–J Verification Report (Rev 1)

### 1. Executive verdict

Verified with gaps.

Core runtime verification succeeded for Packs A–J on a real local target repository:

- Rust evidence binary built and was directly callable.
- `forge-eval run` emitted the full expected artifact set.
- `forge-eval validate` succeeded on the emitted artifacts.
- Two identical runs were byte-identical across all primary artifacts.
- Controlled fail-closed probes triggered correctly.

Confirmed gaps remain:

- offline Python install does not satisfy the declared dependency floor because the local machine only has `jsonschema 4.10.3`, while `pyproject.toml` requires `jsonschema>=4.22.0`
- Rust integration CLI tests are failing because they cannot find the compiled binary at runtime
- the Rust evidence binary is implemented and callable, but it is not wired into the main A–J pipeline path

### 2. Repository and environment

- Forge Eval repo: `/home/charlie/Forge/ecosystem/forge-eval/repo`
- Target repo: `/home/charlie/Forge/ecosystem/DataForge`
- Base ref: `eea89609d5e32d61f85e658f05cc8f573fb6fd29`
- Head ref: `c8fe082d8d7c8cdb74c4ec7d0f727af306c40051`
- Selection reason: real local Forge repo, safe to inspect, small but non-trivial one-commit diff (`2 files changed, 21 insertions`)
- Python version: `3.12.3`
- Rust version: `rustc 1.93.0 (254b59607 2026-01-19)`
- Cargo version: `1.93.0 (083ac5135 2025-12-15)`

Short implementation inventory:

| Surface | Location | Status |
|---|---|---|
| CLI entrypoint | `src/forge_eval/cli.py` | Confirmed |
| Stage runner | `src/forge_eval/stage_runner.py` | Confirmed |
| Stage modules | `src/forge_eval/stages/*.py` | Confirmed |
| Schemas | `src/forge_eval/schemas/*.schema.json` | Confirmed |
| Rust evidence binary | `rust/forge-evidence` | Confirmed |
| Pack A–J Python tests | `tests/` | Confirmed |
| Rust tests | `rust/forge-evidence/tests` | Confirmed |

Stage module inventory confirmed:

- `risk_heatmap.py`
- `context_slices.py`
- `reviewer_execution.py`
- `telemetry_matrix.py`
- `occupancy_snapshot.py`
- `capture_estimate.py`

### 3. Build and install results

Commands used:

```bash
cd /home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence
cargo build --offline

rm -rf /tmp/forge-eval-verify-venv
python3 -m venv --system-site-packages /tmp/forge-eval-verify-venv
/tmp/forge-eval-verify-venv/bin/python -m pip install -e /home/charlie/Forge/ecosystem/forge-eval/repo
/tmp/forge-eval-verify-venv/bin/python -m pip install --no-build-isolation --no-deps -e /home/charlie/Forge/ecosystem/forge-eval/repo
```

Results:

- Rust build result: success
- Rust build output: `rust/forge-evidence/target/debug/forge-evidence`
- Python install result: partial

Details:

- `cargo build --offline` succeeded.
- `pip install -e .` failed offline because the local machine could not satisfy `jsonschema>=4.22.0` from the network-disabled environment.
- Local installed version available on the machine was `jsonschema 4.10.3`.
- `pip install --no-build-isolation --no-deps -e .` succeeded and allowed CLI execution, but this bypassed dependency resolution.

Assessment:

- Rust build is verified.
- Python package code is installable.
- Full dependency-satisfied editable install is not verified in this offline environment.

Evidence binary availability:

```bash
/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence sha256 /tmp/forge-eval-aj-run-a/config.resolved.json
/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence artifact-id --kind risk_heatmap /tmp/forge-eval-aj-run-a/risk_heatmap.json
```

Observed outputs:

- SHA-256 of `config.resolved.json`: `08824e951205e7d62b5b012f8c0deb509d35019c36bf8bf0dc48046cd4ffe62c`
- Deterministic artifact id for `risk_heatmap.json`: `fcd430a3db79572ff60715ef0dbd8ac5db762f63248a592a51b2a7d7317ed41a`

### 4. CLI verification

Commands used:

```bash
/tmp/forge-eval-verify-venv/bin/forge-eval --help
/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence --help
```

Confirmed commands:

- `forge-eval run`
- `forge-eval validate`
- `forge-evidence canonicalize`
- `forge-evidence sha256`
- `forge-evidence artifact-id`
- `forge-evidence hashchain`

Help output summary:

- Python CLI exposes exactly `run` and `validate`.
- Rust CLI exposes exactly `canonicalize`, `sha256`, `artifact-id`, and `hashchain`.

Deviations:

- none in the CLI surface itself

### 5. Real run results

Test config used:

- Path: `/tmp/forge-eval-aj-verify-config.yaml`
- Contents:

```yaml
{}
```

This was a minimal explicit test config. `load_config()` normalized it to the repo defaults.

Exact run command:

```bash
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
/tmp/forge-eval-verify-venv/bin/forge-eval run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-aj-verify-config.yaml \
  --out /tmp/forge-eval-aj-run-a
```

Exit result:

- exit code `0`
- stdout payload:

```json
{"result":{"artifacts_written":["config.resolved.json","risk_heatmap.json","context_slices.json","review_findings.json","telemetry_matrix.json","occupancy_snapshot.json","capture_estimate.json"],"base_commit":"eea89609d5e32d61f85e658f05cc8f573fb6fd29","head_commit":"c8fe082d8d7c8cdb74c4ec7d0f727af306c40051","run_id":"d5420d29d8bc811a"},"status":"ok"}
```

Emitted artifacts:

- `/tmp/forge-eval-aj-run-a/config.resolved.json`
- `/tmp/forge-eval-aj-run-a/risk_heatmap.json`
- `/tmp/forge-eval-aj-run-a/context_slices.json`
- `/tmp/forge-eval-aj-run-a/review_findings.json`
- `/tmp/forge-eval-aj-run-a/telemetry_matrix.json`
- `/tmp/forge-eval-aj-run-a/occupancy_snapshot.json`
- `/tmp/forge-eval-aj-run-a/capture_estimate.json`

Artifact notes:

- `run_id` was consistent across all artifacts.
- Packs G–J store `run_id` under `run.run_id`, not at the top level.
- Observed summaries:
  - `risk_heatmap.json`: `target_count=2`
  - `context_slices.json`: `slice_count=3`, `total_line_count=93`
  - `review_findings.json`: `finding_count=2`, `reviewer_ok_count=3`
  - `telemetry_matrix.json`: `defect_count=2`, `k_eff=2`
  - `occupancy_snapshot.json`: `mean_psi_post=0.826667`
  - `capture_estimate.json`: `selected_hidden=1.0`, `selected_total=3.0`, `selected_method=max_hidden`

### 6. Validation results

Exact validation command:

```bash
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
/tmp/forge-eval-verify-venv/bin/forge-eval validate --artifacts /tmp/forge-eval-aj-run-a
```

Result:

- exit code `0`
- stdout payload:

```json
{"result":{"artifacts_dir":"/tmp/forge-eval-aj-run-a","expected_artifacts":["risk_heatmap.json","context_slices.json","review_findings.json","telemetry_matrix.json","occupancy_snapshot.json","capture_estimate.json"],"validated_files":["capture_estimate.json","context_slices.json","occupancy_snapshot.json","review_findings.json","risk_heatmap.json","telemetry_matrix.json"]},"status":"ok"}
```

Schema and consistency notes:

- presence validation: confirmed
- per-artifact schema validation: confirmed
- `config.resolved.json` correctly drove expected-artifact derivation
- `run_id` consistency across artifacts: confirmed by direct inspection
- important limitation: `forge-eval validate` does not perform deep cross-artifact semantic checks beyond presence and schema; those checks are enforced during stage execution

### 7. Determinism results

Run A path:

- `/tmp/forge-eval-aj-run-a`

Run B path:

- `/tmp/forge-eval-aj-run-b`

Exact second run command:

```bash
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence \
/tmp/forge-eval-verify-venv/bin/forge-eval run \
  --repo /home/charlie/Forge/ecosystem/DataForge \
  --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 \
  --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 \
  --config /tmp/forge-eval-aj-verify-config.yaml \
  --out /tmp/forge-eval-aj-run-b
```

Byte-comparison result by artifact:

| Artifact | Result |
|---|---|
| `config.resolved.json` | byte-identical |
| `risk_heatmap.json` | byte-identical |
| `context_slices.json` | byte-identical |
| `review_findings.json` | byte-identical |
| `telemetry_matrix.json` | byte-identical |
| `occupancy_snapshot.json` | byte-identical |
| `capture_estimate.json` | byte-identical |

Overall verdict:

- determinism verified for the full current A–J runtime artifact set

### 8. Fail-closed probe results

| Probe name | Expected behavior | Actual behavior | Verdict |
|---|---|---|---|
| Invalid config key | reject config with `config_error` | `unknown config keys` with `details.keys=["unknown_top_level_key"]` | Pass |
| Invalid stage dependency | reject `capture_estimate` without `occupancy_snapshot` | `capture_estimate stage requires occupancy_snapshot stage to be enabled` | Pass |
| Missing required artifact during validate | `validate` fails with `validation_error` | missing `telemetry_matrix.json` produced `required artifact is missing` | Pass |
| Malformed JSON artifact | `validate` fails with `validation_error` | corrupt `risk_heatmap.json` produced `artifact file is invalid JSON` | Pass |
| Reviewer failure under `record_and_continue` | reviewer failure recorded, stage does not raise | patched reviewer raised `RuntimeError`; stage emitted reviewer `status=failed`, `finding_count=0` | Pass |
| Cross-artifact run mismatch | Pack J stage rejects mismatch | patched `occupancy_snapshot.run.run_id` produced `stage_error` `run_id mismatch across pipeline, telemetry, and occupancy artifacts` | Pass |

Exact probe commands:

```bash
cat > /tmp/forge-eval-aj-fail-invalid-key.yaml <<'EOF'
unknown_top_level_key: true
EOF
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence /tmp/forge-eval-verify-venv/bin/forge-eval run --repo /home/charlie/Forge/ecosystem/DataForge --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 --config /tmp/forge-eval-aj-fail-invalid-key.yaml --out /tmp/forge-eval-aj-fail-invalid-key

cat > /tmp/forge-eval-aj-fail-stage-deps.yaml <<'EOF'
enabled_stages:
  - capture_estimate
EOF
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence /tmp/forge-eval-verify-venv/bin/forge-eval run --repo /home/charlie/Forge/ecosystem/DataForge --base eea89609d5e32d61f85e658f05cc8f573fb6fd29 --head c8fe082d8d7c8cdb74c4ec7d0f727af306c40051 --config /tmp/forge-eval-aj-fail-stage-deps.yaml --out /tmp/forge-eval-aj-fail-stage-deps

cp -R /tmp/forge-eval-aj-run-a /tmp/forge-eval-aj-fail-missing-artifact
rm -f /tmp/forge-eval-aj-fail-missing-artifact/telemetry_matrix.json
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence /tmp/forge-eval-verify-venv/bin/forge-eval validate --artifacts /tmp/forge-eval-aj-fail-missing-artifact

cp -R /tmp/forge-eval-aj-run-a /tmp/forge-eval-aj-fail-malformed-json
printf '{invalid json\n' > /tmp/forge-eval-aj-fail-malformed-json/risk_heatmap.json
FORGE_EVIDENCE_BIN=/home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence/target/debug/forge-evidence /tmp/forge-eval-verify-venv/bin/forge-eval validate --artifacts /tmp/forge-eval-aj-fail-malformed-json
```

Additional stage-level probes used for the last two rows were executed through direct Python imports from the installed package code.

### 9. Documentation alignment audit

| Area | Documented expectation | Implementation evidence | Status |
|---|---|---|---|
| Stage order | Docs use `config -> risk_heatmap -> context_slices -> review_findings -> telemetry_matrix -> occupancy_snapshot -> capture_estimate` and also a fixed stage list starting at `risk_heatmap` | `STAGE_ORDER` is `risk_heatmap` through `capture_estimate`; `config.resolved.json` is written before stages | Partial |
| Artifact names | Docs list `config.resolved.json`, `risk_heatmap.json`, `context_slices.json`, `review_findings.json`, `telemetry_matrix.json`, `occupancy_snapshot.json`, `capture_estimate.json` | Real run emitted exactly that set | Matches |
| Schema files | Docs list schema files for Packs G–J and the current emitted artifacts | A–J schema files exist and validate runtime artifacts successfully | Matches |
| Reviewer execution stage | Docs describe `reviewer_execution_v1`, reviewer statuses `ok/failed/skipped`, deterministic findings, reviewer-independent `defect_key` | Real run and direct failure probe matched this behavior | Matches |
| Telemetry matrix stage | Docs describe tri-state matrix, cross-reviewer coalescing, conservative `k_eff`, and fail-closed duplicate handling | Real run emitted tri-state output and `k_eff=2`; tests cover coalescing and duplicate fail-closed paths | Matches |
| Occupancy snapshot stage | Docs describe bounded `psi_post` with conservative suppression semantics and run consistency checks | Real run emitted `mean_psi_post=0.826667`; stage-level mismatch probes fail closed | Matches |
| Capture estimate stage | Docs describe cross-artifact checks, Chao1, ICE, and `max_hidden` selection | Real run emitted Chao1/ICE/selected hidden estimate; run mismatch probe failed closed | Matches |
| Error classes | Docs list `ConfigError`, `ValidationError`, `StageError`, `EvidenceCliError` | Code also defines `GitError` in `src/forge_eval/errors.py` | Partial |
| Runbook commands | Docs say `cargo build --offline`, `pip install -e .`, `forge-eval run`, `forge-eval validate` | Build/run/validate commands are correct; plain `pip install -e .` was not satisfiable offline on this machine because declared dependency floor could not be resolved | Partial |
| README verification status text | README says A–F were real-target verified, while G–J were covered by tests/smoke runs | This audit verified A–J on a real local target repo | Diverges |
| Rust evidence runtime activation | README says the Rust evidence subsystem is implemented and wrapped, but not yet wired into the main evaluation path | `src/forge_eval/evidence_cli.py` exists; no main pipeline wiring was observed in `stage_runner.py` or stage modules | Matches |

### 10. Test suite audit

Commands used:

```bash
cd /home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence
cargo test --offline

cd /home/charlie/Forge/ecosystem/forge-eval/repo
PYTHONPATH=src /home/charlie/Forge/ecosystem/forge-smithy/.venv/bin/python -m pytest -q -rA
```

Results:

- Python tests: pass
- Python collected tests: `91`
- Rust tests: partial

Rust details:

- unit tests in `src/main.rs`: `5 passed`
- integration CLI tests in `tests/integration_cli.rs`: `5 failed`
- failure mode: every integration CLI test failed with `Os { code: 2, kind: NotFound, message: "No such file or directory" }` while trying to execute `env!("CARGO_BIN_EXE_forge-evidence")`

Python details:

- stage tests present for Packs E–J
- integration tests present for:
  - `risk_heatmap`
  - `context_slices`
  - `review_findings` + `telemetry_matrix` + `occupancy_snapshot` + `capture_estimate`
- observed result: full Python test pass under an existing local venv with `pytest`

Missing or weak coverage observed:

- Rust CLI integration tests are present but currently failing
- mainline pipeline use of the Rust evidence wrapper is not covered because the wrapper is not yet wired into the stage pipeline
- `forge-eval validate` cross-artifact semantic verification is not implemented; those invariants are enforced at stage runtime instead

### 11. Gaps and blocking findings

Confirmed gaps:

1. Declared Python dependency floor is not currently satisfiable offline on this machine.
   - `pyproject.toml` requires `jsonschema>=4.22.0`
   - local machine only had `jsonschema 4.10.3`
   - plain `pip install -e .` failed

2. Rust integration CLI tests are broken.
   - `cargo test --offline` failed 5 integration tests in `rust/forge-evidence/tests/integration_cli.rs`
   - all failures were binary-launch failures, not logic assertion failures

3. Rust evidence binary is not wired into the main A–J runtime path.
   - it is implemented and callable
   - live pipeline orchestration does not currently invoke `evidence_cli.py`

4. Documentation drift exists in the README verification status text.
   - current README understates real-target verification for Packs G–J

### 12. Recommended next actions

1. Fix the Python packaging path so `pip install -e .` succeeds in the intended offline/dev environment without `--no-deps` workarounds.
2. Fix `rust/forge-evidence` integration CLI test binary resolution so `cargo test --offline` passes end to end.
3. Decide whether Rust evidence primitives should remain callable-but-unwired or be integrated into the primary pipeline artifact path.
4. Refresh the Forge Eval README verification status so it reflects the current A–J real-run verification evidence.
