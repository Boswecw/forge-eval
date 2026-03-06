from __future__ import annotations

import hashlib
import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_title(value: str) -> str:
    lowered = value.strip().lower()
    return _WHITESPACE_RE.sub(" ", lowered)


def line_anchor(*, line_start: int | None, line_end: int | None, slice_id: str) -> str:
    if line_start is not None and line_end is not None:
        return f"{line_start}:{line_end}"
    return f"slice:{slice_id}"


def defect_key_for_finding(
    *,
    reviewer_id: str,
    file_path: str,
    category: str,
    title: str,
    line_start: int | None,
    line_end: int | None,
    slice_id: str,
) -> str:
    _ = reviewer_id
    anchor = line_anchor(line_start=line_start, line_end=line_end, slice_id=slice_id)
    title_norm = normalize_title(title)
    payload = "\0".join([file_path, category, title_norm, anchor]).encode("utf-8")
    return f"dfk_{hashlib.sha256(payload).hexdigest()}"
