from __future__ import annotations

from typing import Any

from forge_eval.errors import StageError

_ALLOWED_KEFF_MODES = {"global_min_per_defect"}


def k_eff_for_row(observations: dict[str, int | None]) -> int:
    return sum(1 for value in observations.values() if value is not None)


def compute_global_k_eff(*, rows: list[dict[str, Any]], mode: str) -> int:
    if mode not in _ALLOWED_KEFF_MODES:
        raise StageError(
            "unsupported telemetry k_eff mode",
            stage="telemetry_matrix",
            details={"mode": mode},
        )

    if not rows:
        return 0

    values: list[int] = []
    for row in rows:
        value = row.get("k_eff_defect")
        if isinstance(value, bool) or not isinstance(value, int):
            raise StageError(
                "matrix row missing valid k_eff_defect",
                stage="telemetry_matrix",
                details={"row": row},
            )
        values.append(value)
    return min(values)
