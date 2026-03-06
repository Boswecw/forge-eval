from __future__ import annotations

from forge_eval.services.risk_analysis import build_risk_targets


def test_risk_target_scoring_and_sorting() -> None:
    targets = build_risk_targets(
        changed_paths=["b.py", "a.py"],
        churn_by_path={"a.py": (10, 0), "b.py": (2, 1)},
        centrality_scores={"a.py": 0.8, "b.py": 0.1},
        risk_weights={"w_churn": 0.5, "w_centrality": 0.3, "w_change_magnitude": 0.2},
        path_weights={},
    )

    assert [item["file_path"] for item in targets] == ["a.py", "b.py"]
    assert targets[0]["risk_score"] >= targets[1]["risk_score"]


def test_path_weight_influences_raw_score() -> None:
    targets = build_risk_targets(
        changed_paths=["src/core/a.py", "src/leaf/b.py"],
        churn_by_path={"src/core/a.py": (1, 0), "src/leaf/b.py": (1, 0)},
        centrality_scores={"src/core/a.py": 0.5, "src/leaf/b.py": 0.5},
        risk_weights={"w_churn": 0.4, "w_centrality": 0.4, "w_change_magnitude": 0.2},
        path_weights={"src/core/": 2.0},
    )

    core = next(t for t in targets if t["file_path"] == "src/core/a.py")
    leaf = next(t for t in targets if t["file_path"] == "src/leaf/b.py")
    assert core["risk_raw"] > leaf["risk_raw"]
