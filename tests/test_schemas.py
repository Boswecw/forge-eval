from __future__ import annotations

import copy

import pytest

from forge_eval.errors import ValidationError
from forge_eval.validation.schema_loader import SCHEMA_BY_ARTIFACT, load_all_schemas
from forge_eval.validation.validate_artifact import validate_instance


VALID_EXAMPLES = {
    "risk_heatmap": {
        "schema_version": "v1",
        "kind": "risk_heatmap",
        "run_id": "run",
        "repo_path": "/tmp/repo",
        "base_ref": "base",
        "head_ref": "head",
        "weights": {"w_churn": 0.4, "w_centrality": 0.4, "w_change_magnitude": 0.2},
        "targets": [],
        "summary": {"target_count": 0, "min_risk_score": 0.0, "max_risk_score": 0.0},
        "provenance": {"algorithm": "risk", "deterministic": True},
    },
    "context_slices": {
        "schema_version": "v1",
        "kind": "context_slices",
        "run_id": "run",
        "repo_path": "/tmp/repo",
        "base_ref": "base",
        "head_ref": "head",
        "config": {
            "context_radius_lines": 12,
            "merge_gap_lines": 2,
            "max_slices_per_target": 8,
            "max_lines_per_slice": 120,
            "max_total_lines": 1200,
            "fail_on_slice_truncation": True,
            "binary_file_policy": "fail",
        },
        "slices": [],
        "summary": {"target_count": 0, "slice_count": 0, "total_line_count": 0},
        "provenance": {
            "algorithm": "slices",
            "head_version_content": True,
            "deterministic": True,
        },
    },
    "review_findings": {
        "schema_version": "v1",
        "kind": "review_findings",
        "run_id": "run",
        "reviewers": [{"reviewer_id": "r1", "reviewer_type": "rule"}],
        "findings": [],
        "provenance": {"algorithm": "review"},
    },
    "telemetry_matrix": {
        "schema_version": "v1",
        "kind": "telemetry_matrix",
        "run_id": "run",
        "methods": ["m1"],
        "targets": ["t1"],
        "matrix": {"t1": {"m1": 1}},
        "method_health": [{"method_id": "m1", "status": "OK", "error_summary": None}],
        "avg_pairwise_corr": None,
        "k_eff": None,
        "fail_closed": False,
        "provenance": {"algorithm": "telemetry"},
    },
    "occupancy_snapshot": {
        "schema_version": "v1",
        "kind": "occupancy_snapshot",
        "run_id": "run",
        "per_target": [
            {
                "target_id": "t1",
                "risk_bucket": "medium",
                "psi_prior": 0.5,
                "psi_post": 0.6,
                "detected_any": True,
                "methods_included": ["m1"],
            }
        ],
        "provenance": {"algorithm": "occupancy"},
    },
    "capture_estimate": {
        "schema_version": "v1",
        "kind": "capture_estimate",
        "run_id": "run",
        "estimate": 5.2,
        "method_count": 2,
        "target_count": 3,
        "confidence_interval": {"lower": 1.0, "upper": 9.0},
        "provenance": {"algorithm": "capture"},
    },
    "calibration_report": {
        "schema_version": "v1",
        "kind": "calibration_report",
        "run_id": "run",
        "calibration_status": "not_run",
        "priors": [{"method_id": "m1", "p_detect": 0.4}],
        "posteriors": [{"method_id": "m1", "p_detect": 0.4}],
        "provenance": {"algorithm": "calibration"},
    },
    "hazard_map": {
        "schema_version": "v1",
        "kind": "hazard_map",
        "run_id": "run",
        "hazards": [{"target_id": "t1", "lambda_hat": 0.3, "uncertainty": 0.1}],
        "provenance": {"algorithm": "hazard"},
    },
    "merge_decision": {
        "schema_version": "v1",
        "kind": "merge_decision",
        "run_id": "run",
        "decision": "REVIEW",
        "rationale": "insufficient evidence",
        "thresholds": {"hazard_threshold": 0.75, "occupancy_threshold": 0.75},
        "provenance": {"algorithm": "merge-policy"},
    },
    "evidence_bundle": {
        "schema_version": "v1",
        "kind": "evidence_bundle",
        "run_id": "run",
        "artifact_manifest": [
            {
                "kind": "risk_heatmap",
                "path": "risk_heatmap.json",
                "sha256": "a" * 64,
                "artifact_id": "b" * 64,
            }
        ],
        "hashchain": {
            "chain_hashes": ["c" * 64],
            "final_chain_hash": "c" * 64,
        },
        "final_sha256": "d" * 64,
        "provenance": {"algorithm": "evidence"},
    },
}


def test_schema_loader_loads_all() -> None:
    schemas = load_all_schemas()
    assert sorted(schemas.keys()) == sorted(SCHEMA_BY_ARTIFACT.keys())


@pytest.mark.parametrize("kind", sorted(VALID_EXAMPLES.keys()))
def test_schema_accepts_valid_examples(kind: str) -> None:
    schemas = load_all_schemas()
    validate_instance(VALID_EXAMPLES[kind], schemas[kind], artifact_kind=kind)


@pytest.mark.parametrize("kind", sorted(VALID_EXAMPLES.keys()))
def test_schema_rejects_invalid_examples(kind: str) -> None:
    schemas = load_all_schemas()
    broken = copy.deepcopy(VALID_EXAMPLES[kind])
    broken.pop("run_id", None)
    with pytest.raises(ValidationError):
        validate_instance(broken, schemas[kind], artifact_kind=kind)
