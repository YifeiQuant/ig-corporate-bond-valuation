from __future__ import annotations

from pathlib import Path

import pandas as pd

from .bond_math import price_cashflows
from .cashflows import generate_cashflows
from .comps import infer_fair_spreads, select_top_comps
from .curve import build_zero_curve, make_discount_function
from .qc import flag_bonds


def load_analytics(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("evaluation_date", "maturity_date"):
        df[col] = pd.to_datetime(df[col])
    return df


def load_bond_universe(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("evaluation_date", "maturity_date"):
        df[col] = pd.to_datetime(df[col])
    return df


def build_evaluation_outputs(
    analytics_path: str | Path,
    bond_universe_path: str | Path,
    treasury_curve_path: str | Path,
    max_comps: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    analytics = load_analytics(analytics_path)
    universe = load_bond_universe(bond_universe_path)
    bonds = analytics.merge(
        universe,
        on=["bond_id", "issuer", "evaluation_date", "maturity_date", "coupon_rate", "clean_price"],
        how="left",
        validate="one_to_one",
    )

    evaluation_rows: list[pd.DataFrame] = []
    comp_rows: list[pd.DataFrame] = []

    for eval_date, bond_slice in bonds.groupby("evaluation_date", sort=True):
        top_comps = select_top_comps(bond_slice, max_comps=max_comps)
        fair_spreads = infer_fair_spreads(bond_slice, top_comps)
        _, zero_curve = build_zero_curve(treasury_curve_path, eval_date=eval_date)
        discount_fn, _ = make_discount_function(zero_curve)

        evaluated = bond_slice.merge(fair_spreads, on="bond_id", how="left", validate="one_to_one")
        model_dirty_prices = []
        for _, row in evaluated.iterrows():
            cashflows = generate_cashflows(
                settlement_date=row["evaluation_date"],
                maturity_date=row["maturity_date"],
                coupon_rate=float(row["coupon_rate"]),
                coupon_frequency=int(row["coupon_frequency"]),
                face_value=float(row["face_value"]),
            )
            model_dirty_prices.append(
                price_cashflows(cashflows, discount_fn, spread=float(row["fair_spread"]))
            )

        evaluated = evaluated.copy()
        evaluated["fair_model_dirty_price"] = model_dirty_prices
        evaluated["price_residual"] = evaluated["dirty_price"] - evaluated["fair_model_dirty_price"]
        evaluated["spread_residual_bps"] = (
            (evaluated["spread_to_curve"] - evaluated["fair_spread"]) * 10000.0
        )
        evaluated = flag_bonds(evaluated)

        comp_details = top_comps.merge(
            fair_spreads[["bond_id", "fair_spread"]],
            left_on="target_bond_id",
            right_on="bond_id",
            how="left",
        ).drop(columns=["bond_id"])
        comp_details.insert(0, "evaluation_date", eval_date)

        evaluation_rows.append(evaluated)
        comp_rows.append(comp_details)

    evaluation_table = pd.concat(evaluation_rows, ignore_index=True)
    comp_table = pd.concat(comp_rows, ignore_index=True)
    return evaluation_table, comp_table
