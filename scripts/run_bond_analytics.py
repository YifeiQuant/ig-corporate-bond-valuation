from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bond_math import evaluate_bond
from src.curve import build_zero_curve, make_discount_function


def load_bond_universe(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("evaluation_date", "maturity_date"):
        df[col] = pd.to_datetime(df[col])
    return df


def main() -> None:
    bonds = load_bond_universe("data/raw/bond_universe.csv")
    results = []

    for eval_date, bond_slice in bonds.groupby("evaluation_date", sort=True):
        _, zero_curve = build_zero_curve("data/raw/treasury_curve.csv", eval_date=eval_date)
        discount_fn, _ = make_discount_function(zero_curve)

        for _, bond_row in bond_slice.iterrows():
            results.append(evaluate_bond(bond_row, discount_fn))

    analytics = pd.DataFrame(results).sort_values(["issuer", "maturity_date"])
    output_path = Path("outputs") / "bond_analytics.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    analytics.to_csv(output_path, index=False)

    display = analytics.copy()
    for col in ("coupon_rate", "ytm", "spread_to_curve"):
        display[col] = display[col].map(lambda x: round(float(x) * 100.0, 4))
    for col in (
        "clean_price",
        "accrued_interest",
        "dirty_price",
        "modified_duration",
        "convexity",
        "model_dirty_price",
    ):
        display[col] = display[col].map(lambda x: round(float(x), 6))

    print("Bond analytics output")
    print(display.to_string(index=False))
    print(f"\nSaved analytics to {output_path}")


if __name__ == "__main__":
    main()
