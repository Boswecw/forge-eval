from __future__ import annotations

from pathlib import Path

import pytest

from forge_eval.config import normalize_config
from forge_eval.errors import StageError
from forge_eval.stages.occupancy_snapshot import run_stage


def _telemetry_artifact() -> dict[str, object]:
    return {
        "artifact_version": 1,
        "kind": "telemetry_matrix",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "basec",
            "head_commit": "headc",
            "review_findings_artifact": "review_findings.json",
        },
        "reviewers": [
            {
                "reviewer_id": "r1",
                "status": "ok",
                "kind": "changed_lines",
                "eligible": True,
                "usable": True,
                "failed": False,
                "skipped": False,
                "findings_emitted": 1,
                "slices_seen": 2,
                "error": None,
            },
            {
                "reviewer_id": "r2",
                "status": "ok",
                "kind": "changed_lines",
                "eligible": True,
                "usable": True,
                "failed": False,
                "skipped": False,
                "findings_emitted": 0,
                "slices_seen": 2,
                "error": None,
            },
            {
                "reviewer_id": "r3",
                "status": "failed",
                "kind": "structural_risk",
                "eligible": False,
                "usable": False,
                "failed": True,
                "skipped": False,
                "findings_emitted": 0,
                "slices_seen": 1,
                "error": "timeout",
            },
        ],
        "defects": [
            {
                "defect_key": "dfk_" + ("a" * 64),
                "file_path": "a.py",
                "category": "consistency",
                "severity": "high",
                "reported_by": ["r1"],
                "support_count": 1,
            },
            {
                "defect_key": "dfk_" + ("b" * 64),
                "file_path": "b.py",
                "category": "correctness",
                "severity": "medium",
                "reported_by": ["r1"],
                "support_count": 1,
            },
            {
                "defect_key": "dfk_" + ("c" * 64),
                "file_path": "c.py",
                "category": "correctness",
                "severity": "medium",
                "reported_by": ["r1"],
                "support_count": 1,
            },
            {
                "defect_key": "dfk_" + ("d" * 64),
                "file_path": "README.md",
                "category": "docs",
                "severity": "low",
                "reported_by": ["r1"],
                "support_count": 1,
            },
        ],
        "matrix": [
            {
                "defect_key": "dfk_" + ("a" * 64),
                "observations": {"r1": 1, "r2": 0, "r3": None},
                "k_eff_defect": 2,
            },
            {
                "defect_key": "dfk_" + ("b" * 64),
                "observations": {"r1": 0, "r2": None, "r3": None},
                "k_eff_defect": 1,
            },
            {
                "defect_key": "dfk_" + ("c" * 64),
                "observations": {"r1": 0, "r2": 0, "r3": None},
                "k_eff_defect": 2,
            },
            {
                "defect_key": "dfk_" + ("d" * 64),
                "observations": {"r1": None, "r2": None, "r3": None},
                "k_eff_defect": 0,
            },
        ],
        "summary": {
            "k_configured": 3,
            "k_executed": 3,
            "k_failed": 1,
            "k_skipped": 0,
            "k_usable": 2,
            "k_eff": 0,
            "defect_count": 4,
            "matrix_rows": 4,
            "cells_observed": 1,
            "cells_missed": 3,
            "cells_null": 8,
        },
        "provenance": {
            "algorithm": "telemetry_matrix_v1",
            "deterministic": True,
            "inputs": ["review_findings.json"],
            "applicability_mode": "reviewer_kind_scope_v1",
            "k_eff_mode": "global_min_per_defect",
        },
    }


def test_occupancy_snapshot_stage_semantics_and_bounds() -> None:
    cfg = normalize_config({})
    out = run_stage(
        repo_path=Path("/tmp/repo"),
        base_ref="base",
        head_ref="head",
        run_id="run",
        config=cfg,
        telemetry_matrix_artifact=_telemetry_artifact(),
    )

    assert out["kind"] == "occupancy_snapshot"
    assert out["artifact_version"] == 1

    rows = {row["defect_key"]: row for row in out["rows"]}
    psi_a = rows["dfk_" + ("a" * 64)]["psi_post"]
    psi_b = rows["dfk_" + ("b" * 64)]["psi_post"]
    psi_c = rows["dfk_" + ("c" * 64)]["psi_post"]
    psi_d = rows["dfk_" + ("d" * 64)]["psi_post"]

    for row in out["rows"]:
        assert 0.0 <= row["psi_post"] <= 1.0

    # observed defects retain higher occupancy than miss-dominated rows
    assert psi_a > psi_c
    # stronger usable coverage suppresses more than weak usable coverage
    assert psi_c < psi_b
    # null-heavy sparse coverage remains uncertain instead of collapsing low
    assert psi_d >= 0.60

    assert out["summary"]["global_k_eff"] == 0
    assert out["model"]["name"] == "occupancy_rev1"


def test_occupancy_snapshot_run_id_mismatch_fails_closed() -> None:
    cfg = normalize_config({})
    with pytest.raises(StageError):
        run_stage(
            repo_path=Path("/tmp/repo"),
            base_ref="base",
            head_ref="head",
            run_id="wrong-run",
            config=cfg,
            telemetry_matrix_artifact=_telemetry_artifact(),
        )


def test_occupancy_snapshot_illegal_cell_value_fails_closed() -> None:
    cfg = normalize_config({})
    artifact = _telemetry_artifact()
    artifact["matrix"][0]["observations"]["r2"] = 2

    with pytest.raises(StageError):
        run_stage(
            repo_path=Path("/tmp/repo"),
            base_ref="base",
            head_ref="head",
            run_id="run",
            config=cfg,
            telemetry_matrix_artifact=artifact,
        )


def test_occupancy_snapshot_keff_mismatch_fails_closed() -> None:
    cfg = normalize_config({})
    artifact = _telemetry_artifact()
    artifact["matrix"][1]["k_eff_defect"] = 2

    with pytest.raises(StageError):
        run_stage(
            repo_path=Path("/tmp/repo"),
            base_ref="base",
            head_ref="head",
            run_id="run",
            config=cfg,
            telemetry_matrix_artifact=artifact,
        )


def test_occupancy_snapshot_invalid_config_value_fails_closed() -> None:
    cfg = normalize_config({})
    cfg["occupancy_detection_assumption"] = 1.5

    with pytest.raises(StageError):
        run_stage(
            repo_path=Path("/tmp/repo"),
            base_ref="base",
            head_ref="head",
            run_id="run",
            config=cfg,
            telemetry_matrix_artifact=_telemetry_artifact(),
        )
