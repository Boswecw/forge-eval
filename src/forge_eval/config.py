from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from forge_eval.errors import ConfigError

KNOWN_STAGES = ("risk_heatmap", "context_slices")

DEFAULT_CONFIG: dict[str, Any] = {
    "enabled_stages": ["risk_heatmap", "context_slices"],
    "risk_weights": {
        "w_churn": 0.45,
        "w_centrality": 0.35,
        "w_change_magnitude": 0.20,
    },
    "path_weights": {},
    "context_radius_lines": 12,
    "merge_gap_lines": 2,
    "max_slices_per_target": 8,
    "max_lines_per_slice": 120,
    "max_total_lines": 1200,
    "fail_on_slice_truncation": True,
    "include_file_extensions": [
        ".py",
        ".rs",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".md",
    ],
    "exclude_paths": ["dist/", "build/", ".venv/", "node_modules/"],
    "binary_file_policy": "fail",
}


def _parse_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError("config file does not exist", details={"path": str(path)})
    raw = path.read_text(encoding="utf-8")

    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigError("invalid JSON config", details={"path": str(path), "error": str(exc)}) from exc
    elif suffix in {".yaml", ".yml"}:
        try:
            obj = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ConfigError("invalid YAML config", details={"path": str(path), "error": str(exc)}) from exc
    else:
        raise ConfigError(
            "unsupported config format; expected .json/.yaml/.yml",
            details={"path": str(path), "suffix": suffix},
        )

    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise ConfigError("config root must be an object", details={"path": str(path)})
    return obj


def _ensure_number(name: str, value: Any, *, min_value: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError("config value must be numeric", details={"key": name, "value": value})
    out = float(value)
    if min_value is not None and out < min_value:
        raise ConfigError(
            "config value below allowed minimum",
            details={"key": name, "value": out, "min": min_value},
        )
    return out


def _normalize_extensions(values: Any) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ConfigError("include_file_extensions must be a list of strings")
    normalized = []
    for ext in values:
        ext = ext.strip()
        if not ext:
            raise ConfigError("empty extension entry is not allowed")
        if not ext.startswith("."):
            ext = f".{ext}"
        normalized.append(ext.lower())
    return sorted(set(normalized))


def _normalize_exclude_paths(values: Any) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ConfigError("exclude_paths must be a list of strings")
    normalized = []
    for path in values:
        p = path.replace("\\", "/").strip()
        if not p:
            raise ConfigError("exclude_paths entries cannot be empty")
        if not p.endswith("/"):
            p = f"{p}/"
        normalized.append(p)
    return sorted(set(normalized))


def _normalize_path_weights(values: Any) -> dict[str, float]:
    if not isinstance(values, dict):
        raise ConfigError("path_weights must be an object")
    out: dict[str, float] = {}
    for key in sorted(values.keys()):
        val = values[key]
        if not isinstance(key, str) or not key:
            raise ConfigError("path_weights keys must be non-empty strings")
        weight = _ensure_number(f"path_weights.{key}", val, min_value=0.0)
        out[key.replace("\\", "/")] = weight
    return out


def _normalize_risk_weights(values: Any) -> dict[str, float]:
    if not isinstance(values, dict):
        raise ConfigError("risk_weights must be an object")

    expected = {"w_churn", "w_centrality", "w_change_magnitude"}
    unknown = set(values.keys()) - expected
    if unknown:
        raise ConfigError("unknown risk_weights keys", details={"keys": sorted(unknown)})

    merged = copy.deepcopy(DEFAULT_CONFIG["risk_weights"])
    for key, value in values.items():
        merged[key] = _ensure_number(f"risk_weights.{key}", value, min_value=0.0)

    total = merged["w_churn"] + merged["w_centrality"] + merged["w_change_magnitude"]
    if total <= 0.0:
        raise ConfigError("risk weight sum must be > 0", details={"risk_weights": merged})

    # Normalize to deterministic unit sum for stable scoring.
    return {k: merged[k] / total for k in sorted(merged.keys())}


def normalize_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    cfg: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
    raw = raw or {}

    unknown = set(raw.keys()) - set(DEFAULT_CONFIG.keys())
    if unknown:
        raise ConfigError("unknown config keys", details={"keys": sorted(unknown)})

    if "enabled_stages" in raw:
        value = raw["enabled_stages"]
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError("enabled_stages must be a list of strings")
        requested = set(value)
        invalid = requested - set(KNOWN_STAGES)
        if invalid:
            raise ConfigError("enabled_stages contains unknown stage", details={"stages": sorted(invalid)})
        cfg["enabled_stages"] = [stage for stage in KNOWN_STAGES if stage in requested]
        if not cfg["enabled_stages"]:
            raise ConfigError("at least one stage must be enabled")

    if "risk_weights" in raw:
        cfg["risk_weights"] = _normalize_risk_weights(raw["risk_weights"])

    if "path_weights" in raw:
        cfg["path_weights"] = _normalize_path_weights(raw["path_weights"])

    int_constraints = {
        "context_radius_lines": 0,
        "merge_gap_lines": 0,
        "max_slices_per_target": 1,
        "max_lines_per_slice": 1,
        "max_total_lines": 1,
    }
    for key, min_value in int_constraints.items():
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError("config value must be integer", details={"key": key, "value": value})
        if value < min_value:
            raise ConfigError(
                "config value below minimum",
                details={"key": key, "value": value, "min": min_value},
            )
        cfg[key] = value

    if "fail_on_slice_truncation" in raw:
        value = raw["fail_on_slice_truncation"]
        if not isinstance(value, bool):
            raise ConfigError("fail_on_slice_truncation must be boolean")
        cfg["fail_on_slice_truncation"] = value

    if "include_file_extensions" in raw:
        cfg["include_file_extensions"] = _normalize_extensions(raw["include_file_extensions"])

    if "exclude_paths" in raw:
        cfg["exclude_paths"] = _normalize_exclude_paths(raw["exclude_paths"])

    if "binary_file_policy" in raw:
        value = raw["binary_file_policy"]
        if value not in {"fail", "ignore"}:
            raise ConfigError("binary_file_policy must be 'fail' or 'ignore'")
        cfg["binary_file_policy"] = value

    cfg["include_file_extensions"] = _normalize_extensions(cfg["include_file_extensions"])
    cfg["exclude_paths"] = _normalize_exclude_paths(cfg["exclude_paths"])

    return cfg


def load_config(config_path: str | Path | None) -> dict[str, Any]:
    if config_path is None:
        return normalize_config({})
    path = Path(config_path)
    parsed = _parse_config_file(path)
    return normalize_config(parsed)
