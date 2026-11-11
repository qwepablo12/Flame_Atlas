"""Rank tests by how close their conditions are to a crew environment.

Score in [0, 1]: 1 = same conditions. Missing values get a neutral penalty,
so well-documented tests rank above vague ones.
"""
from __future__ import annotations

import math

import pandas as pd

# How far apart two values can be before similarity drops a lot
SCALES = {"o2_percent": 10.0, "pressure_kpa": 30.0, "flow_speed_cm_s": 20.0, "gravity_g": 0.5}
WEIGHTS = {"o2_percent": 0.4, "pressure_kpa": 0.25, "flow_speed_cm_s": 0.15, "gravity_g": 0.2}
MISSING = 0.35   # similarity used when the test does not report a value


def _sim(a, b, scale) -> float:
    if a is None or b is None or (isinstance(a, float) and math.isnan(a)) or (isinstance(b, float) and math.isnan(b)):
        return MISSING
    return math.exp(-abs(float(a) - float(b)) / scale)


def score_row(row: pd.Series, target: dict) -> float:
    total = wsum = 0.0
    for col, w in WEIGHTS.items():
        if target.get(col) is None:
            continue
        total += w * _sim(row.get(col), target[col], SCALES[col])
        wsum += w
    s = total / wsum if wsum else 0.0
    if target.get("phase") and row.get("phase") not in (target["phase"], "unknown"):
        s *= 0.5
    return s * (0.7 + 0.3 * float(row.get("confidence") or 0.5))


def rank(df: pd.DataFrame, target: dict, top: int = 10) -> pd.DataFrame:
    out = df.copy()
    out["relevance"] = out.apply(score_row, axis=1, target=target).round(3)
    return out.sort_values("relevance", ascending=False).head(top)


def gravity_bounds(df: pd.DataFrame, target: dict) -> dict:
    """No partial-g data in PSI: report the closest micro-g and 1-g results as bounds."""
    t = {k: v for k, v in target.items() if k != "gravity_g"}
    micro = rank(df[df["gravity_g"].fillna(0) < 0.05], {**t, "gravity_g": 0.0}, top=3)
    earth = rank(df[df["gravity_g"].fillna(0) > 0.9], {**t, "gravity_g": 1.0}, top=3)
    return {"microgravity": micro, "normal_gravity": earth}
