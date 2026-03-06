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
        "artifact_version": 1,
        "kind": "review_findings",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "aaa",
            "head_commit": "bbb",
            "slice_artifact": "context_slices.json",
            "risk_artifact": "risk_heatmap.json",
        },
        "reviewers": [
            {
                "reviewer_id": "r1",
                "kind": "changed_lines",
                "status": "ok",
                "slices_seen": 2,
                "findings_emitted": 1,
                "error": None,
            }
        ],
        "findings": [
            {
                "defect_key": "dfk_" + ("a" * 64),
                "reviewer_id": "r1",
                "file_path": "a.py",
                "slice_id": "a.py:1:2",
                "title": "title",
                "description": "description",
                "severity": "medium",
                "confidence": 0.8,
                "category": "consistency",
                "line_start": 1,
                "line_end": 2,
                "evidence": {"anchors": ["a.py:1:2"], "signals": ["changed_lines"]},
            }
        ],
        "summary": {
            "reviewer_count": 1,
            "reviewer_ok_count": 1,
            "reviewer_failed_count": 0,
            "reviewer_skipped_count": 0,
            "finding_count": 1,
            "finding_count_by_severity": {"low": 0, "medium": 1, "high": 0, "critical": 0},
        },
        "provenance": {
            "algorithm": "reviewer_execution_v1",
            "deterministic": True,
            "reviewer_failure_policy": "fail_stage",
            "inputs": ["context_slices.json", "risk_heatmap.json"],
        },
    },
    "telemetry_matrix": {
        "artifact_version": 1,
        "kind": "telemetry_matrix",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "aaa",
            "head_commit": "bbb",
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
            }
        ],
        "defects": [
            {
                "defect_key": "dfk_" + ("b" * 64),
                "file_path": "a.py",
                "category": "consistency",
                "severity": "medium",
                "reported_by": ["r1"],
                "support_count": 1,
            }
        ],
        "matrix": [
            {
                "defect_key": "dfk_" + ("b" * 64),
                "observations": {"r1": 1},
                "k_eff_defect": 1,
            }
        ],
        "summary": {
            "k_configured": 1,
            "k_executed": 1,
            "k_failed": 0,
            "k_skipped": 0,
            "k_usable": 1,
            "k_eff": 1,
            "defect_count": 1,
            "matrix_rows": 1,
            "cells_observed": 1,
            "cells_missed": 0,
            "cells_null": 0,
        },
        "provenance": {
            "algorithm": "telemetry_matrix_v1",
            "deterministic": True,
            "inputs": ["review_findings.json"],
            "applicability_mode": "reviewer_kind_scope_v1",
            "k_eff_mode": "global_min_per_defect",
        },
    },
    "occupancy_snapshot": {
        "artifact_version": 1,
        "kind": "occupancy_snapshot",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "aaa",
            "head_commit": "bbb",
            "telemetry_artifact": "telemetry_matrix.json",
        },
        "rows": [
            {
                "defect_key": "dfk_" + ("c" * 64),
                "psi_post": 0.6,
                "observed_by": 1,
                "missed_by": 0,
                "null_by": 0,
                "k_eff_defect": 1,
                "support_count": 1,
                "evidence_strength": "moderate",
                "file_path": "a.py",
                "category": "consistency",
                "severity": "medium",
                "inputs": {
                    "prior": 0.7,
                    "detection_assumption": 0.7,
                    "coverage_ratio": 1.0,
                    "miss_penalty": 0.0,
                    "uncertainty_guard": 0.0,
                },
            }
        ],
        "summary": {
            "defect_rows": 1,
            "rows_with_positive_observation": 1,
            "rows_with_nulls": 0,
            "mean_psi_post": 0.6,
            "max_psi_post": 0.6,
            "min_psi_post": 0.6,
            "global_k_eff": 1,
        },
        "model": {
            "name": "occupancy_rev1",
            "mode": "deterministic_conservative",
            "prior_policy": "config_locked_v1",
            "null_policy": "null_is_uncertainty",
            "suppression_policy": "usable_misses_only",
            "parameters": {
                "occupancy_prior_base": 0.45,
                "occupancy_support_uplift": 0.2,
                "occupancy_detection_assumption": 0.7,
                "occupancy_miss_penalty_strength": 0.35,
                "occupancy_null_uncertainty_boost": 0.3,
                "occupancy_round_digits": 6,
                "severity_uplift": {
                    "low": 0.0,
                    "medium": 0.05,
                    "high": 0.1,
                    "critical": 0.15,
                },
            },
        },
        "provenance": {
            "algorithm": "occupancy_snapshot_v1",
            "deterministic": True,
            "inputs": ["telemetry_matrix.json"],
            "model_version": "occupancy_rev1",
        },
    },
    "capture_estimate": {
        "artifact_version": 1,
        "kind": "capture_estimate",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "aaa",
            "head_commit": "bbb",
            "telemetry_artifact": "telemetry_matrix.json",
            "occupancy_artifact": "occupancy_snapshot.json",
        },
        "inputs": {
            "mode": "deterministic_conservative",
            "occupancy_inclusion_policy": "include_all",
            "chao1_variant": "bias_corrected",
            "ice_rare_threshold": 10,
            "selection_policy": "max_hidden",
            "sparse_guard_policy": "enabled",
            "round_digits": 6,
        },
        "counts": {
            "defect_rows": 3,
            "included_rows": 3,
            "excluded_rows": 0,
            "k_eff_global": 2,
            "f1": 2,
            "f2": 1,
            "incidence_histogram": {"1": 2, "2": 1},
            "ice": {
                "rare_threshold": 10,
                "rare_count": 3,
                "frequent_count": 0,
                "q1": 2,
                "q2": 1,
                "sample_coverage": 0.5,
            },
        },
        "estimators": {
            "chao1": {
                "observed": 3,
                "hidden": 0.5,
                "total": 3.5,
                "formula_variant": "bias_corrected",
                "guard_applied": False,
                "inputs": {"f1": 2, "f2": 1},
            },
            "ice": {
                "observed": 3,
                "hidden": 1.0,
                "total": 4.0,
                "rare_threshold": 10,
                "sample_coverage": 0.5,
                "formula_variant": "ice",
                "guard_applied": False,
                "inputs": {
                    "rare_count": 3,
                    "frequent_count": 0,
                    "q1": 2,
                    "q2": 1,
                    "gamma_sq": 0.0,
                },
            },
            "selected_method": "max_hidden",
            "selected_source": "ice",
            "selected_hidden": 1.0,
            "selected_total": 4.0,
        },
        "summary": {
            "observed_defects": 3,
            "selected_hidden": 1.0,
            "selected_total": 4.0,
            "selected_method": "max_hidden",
            "sparse_data": True,
            "low_doubleton_support": False,
            "ice_low_coverage": False,
            "estimator_guard_applied": False,
            "global_k_eff": 2,
            "mean_psi_post": 0.73,
        },
        "provenance": {
            "algorithm": "capture_estimate_v1",
            "deterministic": True,
            "inputs": ["telemetry_matrix.json", "occupancy_snapshot.json"],
            "inclusion_policy": "include_all",
            "selection_policy": "max_hidden",
        },
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
        "artifact_version": 1,
        "kind": "hazard_map",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "aaa",
            "head_commit": "bbb",
            "risk_artifact": "risk_heatmap.json",
            "telemetry_artifact": "telemetry_matrix.json",
            "occupancy_artifact": "occupancy_snapshot.json",
            "capture_artifact": "capture_estimate.json",
        },
        "inputs": {
            "mode": "deterministic_conservative",
            "risk_artifact": "risk_heatmap.json",
            "telemetry_artifact": "telemetry_matrix.json",
            "occupancy_artifact": "occupancy_snapshot.json",
            "capture_artifact": "capture_estimate.json",
            "hidden_selection_policy": "max_hidden",
            "round_digits": 6,
        },
        "summary": {
            "hazard_score": 0.72,
            "hazard_tier": "high",
            "defect_count": 2,
            "observed_defects": 2,
            "selected_hidden": 0.5,
            "selected_total": 2.5,
            "mean_psi_post": 0.7,
            "max_risk_score": 0.9,
            "max_hazard_contribution": 0.61,
            "hidden_pressure": 0.2,
            "base_hazard_score": 0.64,
            "hidden_uplift": 0.04,
            "uncertainty_uplift": 0.08,
            "blocking_signals_present": True,
            "blocking_reason_flags": ["hazard_score_threshold"],
            "uncertainty_flags": ["low_global_k_eff"],
        },
        "rows": [
            {
                "defect_key": "dfk_" + ("d" * 64),
                "file_path": "a.py",
                "category": "correctness",
                "severity": "high",
                "reported_by": ["r1", "r2"],
                "support_count": 2,
                "observed_by": 2,
                "missed_by": 0,
                "null_by": 1,
                "k_eff_defect": 2,
                "psi_post": 0.81,
                "local_risk_score": 0.9,
                "severity_weight": 0.35,
                "occupancy_uplift": 0.099225,
                "structural_risk_uplift": 0.0945,
                "support_uplift": 0.0525,
                "hazard_contribution": 0.596225,
                "hazard_flags": ["high_severity", "high_structural_risk", "high_residual_occupancy", "null_uncertainty", "cross_reviewer_support"],
            }
        ],
        "model": {
            "name": "hazard_rev1",
            "mode": "deterministic_conservative",
            "row_policy": "severity_plus_uplifts_v1",
            "summary_policy": "bounded_union_hidden_uncertainty_v1",
            "parameters": {
                "hazard_round_digits": 6,
                "hazard_hidden_uplift_strength": 0.2,
                "hazard_structural_risk_strength": 0.3,
                "hazard_occupancy_strength": 0.35,
                "hazard_support_uplift_strength": 0.15,
                "hazard_uncertainty_boost": 0.12,
                "hazard_blocking_threshold": 0.8,
                "severity_weights": {
                    "low": 0.08,
                    "medium": 0.18,
                    "high": 0.35,
                    "critical": 0.55,
                },
            },
            "thresholds": {
                "tier_floors": {
                    "low": 0.0,
                    "guarded": 0.2,
                    "elevated": 0.4,
                    "high": 0.6,
                    "critical": 0.8,
                }
            },
        },
        "provenance": {
            "algorithm": "hazard_map_v1",
            "deterministic": True,
            "inputs": [
                "risk_heatmap.json",
                "telemetry_matrix.json",
                "occupancy_snapshot.json",
                "capture_estimate.json",
            ],
            "model_version": "hazard_rev1",
        },
    },
    "merge_decision": {
        "artifact_version": 1,
        "kind": "merge_decision",
        "run": {
            "run_id": "run",
            "repo_path": "/tmp/repo",
            "base_ref": "base",
            "head_ref": "head",
            "base_commit": "basec",
            "head_commit": "headc",
            "hazard_artifact": "hazard_map.json",
        },
        "inputs": {
            "mode": "deterministic_advisory",
            "hazard_artifact": "hazard_map.json",
        },
        "decision": {
            "result": "caution",
            "advisory": True,
            "blocking_conditions_present": False,
            "caution_conditions_present": True,
        },
        "summary": {
            "decision_label": "CAUTION",
            "hazard_score": 0.55,
            "dominant_hazard_tier": "elevated",
            "blocking_signals_present": False,
            "blocking_reason_count": 0,
            "caution_reason_count": 2,
            "reason_code_count": 2,
            "uncertainty_flag_count": 1,
        },
        "reason_codes": ["HAZARD_TIER_ELEVATED", "HAZARD_UNCERTAINTY_PRESENT"],
        "model": {
            "name": "merge_rev1",
            "mode": "deterministic_advisory",
            "decision_policy": "hazard_gate_v1",
            "parameters": {
                "merge_decision_caution_threshold": 0.2,
                "merge_decision_block_threshold": 0.6,
                "merge_decision_block_on_hazard_blocking_signals": True,
            },
        },
        "provenance": {
            "algorithm": "merge_decision_v1",
            "deterministic": True,
            "inputs": ["hazard_map.json"],
            "model_version": "merge_rev1",
        },
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
    if kind in {"review_findings", "telemetry_matrix", "occupancy_snapshot", "capture_estimate", "hazard_map", "merge_decision"}:
        broken["run"].pop("run_id", None)
    else:
        broken.pop("run_id", None)
    with pytest.raises(ValidationError):
        validate_instance(broken, schemas[kind], artifact_kind=kind)
