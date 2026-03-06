# Forge Eval Post-Verification Hardening Report (Rev 1)

### 1. Executive summary

Hardened.

The four confirmed post-verification hardening targets were addressed without expanding runtime scope beyond the current A-J boundary.

- Rust CLI integration tests now resolve and launch the real compiled `forge-evidence` binary.
- Python packaging metadata and install guidance now match the current code/test surface and the verified offline dev workflow.
- Rust evidence posture is now explicit: callable and tested, but not part of the main A-J stage pipeline.
- README verification status now reflects the completed real-run A-J verification.

### 2. Input verification baseline

Starting point from `reports/forge_eval_a_to_j_verification_report_rev1.md`:

- A-J runtime path verified on a real local target repo
- expected artifacts emitted
- `forge-eval validate` passed
- primary artifacts were byte-stable across repeated runs
- fail-closed probes were confirmed
- Python tests passed
- Rust unit tests passed

Confirmed gaps at the start of this hardening slice:

1. Rust integration CLI tests could not locate the compiled binary
2. offline editable install did not satisfy the declared dependency floor on the local machine
3. Rust evidence integration posture was real but not explicit enough in the repo text
4. README verification status understated the current A-J verification state

### 3. Rust integration-test hardening

Files inspected:

- `rust/forge-evidence/tests/integration_cli.rs`
- `rust/forge-evidence/Cargo.toml`
- compiled test binary strings and target outputs under `rust/forge-evidence/target/`

Root cause:

- the integration test binary had a stale absolute `CARGO_BIN_EXE_forge-evidence` path baked into it from an older checkout location
- when that compile-time path no longer existed, `Command::new(...)` failed with `Os { code: 2, kind: NotFound, message: "No such file or directory" }`
- the defect was in test-side binary resolution, not in the Rust binary implementation itself

Changes made:

- added a small `resolve_bin()` helper in `rust/forge-evidence/tests/integration_cli.rs`
- resolution order is now:
  1. `CARGO_BIN_EXE_forge-evidence` if present and the file exists
  2. fallback derived from `current_exe()` to `target/debug/forge-evidence`
  3. fallback derived from `CARGO_MANIFEST_DIR/target/debug/forge-evidence`
- kept the tests executing the real compiled binary
- did not weaken the integration tests or replace them with unit-only coverage

Exact test command:

```bash
cd /home/charlie/Forge/ecosystem/forge-eval/repo/rust/forge-evidence
cargo test --offline
```

Result:

- pass
- Rust test totals after the fix:
  - unit tests: `5 passed`
  - integration CLI tests: `5 passed`

### 4. Packaging/install posture audit

Files inspected:

- `pyproject.toml`
- `src/forge_eval/validation/validate_artifact.py`
- `src/forge_eval/validation/schema_loader.py`
- `README.md`
- `doc/system/11-handover-runbook.md`

Dependency-floor assessment:

- current code only imports `Draft202012Validator` from `jsonschema`
- the local machine's `jsonschema 4.10.3` provides that validator
- the full Python test suite passed against `jsonschema 4.10.3`
- therefore the previous floor `jsonschema>=4.22.0` was stricter than the current code/test evidence supports

Changes made:

- lowered the declared dependency floor in `pyproject.toml` from `jsonschema>=4.22.0` to `jsonschema>=4.10.3`
- updated README and runbook install guidance to distinguish:
  - networked/default install: `pip install -e .`
  - offline/pre-provisioned install: `pip install --no-build-isolation -e .`
- documented that offline plain `pip install -e .` still fails because pip's isolated build environment attempts to fetch build requirements from an index

Exact commands:

```bash
rm -rf /tmp/forge-eval-harden-venv
python3 -m venv --system-site-packages /tmp/forge-eval-harden-venv
/tmp/forge-eval-harden-venv/bin/python -m pip install -e /home/charlie/Forge/ecosystem/forge-eval/repo
/tmp/forge-eval-harden-venv/bin/python -m pip install --no-build-isolation -e /home/charlie/Forge/ecosystem/forge-eval/repo
PYTHONPATH=src /home/charlie/Forge/ecosystem/forge-smithy/.venv/bin/python -m pytest -q -rA
```

Result:

- plain offline `pip install -e .`: still fails, now clearly attributable to build-isolation trying to fetch `setuptools>=68`
- offline `pip install --no-build-isolation -e .`: passes cleanly with:
  - `PyYAML 6.0.1`
  - `jsonschema 4.10.3`
- full Python test suite after the metadata/doc changes: pass (`91` tests)
- packaging posture is now truthful and reproducible for the intended offline dev environment

### 5. Evidence integration posture

Files inspected:

- `src/forge_eval/evidence_cli.py`
- `src/forge_eval/stage_runner.py`
- `doc/system/02-architecture.md`
- `doc/system/06-evidence-subsystem.md`
- `doc/system/11-handover-runbook.md`
- `README.md`

Current truthful posture:

- `forge-evidence` is implemented, directly callable, and tested
- `evidence_cli.py` is implemented as a fail-closed Python wrapper
- the current A-J mainline stage pipeline does not invoke the evidence wrapper during `forge-eval run` or `forge-eval validate`
- downstream evidence bundle assembly remains out of scope

Changes made:

- added an explicit posture note to `src/forge_eval/evidence_cli.py`
- updated architecture, evidence-subsystem, runbook, and README text so they all state the same boundary

Remaining boundary:

- Rust evidence remains a verified helper subsystem, not a mainline runtime stage dependency, until a later explicit slice wires evidence primitives into emitted artifact handling or bundle assembly

### 6. README / documentation refresh

Files changed:

- `README.md`
- `doc/system/02-architecture.md`
- `doc/system/06-evidence-subsystem.md`
- `doc/system/11-handover-runbook.md`
- `doc/feSYSTEM.md` (rebuilt)

Status wording updated:

- README now states that the current A-J runtime path has been verified on a real local target repo
- README now references `reports/forge_eval_a_to_j_verification_report_rev1.md`
- README now keeps downstream packs explicitly out of scope
- install guidance now distinguishes networked/default install from offline/pre-provisioned install
- evidence posture wording now explicitly says callable-and-tested but not mainline in the current A-J pipeline

Result:

- repo text no longer understates the current verified state
- code/docs/README align on the current evidence boundary and install posture
- assembled system reference rebuilt successfully with:

```bash
bash /home/charlie/Forge/ecosystem/forge-eval/repo/doc/system/BUILD.sh
```

### 7. Remaining open items

None from this hardening slice.

The current non-mainline evidence posture is intentional and documented, not an unresolved defect.

### 8. Recommended next actions

1. If a later slice needs evidence-grade artifact IDs or hashchains in the main runtime path, wire `evidence_cli.py` into that path explicitly rather than implying partial integration.
2. If offline installs need to work without `--no-build-isolation`, add a wheel cache or another provisioned build-dependency path instead of weakening the documented workflow.
