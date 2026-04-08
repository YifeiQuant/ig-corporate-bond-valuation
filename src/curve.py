from pathlib import Path
from typing import Callable, Tuple

import numpy as np
import pandas as pd


def load_treasury_curve(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def tenor_to_years(tenor: str) -> float:
    tenor = tenor.strip().upper()
    if tenor.endswith("M"):
        return float(tenor[:-1]) / 12.0
    if tenor.endswith("Y"):
        return float(tenor[:-1])
    raise ValueError(f"Unsupported tenor format: {tenor}")


def standard_tenor_to_years(par_row: pd.Series) -> pd.DataFrame:
    records = []
    for col, val in par_row.items():
        if col == "date":
            continue
        if pd.isna(val):
            continue
        records.append(
            {
                "tenor": col,
                "maturity_years": tenor_to_years(col),
                "par_yield": float(val) / 100.0,
            }
        )
    out = pd.DataFrame(records).sort_values("maturity_years").reset_index(drop=True)
    return out


def get_treasury_par_curve(
    history: pd.DataFrame, eval_date: str | pd.Timestamp | None = None
) -> tuple[pd.Timestamp, pd.DataFrame]:
    if history.empty:
        raise ValueError("Treasury curve history is empty.")

    if eval_date is None:
        curve_row = history.iloc[-1]
    else:
        target = pd.Timestamp(eval_date).normalize()
        matches = history.loc[history["date"].dt.normalize() == target]
        if matches.empty:
            available_min = history["date"].min().date()
            available_max = history["date"].max().date()
            raise ValueError(
                f"No Treasury curve found for {target.date()}. "
                f"Available dates span {available_min} to {available_max}."
            )
        curve_row = matches.iloc[-1]

    as_of_date = pd.Timestamp(curve_row["date"]).normalize()
    par_curve = standard_tenor_to_years(curve_row)
    return as_of_date, par_curve


def bootstrap_zero_curve(
    par_curve: pd.DataFrame,
    coupon_freq: int = 2
) -> pd.DataFrame:
    """
    Bootstrap discount factors and zero rates from a par curve.

    Assumptions:
    - face value = 100
    - coupon rate at each maturity equals par yield at that maturity
    - coupon frequency is fixed across maturities
    - coupon dates align perfectly with tenor grid where possible

    For very short maturities below one coupon period, use simple discounting:
        DF(T) = 1 / (1 + y * T)

    For coupon-bearing maturities:
        100 = sum(c/f * 100 * DF(t_i)) + (100 + c/f * 100) * DF(T)
    """
    face = 100.0
    rows = []
    known_dfs = {}

    def infer_discount_factor(target_time: float) -> float:
        rounded_target = round(target_time, 10)
        if rounded_target in known_dfs:
            return known_dfs[rounded_target]

        known_times = sorted(known_dfs)
        if not known_times:
            raise ValueError("No earlier discount factors are available for interpolation.")

        # A production curve engine would usually use a richer interpolation or
        # parametric term-structure fit. Here, log-linear interpolation on discount
        # factors keeps the implementation transparent and stable at coupon dates
        # that fall between the standard tenor nodes.
        if rounded_target <= known_times[0]:
            t0 = known_times[0]
            zero0 = known_dfs[t0] ** (-1.0 / t0) - 1.0
            return (1.0 + zero0) ** (-rounded_target)

        for left, right in zip(known_times[:-1], known_times[1:]):
            if left <= rounded_target <= right:
                log_df = np.interp(
                    rounded_target,
                    [left, right],
                    [np.log(known_dfs[left]), np.log(known_dfs[right])],
                )
                return float(np.exp(log_df))

        last_time = known_times[-1]
        last_zero = known_dfs[last_time] ** (-1.0 / last_time) - 1.0
        return (1.0 + last_zero) ** (-rounded_target)

    for _, row in par_curve.iterrows():
        T = float(row["maturity_years"])
        y = float(row["par_yield"])

        # short-end: treat as zero/simple instrument
        if T <= 1.0 / coupon_freq + 1e-12:
            df_T = 1.0 / (1.0 + y * T)
        else:
            coupon = y * face
            cpn = coupon / coupon_freq

            # coupon dates before maturity
            payment_times = np.arange(1, int(round(T * coupon_freq)) + 1) / coupon_freq
            payment_times = payment_times[payment_times < T - 1e-12]

            pv_coupons = 0.0
            for t in payment_times:
                pv_coupons += cpn * infer_discount_factor(t)

            df_T = (face - pv_coupons) / (face + cpn)

        zero_rate = df_T ** (-1.0 / T) - 1.0

        known_dfs[round(T, 10)] = df_T
        rows.append(
            {
                "maturity_years": T,
                "par_yield": y,
                "discount_factor": df_T,
                "zero_rate": zero_rate,
            }
        )

    return pd.DataFrame(rows)


def build_zero_curve(
    path: str | Path,
    eval_date: str | pd.Timestamp | None = None,
    coupon_freq: int = 2,
) -> tuple[pd.Timestamp, pd.DataFrame]:
    history = load_treasury_curve(path)
    as_of_date, par_curve = get_treasury_par_curve(history, eval_date=eval_date)
    zero_curve = bootstrap_zero_curve(par_curve, coupon_freq=coupon_freq)
    zero_curve.insert(0, "date", as_of_date)
    return as_of_date, zero_curve


def make_discount_function(
    zero_curve: pd.DataFrame
) -> Tuple[Callable[[float], float], Callable[[float], float]]:
    """
    Returns:
        df_fn(t): interpolated discount factor
        zero_fn(t): interpolated zero rate
    """
    times = zero_curve["maturity_years"].to_numpy()
    dfs = zero_curve["discount_factor"].to_numpy()
    zeros = zero_curve["zero_rate"].to_numpy()

    def df_fn(t: float) -> float:
        if t <= times[0]:
            return float(np.interp(t, times, dfs))
        return float(np.interp(t, times, dfs))

    def zero_fn(t: float) -> float:
        if t <= times[0]:
            return float(np.interp(t, times, zeros))
        return float(np.interp(t, times, zeros))

    return df_fn, zero_fn


def format_curve_table(curve: pd.DataFrame) -> pd.DataFrame:
    formatted = curve.copy()
    for col in ("par_yield", "zero_rate"):
        if col in formatted.columns:
            formatted[col] = formatted[col].map(lambda x: round(float(x) * 100.0, 4))
    if "discount_factor" in formatted.columns:
        formatted["discount_factor"] = formatted["discount_factor"].map(
            lambda x: round(float(x), 8)
        )
    if "maturity_years" in formatted.columns:
        formatted["maturity_years"] = formatted["maturity_years"].map(
            lambda x: round(float(x), 4)
        )
    return formatted

if __name__ == "__main__":
    print("curve.py executed successfully")
