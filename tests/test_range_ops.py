from __future__ import annotations

from forge_eval.services.range_ops import clamp_range, merge_ranges, split_range


def test_merge_overlapping_ranges() -> None:
    merged = merge_ranges([(10, 20), (15, 30)], merge_gap_lines=0)
    assert merged == [(10, 30)]


def test_merge_adjacent_ranges() -> None:
    merged = merge_ranges([(1, 5), (6, 9)], merge_gap_lines=0)
    assert merged == [(1, 9)]


def test_preserve_disjoint_ranges() -> None:
    merged = merge_ranges([(1, 2), (10, 12)], merge_gap_lines=0)
    assert merged == [(1, 2), (10, 12)]


def test_split_oversized_range_deterministically() -> None:
    out = split_range((1, 10), max_lines=4)
    assert out == [(1, 4), (5, 8), (9, 10)]


def test_clamp_to_bounds() -> None:
    out = clamp_range((3, 50), min_line=1, max_line=20)
    assert out == (3, 20)
