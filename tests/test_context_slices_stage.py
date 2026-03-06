from __future__ import annotations

from pathlib import Path

from forge_eval.stages.context_slices import run_stage


def test_context_slices_stage_wires_extractor(monkeypatch) -> None:
    captured = {}

    def fake_extract_context_slices(**kwargs):
        captured.update(kwargs)
        return {
            "slices": [
                {
                    "slice_id": "a.py:1:2",
                    "file_path": "a.py",
                    "start_line": 1,
                    "end_line": 2,
                    "changed_line_count": 1,
                    "total_line_count": 2,
                    "content": "x\ny",
                    "origin": {
                        "source": "git_diff_head_version",
                        "base_ref": "base",
                        "head_ref": "head",
                        "changed_ranges": [[1, 1]],
                    },
                }
            ],
            "summary": {"target_count": 1, "slice_count": 1, "total_line_count": 2},
        }

    monkeypatch.setattr(
        "forge_eval.stages.context_slices.extract_context_slices",
        fake_extract_context_slices,
    )

    config = {
        "context_radius_lines": 12,
        "merge_gap_lines": 2,
        "max_slices_per_target": 8,
        "max_lines_per_slice": 120,
        "max_total_lines": 1200,
        "fail_on_slice_truncation": True,
        "binary_file_policy": "fail",
    }
    out = run_stage(
        repo_path=Path("/tmp/repo"),
        base_ref="base",
        head_ref="head",
        run_id="run",
        config=config,
        target_file_subset=["a.py"],
    )

    assert out["kind"] == "context_slices"
    assert out["summary"]["slice_count"] == 1
    assert captured["target_file_subset"] == ["a.py"]
