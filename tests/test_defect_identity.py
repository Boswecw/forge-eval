from __future__ import annotations

from forge_eval.services.defect_identity import defect_key_for_finding


def test_defect_key_is_stable() -> None:
    one = defect_key_for_finding(
        reviewer_id="changed_lines.rule.v1",
        file_path="a.py",
        category="consistency",
        title="Schema Change  Lacks Validator",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    two = defect_key_for_finding(
        reviewer_id="changed_lines.rule.v1",
        file_path="a.py",
        category="consistency",
        title="Schema Change  Lacks Validator",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    assert one == two
    assert one.startswith("dfk_")
    assert len(one) == 68


def test_defect_key_normalizes_title_whitespace() -> None:
    one = defect_key_for_finding(
        reviewer_id="changed_lines.rule.v1",
        file_path="a.py",
        category="consistency",
        title="Schema   Change Lacks Validator",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    two = defect_key_for_finding(
        reviewer_id="changed_lines.rule.v1",
        file_path="a.py",
        category="consistency",
        title="  schema change lacks validator ",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    assert one == two


def test_defect_key_coalesces_across_reviewers() -> None:
    one = defect_key_for_finding(
        reviewer_id="changed_lines.rule.v1",
        file_path="a.py",
        category="consistency",
        title="Schema Change Lacks Validator",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    two = defect_key_for_finding(
        reviewer_id="changed_lines.peer.v1",
        file_path="a.py",
        category="consistency",
        title="Schema Change Lacks Validator",
        line_start=10,
        line_end=12,
        slice_id="a.py:1:20",
    )
    assert one == two
