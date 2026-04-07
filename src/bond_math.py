from __future__ import annotations

from typing import Callable

import pandas as pd

from .cashflows import accrued_interest, generate_cashflows


def price_cashflows(
    cashflows: pd.DataFrame,
    discount_fn: Callable[[float], float],
    spread: float = 0.0,
) -> float:
    pv = 0.0
    for row in cashflows.itertuples(index=False):
        spread_df = (1.0 + spread) ** (-row.time_to_cashflow_years)
        pv += row.cashflow * discount_fn(row.time_to_cashflow_years) * spread_df
    return pv


def solve_spread(
    cashflows: pd.DataFrame,
    target_dirty_price: float,
    discount_fn: Callable[[float], float],
    lower_bound: float = -0.02,
    upper_bound: float = 0.20,
    tolerance: float = 1e-8,
    max_iter: int = 200,
) -> float:
    lo = lower_bound
    hi = upper_bound
    pv_lo = price_cashflows(cashflows, discount_fn, spread=lo) - target_dirty_price
    pv_hi = price_cashflows(cashflows, discount_fn, spread=hi) - target_dirty_price

    if pv_lo == 0:
        return lo
    if pv_hi == 0:
        return hi
    if pv_lo * pv_hi > 0:
        raise ValueError("Spread root is not bracketed by the chosen search interval.")

    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        pv_mid = price_cashflows(cashflows, discount_fn, spread=mid) - target_dirty_price
        if abs(pv_mid) < tolerance:
            return mid
        if pv_lo * pv_mid < 0:
            hi = mid
            pv_hi = pv_mid
        else:
            lo = mid
            pv_lo = pv_mid

    return 0.5 * (lo + hi)


def price_from_ytm(
    cashflows: pd.DataFrame,
    ytm: float,
    coupon_frequency: int = 2,
) -> float:
    pv = 0.0
    for row in cashflows.itertuples(index=False):
        discount = (1.0 + ytm / coupon_frequency) ** (
            -coupon_frequency * row.time_to_cashflow_years
        )
        pv += row.cashflow * discount
    return pv


def solve_ytm(
    cashflows: pd.DataFrame,
    target_dirty_price: float,
    coupon_frequency: int = 2,
    lower_bound: float = -0.02,
    upper_bound: float = 0.25,
    tolerance: float = 1e-8,
    max_iter: int = 200,
) -> float:
    lo = lower_bound
    hi = upper_bound
    pv_lo = price_from_ytm(cashflows, lo, coupon_frequency) - target_dirty_price
    pv_hi = price_from_ytm(cashflows, hi, coupon_frequency) - target_dirty_price

    if pv_lo == 0:
        return lo
    if pv_hi == 0:
        return hi
    if pv_lo * pv_hi > 0:
        raise ValueError("Yield root is not bracketed by the chosen search interval.")

    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        pv_mid = price_from_ytm(cashflows, mid, coupon_frequency) - target_dirty_price
        if abs(pv_mid) < tolerance:
            return mid
        if pv_lo * pv_mid < 0:
            hi = mid
            pv_hi = pv_mid
        else:
            lo = mid
            pv_lo = pv_mid

    return 0.5 * (lo + hi)


def modified_duration(
    cashflows: pd.DataFrame,
    ytm: float,
    coupon_frequency: int = 2,
    bump_size: float = 1e-4,
) -> float:
    price_up = price_from_ytm(cashflows, ytm + bump_size, coupon_frequency)
    price_down = price_from_ytm(cashflows, ytm - bump_size, coupon_frequency)
    base_price = price_from_ytm(cashflows, ytm, coupon_frequency)
    return (price_down - price_up) / (2.0 * base_price * bump_size)


def convexity(
    cashflows: pd.DataFrame,
    ytm: float,
    coupon_frequency: int = 2,
    bump_size: float = 1e-4,
) -> float:
    price_up = price_from_ytm(cashflows, ytm + bump_size, coupon_frequency)
    price_down = price_from_ytm(cashflows, ytm - bump_size, coupon_frequency)
    base_price = price_from_ytm(cashflows, ytm, coupon_frequency)
    return (price_up + price_down - 2.0 * base_price) / (base_price * bump_size**2)


def evaluate_bond(
    bond_row: pd.Series,
    discount_fn: Callable[[float], float],
) -> dict[str, object]:
    settlement_date = bond_row["evaluation_date"]
    maturity_date = bond_row["maturity_date"]
    coupon_rate = float(bond_row["coupon_rate"])
    coupon_frequency = int(bond_row["coupon_frequency"])
    clean_price = float(bond_row["clean_price"])
    face_value = float(bond_row.get("face_value", 100.0))

    cashflows = generate_cashflows(
        settlement_date=settlement_date,
        maturity_date=maturity_date,
        coupon_rate=coupon_rate,
        coupon_frequency=coupon_frequency,
        face_value=face_value,
    )
    accrued = accrued_interest(
        settlement_date=settlement_date,
        maturity_date=maturity_date,
        coupon_rate=coupon_rate,
        coupon_frequency=coupon_frequency,
        face_value=face_value,
    )
    dirty_price = clean_price + accrued
    spread = solve_spread(cashflows, dirty_price, discount_fn)
    ytm = solve_ytm(cashflows, dirty_price, coupon_frequency=coupon_frequency)
    mod_duration = modified_duration(
        cashflows, ytm=ytm, coupon_frequency=coupon_frequency
    )
    cx = convexity(cashflows, ytm=ytm, coupon_frequency=coupon_frequency)
    model_dirty_price = price_cashflows(cashflows, discount_fn, spread=spread)

    return {
        "bond_id": bond_row["bond_id"],
        "issuer": bond_row["issuer"],
        "evaluation_date": pd.Timestamp(settlement_date).normalize(),
        "maturity_date": pd.Timestamp(maturity_date).normalize(),
        "coupon_rate": coupon_rate,
        "clean_price": clean_price,
        "accrued_interest": accrued,
        "dirty_price": dirty_price,
        "ytm": ytm,
        "spread_to_curve": spread,
        "modified_duration": mod_duration,
        "convexity": cx,
        "model_dirty_price": model_dirty_price,
    }
