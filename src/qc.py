from __future__ import annotations

import pandas as pd


def assign_review_flag(row: pd.Series) -> str:
    spread_residual_bps = abs(float(row["spread_residual_bps"]))
    price_residual_cents = abs(float(row["price_residual"]) * 100.0)
    comp_count = int(row["comp_count"])
    comp_support_score = float(row["comp_support_score"])

    if spread_residual_bps >= 20 or price_residual_cents >= 100 or comp_count < 2:
        return "High Review"
    if spread_residual_bps >= 10 or price_residual_cents >= 50 or comp_support_score < 1.5:
        return "Review"
    return "Normal"


def flag_bonds(evaluation_table: pd.DataFrame) -> pd.DataFrame:
    flagged = evaluation_table.copy()
    flagged["review_flag"] = flagged.apply(assign_review_flag, axis=1)
    flagged["review_reason"] = flagged.apply(_build_reason, axis=1)
    return flagged


def _build_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if abs(float(row["spread_residual_bps"])) >= 20:
        reasons.append("large spread residual")
    elif abs(float(row["spread_residual_bps"])) >= 10:
        reasons.append("moderate spread residual")

    if abs(float(row["price_residual"]) * 100.0) >= 100:
        reasons.append("large price residual")
    elif abs(float(row["price_residual"]) * 100.0) >= 50:
        reasons.append("moderate price residual")

    if int(row["comp_count"]) < 2:
        reasons.append("weak comp count")

    if float(row["comp_support_score"]) < 1.5:
        reasons.append("weak comp support")

    return "; ".join(reasons) if reasons else "within tolerance"
