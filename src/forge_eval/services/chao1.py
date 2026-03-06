from __future__ import annotations

from typing import Any

from forge_eval.errors import StageError


def estimate_chao1(
    *,
    observed: int,
    f1: int,
    f2: int,
    round_digits: int,
) -> dict[str, Any]:
    _validate_counts(observed=observed, f1=f1, f2=f2)
    _validate_round_digits(round_digits)

    guard_applied = f2 == 0
    hidden = (f1 * max(f1 - 1, 0)) / (2.0 * (f2 + 1))
    total = observed + hidden
    _validate_number(hidden=hidden, total=total)

    return {
        "observed": observed,
        "hidden": _round_float(hidden, round_digits),
        "total": _round_float(total, round_digits),
        "formula_variant": "bias_corrected",
        "guard_applied": guard_applied,
        "inputs": {
            "f1": f1,
            "f2": f2,
        },
    }


def _validate_counts(*, observed: int, f1: int, f2: int) -> None:
    for key, value in (("observed", observed), ("f1", f1), ("f2", f2)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise StageError(
                "Chao1 inputs must be non-negative integers",
                stage="capture_estimate",
                details={"field": key, "value": value},
            )


def _validate_round_digits(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 12:
        raise StageError(
            "round_digits must be an integer in [0, 12]",
            stage="capture_estimate",
            details={"round_digits": value},
        )


def _validate_number(*, hidden: float, total: float) -> None:
    for key, value in (("hidden", hidden), ("total", total)):
        if value < 0.0 or value != value or value == float("inf"):
            raise StageError(
                "Chao1 produced invalid numeric output",
                stage="capture_estimate",
                details={"field": key, "value": value},
            )


def _round_float(value: float, digits: int) -> float:
    return float(round(float(value), digits))
