from __future__ import annotations

import math

import pandas as pd


def _years_between(start: pd.Timestamp, end: pd.Timestamp) -> float:
    return abs((pd.Timestamp(end) - pd.Timestamp(start)).days) / 365.25


def score_comparable(target: pd.Series, candidate: pd.Series) -> dict[str, object]:
    if target["bond_id"] == candidate["bond_id"]:
        raise ValueError("Target and candidate bonds must be different.")

    issuer_match = int(target["issuer"] == candidate["issuer"])
    rating_match = int(target["rating"] == candidate["rating"])
    seniority_match = int(target["seniority"] == candidate["seniority"])
    sector_match = int(target["sector"] == candidate["sector"])
    currency_match = int(target["currency"] == candidate["currency"])

    maturity_gap_years = _years_between(target["maturity_date"], candidate["maturity_date"])
    coupon_gap = abs(float(target["coupon_rate"]) - float(candidate["coupon_rate"])) * 100.0
    spread_gap_bps = (
        abs(float(target["spread_to_curve"]) - float(candidate["spread_to_curve"])) * 10000.0
    )

    score = 0.0
    score += 4.0 * issuer_match
    score += 2.0 * rating_match
    score += 1.5 * seniority_match
    score += 1.0 * sector_match
    score += 1.0 * currency_match
    score -= 0.8 * maturity_gap_years
    score -= 0.5 * coupon_gap
    score -= 0.03 * spread_gap_bps

    weight = max(score, 0.1)
    return {
        "target_bond_id": target["bond_id"],
        "comp_bond_id": candidate["bond_id"],
        "target_issuer": target["issuer"],
        "comp_issuer": candidate["issuer"],
        "issuer_match": issuer_match,
        "rating_match": rating_match,
        "seniority_match": seniority_match,
        "sector_match": sector_match,
        "currency_match": currency_match,
        "maturity_gap_years": maturity_gap_years,
        "coupon_gap_pct": coupon_gap,
        "spread_gap_bps": spread_gap_bps,
        "comp_score": score,
        "comp_weight": weight,
    }


def build_comp_matrix(bonds: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, target in bonds.iterrows():
        for _, candidate in bonds.iterrows():
            if target["bond_id"] == candidate["bond_id"]:
                continue
            rows.append(score_comparable(target, candidate))
    return pd.DataFrame(rows)


def select_top_comps(
    bonds: pd.DataFrame,
    max_comps: int = 3,
    min_score: float = -math.inf,
) -> pd.DataFrame:
    comp_matrix = build_comp_matrix(bonds)
    comp_matrix = comp_matrix.loc[comp_matrix["comp_score"] >= min_score].copy()
    comp_matrix = comp_matrix.sort_values(
        ["target_bond_id", "comp_score", "comp_weight"],
        ascending=[True, False, False],
    )
    return comp_matrix.groupby("target_bond_id", as_index=False).head(max_comps).reset_index(drop=True)


def infer_fair_spreads(
    bonds: pd.DataFrame,
    top_comps: pd.DataFrame,
) -> pd.DataFrame:
    merged = top_comps.merge(
        bonds[
            [
                "bond_id",
                "issuer",
                "rating",
                "spread_to_curve",
                "modified_duration",
                "coupon_rate",
                "maturity_date",
            ]
        ].rename(
            columns={
                "bond_id": "comp_bond_id",
                "issuer": "comp_issuer_from_bonds",
                "rating": "comp_rating",
                "spread_to_curve": "comp_spread_to_curve",
                "modified_duration": "comp_modified_duration",
                "coupon_rate": "comp_coupon_rate",
                "maturity_date": "comp_maturity_date",
            }
        ),
        on="comp_bond_id",
        how="left",
    )

    rows: list[dict[str, object]] = []
    for target_bond_id, group in merged.groupby("target_bond_id", sort=True):
        total_weight = group["comp_weight"].sum()
        fair_spread = (group["comp_spread_to_curve"] * group["comp_weight"]).sum() / total_weight
        rows.append(
            {
                "bond_id": target_bond_id,
                "fair_spread": fair_spread,
                "comp_count": int(len(group)),
                "comp_support_score": float(group["comp_score"].mean()),
                "comp_ids": ", ".join(group["comp_bond_id"].tolist()),
            }
        )

    return pd.DataFrame(rows)
