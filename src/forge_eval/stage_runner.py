from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from forge_eval.errors import StageError, ValidationError
from forge_eval.services.git_diff import resolve_commit
from forge_eval.stages.context_slices import run_stage as run_context_slices_stage
from forge_eval.stages.risk_heatmap import run_stage as run_risk_heatmap_stage
from forge_eval.validation.schema_loader import SCHEMA_BY_ARTIFACT, load_all_schemas
from forge_eval.validation.validate_artifact import load_json_file, validate_instance

STAGE_ORDER = ("risk_heatmap", "context_slices")
STAGE_TO_ARTIFACT_KIND = {
    "risk_heatmap": "risk_heatmap",
    "context_slices": "context_slices",
}


def stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def write_json_file(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(obj), encoding="utf-8")


def _compute_run_id(repo_path: Path, base_commit: str, head_commit: str) -> str:
    payload = f"{repo_path.resolve()}::{base_commit}::{head_commit}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _run_stage(
    *,
    stage: str,
    repo_path: Path,
    base_ref: str,
    head_ref: str,
    run_id: str,
    config: dict[str, Any],
    prior_artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if stage == "risk_heatmap":
        return run_risk_heatmap_stage(
            repo_path=repo_path,
            base_ref=base_ref,
            head_ref=head_ref,
            run_id=run_id,
            config=config,
        )

    if stage == "context_slices":
        subset = None
        risk_artifact = prior_artifacts.get("risk_heatmap")
        if risk_artifact is not None:
            subset = [str(target["file_path"]) for target in risk_artifact.get("targets", [])]
        return run_context_slices_stage(
            repo_path=repo_path,
            base_ref=base_ref,
            head_ref=head_ref,
            run_id=run_id,
            config=config,
            target_file_subset=subset,
        )

    raise StageError("unknown stage requested", stage=stage, details={"stage": stage})


def run_pipeline(
    *,
    repo_path: str | Path,
    base_ref: str,
    head_ref: str,
    out_dir: str | Path,
    config: dict[str, Any],
    schema_dir: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(repo_path)
    out = Path(out_dir)

    if not repo.exists():
        raise StageError(
            "repository path does not exist",
            stage="run",
            details={"repo_path": str(repo)},
        )

    base_commit = resolve_commit(repo, base_ref)
    head_commit = resolve_commit(repo, head_ref)
    run_id = _compute_run_id(repo, base_commit, head_commit)

    schemas = load_all_schemas(schema_dir)

    enabled_stages = list(config["enabled_stages"])

    resolved_config_artifact = {
        "schema_version": "v1",
        "kind": "config_resolved",
        "run_id": run_id,
        "repo_path": str(repo.resolve()),
        "base_ref": base_ref,
        "head_ref": head_ref,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "enabled_stages": enabled_stages,
        "config": config,
    }
    write_json_file(out / "config.resolved.json", resolved_config_artifact)

    artifact_results: dict[str, dict[str, Any]] = {}

    for stage in STAGE_ORDER:
        if stage not in enabled_stages:
            continue

        artifact = _run_stage(
            stage=stage,
            repo_path=repo,
            base_ref=base_ref,
            head_ref=head_ref,
            run_id=run_id,
            config=config,
            prior_artifacts=artifact_results,
        )

        expected_kind = STAGE_TO_ARTIFACT_KIND[stage]
        if artifact.get("kind") != expected_kind:
            raise StageError(
                "stage produced unexpected artifact kind",
                stage=stage,
                details={
                    "expected_kind": expected_kind,
                    "actual_kind": artifact.get("kind"),
                },
            )

        validate_instance(artifact, schemas[expected_kind], artifact_kind=expected_kind)

        artifact_results[expected_kind] = artifact
        write_json_file(out / f"{expected_kind}.json", artifact)

    return {
        "run_id": run_id,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "artifacts_written": [
            "config.resolved.json",
            *[f"{kind}.json" for kind in artifact_results.keys()],
        ],
    }


def _expected_artifacts_from_resolved_config(config_artifact: dict[str, Any]) -> list[str]:
    enabled = config_artifact.get("enabled_stages")
    if not isinstance(enabled, list) or not all(isinstance(item, str) for item in enabled):
        raise ValidationError(
            "config.resolved.json has invalid enabled_stages",
            details={"enabled_stages": enabled},
        )

    invalid = sorted(set(enabled) - set(STAGE_ORDER))
    if invalid:
        raise ValidationError(
            "config.resolved.json includes unknown stage",
            details={"stages": invalid},
        )

    return [STAGE_TO_ARTIFACT_KIND[stage] for stage in STAGE_ORDER if stage in set(enabled)]


def validate_artifacts_directory(
    *,
    artifacts_dir: str | Path,
    schema_dir: str | Path | None = None,
) -> dict[str, Any]:
    out = Path(artifacts_dir)
    if not out.exists():
        raise ValidationError("artifacts directory does not exist", details={"path": str(out)})

    schemas = load_all_schemas(schema_dir)

    resolved_config_path = out / "config.resolved.json"
    if resolved_config_path.exists():
        resolved_config = load_json_file(resolved_config_path)
        expected_kinds = _expected_artifacts_from_resolved_config(resolved_config)
    else:
        # Strict default expectation for implemented stages.
        expected_kinds = [STAGE_TO_ARTIFACT_KIND[stage] for stage in STAGE_ORDER]

    validated_files: list[str] = []

    for kind in expected_kinds:
        artifact_file = out / f"{kind}.json"
        if not artifact_file.exists():
            raise ValidationError(
                "required artifact is missing",
                details={"artifact_kind": kind, "path": str(artifact_file)},
            )

    for kind in sorted(SCHEMA_BY_ARTIFACT.keys()):
        artifact_file = out / f"{kind}.json"
        if not artifact_file.exists():
            continue
        obj = load_json_file(artifact_file)
        validate_instance(obj, schemas[kind], artifact_kind=kind)
        validated_files.append(artifact_file.name)

    return {
        "artifacts_dir": str(out.resolve()),
        "validated_files": validated_files,
        "expected_artifacts": [f"{kind}.json" for kind in expected_kinds],
    }
