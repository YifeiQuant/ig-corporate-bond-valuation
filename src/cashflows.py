from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CouponWindow:
    previous_coupon: pd.Timestamp
    next_coupon: pd.Timestamp
    accrual_fraction: float


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def generate_coupon_schedule(
    maturity_date: str | pd.Timestamp,
    coupon_frequency: int = 2,
    settlement_date: str | pd.Timestamp | None = None,
) -> list[pd.Timestamp]:
    maturity = _normalize_date(maturity_date)
    step_months = int(round(12 / coupon_frequency))
    dates = [maturity]

    while True:
        next_date = dates[-1] - pd.DateOffset(months=step_months)
        if settlement_date is not None and next_date <= _normalize_date(settlement_date):
            dates.append(next_date)
            break
        dates.append(next_date)
        if len(dates) > 256:
            raise ValueError("Coupon schedule generation exceeded a reasonable limit.")

    return sorted(dates)


def find_coupon_window(
    settlement_date: str | pd.Timestamp,
    maturity_date: str | pd.Timestamp,
    coupon_frequency: int = 2,
) -> CouponWindow:
    settlement = _normalize_date(settlement_date)
    schedule = generate_coupon_schedule(
        maturity_date=maturity_date,
        coupon_frequency=coupon_frequency,
        settlement_date=settlement,
    )

    previous_coupon = None
    next_coupon = None
    for coupon_date in schedule:
        if coupon_date <= settlement:
            previous_coupon = coupon_date
        if coupon_date > settlement:
            next_coupon = coupon_date
            break

    if previous_coupon is None or next_coupon is None:
        raise ValueError("Could not determine coupon window for the requested bond.")

    accrual_days = (settlement - previous_coupon).days
    period_days = (next_coupon - previous_coupon).days
    accrual_fraction = accrual_days / period_days

    return CouponWindow(
        previous_coupon=previous_coupon,
        next_coupon=next_coupon,
        accrual_fraction=accrual_fraction,
    )


def generate_cashflows(
    settlement_date: str | pd.Timestamp,
    maturity_date: str | pd.Timestamp,
    coupon_rate: float,
    coupon_frequency: int = 2,
    face_value: float = 100.0,
) -> pd.DataFrame:
    settlement = _normalize_date(settlement_date)
    maturity = _normalize_date(maturity_date)
    coupon_dates = generate_coupon_schedule(
        maturity_date=maturity,
        coupon_frequency=coupon_frequency,
        settlement_date=settlement,
    )

    coupon_amount = face_value * coupon_rate / coupon_frequency
    rows: list[dict[str, object]] = []
    for coupon_date in coupon_dates:
        if coupon_date <= settlement:
            continue

        amount = coupon_amount
        if coupon_date == maturity:
            amount += face_value

        time_to_cashflow = (coupon_date - settlement).days / 365.25
        rows.append(
            {
                "payment_date": coupon_date,
                "cashflow": amount,
                "time_to_cashflow_years": time_to_cashflow,
            }
        )

    if not rows:
        raise ValueError("No future cashflows remain after the settlement date.")

    return pd.DataFrame(rows)


def accrued_interest(
    settlement_date: str | pd.Timestamp,
    maturity_date: str | pd.Timestamp,
    coupon_rate: float,
    coupon_frequency: int = 2,
    face_value: float = 100.0,
) -> float:
    window = find_coupon_window(
        settlement_date=settlement_date,
        maturity_date=maturity_date,
        coupon_frequency=coupon_frequency,
    )
    coupon_amount = face_value * coupon_rate / coupon_frequency
    return coupon_amount * window.accrual_fraction
