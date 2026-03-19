from __future__ import annotations

from typing import Any

from forge_eval.errors import StageError


def estimate_chao2(
    *,
    observed: int,
    q1: int,
    q2: int,
    m: int,
    round_digits: int,
) -> dict[str, Any]:
    _validate_round_digits(round_digits)

    if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
        return _unavailable(
            reason="observed count is invalid",
            q1=q1,
            q2=q2,
            m=m,
        )
    if isinstance(q1, bool) or not isinstance(q1, int) or q1 < 0:
        return _unavailable(
            reason="q1 must be a non-negative integer",
            q1=q1,
            q2=q2,
            m=m,
        )
    if isinstance(q2, bool) or not isinstance(q2, int) or q2 < 0:
        return _unavailable(
            reason="q2 must be a non-negative integer",
            q1=q1,
            q2=q2,
            m=m,
        )
    if isinstance(m, bool) or not isinstance(m, int) or m < 0:
        return _unavailable(
            reason="m must be a non-negative integer",
            q1=q1,
            q2=q2,
            m=m,
        )
    if m < 2:
        return _unavailable(
            reason="m < 2: not enough sampling units for Chao2",
            q1=q1,
            q2=q2,
            m=m,
        )

    guard_flags: dict[str, bool] = {
        "q2_zero_fallback": False,
        "q1_zero_no_signal": False,
    }

    if q1 == 0:
        guard_flags["q1_zero_no_signal"] = True
        hidden = 0.0
    elif q2 > 0:
        hidden = ((m - 1) / m) * (q1 * q1 / (2.0 * q2))
    else:
        guard_flags["q2_zero_fallback"] = True
        hidden = ((m - 1) / m) * (q1 * (q1 - 1) / 2.0)

    total = observed + hidden

    if hidden < 0.0 or hidden != hidden or hidden == float("inf"):
        raise StageError(
            "Chao2 produced invalid numeric output",
            stage="capture_estimate",
            details={"hidden": hidden, "total": total},
        )

    return {
        "enabled": True,
        "available": True,
        "hidden_estimate": _round_float(hidden, round_digits),
        "total_estimate": _round_float(total, round_digits),
        "guard_flags": guard_flags,
        "inputs_used": {
            "q1": q1,
            "q2": q2,
            "m": m,
        },
        "reason_unavailable": None,
    }


def _unavailable(
    *,
    reason: str,
    q1: object,
    q2: object,
    m: object,
) -> dict[str, Any]:
    return {
        "enabled": True,
        "available": False,
        "hidden_estimate": None,
        "total_estimate": None,
        "guard_flags": {
            "q2_zero_fallback": False,
            "q1_zero_no_signal": False,
        },
        "inputs_used": {
            "q1": q1,
            "q2": q2,
            "m": m,
        },
        "reason_unavailable": reason,
    }


def _validate_round_digits(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 12:
        raise StageError(
            "Chao2 round_digits must be an integer in [0, 12]",
            stage="capture_estimate",
            details={"round_digits": value},
        )


def _round_float(value: float, digits: int) -> float:
    return float(round(float(value), digits))
