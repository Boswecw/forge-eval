from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_eval.config import DEFAULT_CONFIG, load_config, normalize_config
from forge_eval.errors import ConfigError


def test_config_normalization_defaults() -> None:
    cfg = normalize_config({})
    assert cfg["enabled_stages"] == ["risk_heatmap", "context_slices"]
    assert cfg["include_file_extensions"] == sorted(DEFAULT_CONFIG["include_file_extensions"])
    assert cfg["exclude_paths"] == sorted(DEFAULT_CONFIG["exclude_paths"])
    assert abs(sum(cfg["risk_weights"].values()) - 1.0) < 1e-9


def test_config_unknown_key_fails() -> None:
    with pytest.raises(ConfigError):
        normalize_config({"unknown_key": 123})


def test_load_config_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "enabled_stages": ["context_slices"],
                "risk_weights": {"w_churn": 3.0, "w_centrality": 1.0, "w_change_magnitude": 0.0},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg["enabled_stages"] == ["context_slices"]
    assert cfg["risk_weights"]["w_churn"] == 0.75


def test_load_config_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "enabled_stages:\n  - risk_heatmap\ninclude_file_extensions:\n  - py\n  - .TS\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg["enabled_stages"] == ["risk_heatmap"]
    assert cfg["include_file_extensions"] == [".py", ".ts"]
