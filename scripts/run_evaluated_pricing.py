from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluator import build_evaluation_outputs


def _format_for_display(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    rate_columns = ["coupon_rate", "ytm", "spread_to_curve", "fair_spread"]
    for col in rate_columns:
        if col in display.columns:
            display[col] = display[col].map(lambda x: round(float(x) * 100.0, 4))

    for col in ("spread_residual_bps", "comp_support_score"):
        if col in display.columns:
            display[col] = display[col].map(lambda x: round(float(x), 4))

    for col in (
        "clean_price",
        "accrued_interest",
        "dirty_price",
        "fair_model_dirty_price",
        "price_residual",
        "modified_duration",
        "convexity",
    ):
        if col in display.columns:
            display[col] = display[col].map(lambda x: round(float(x), 6))

    return display


def main() -> None:
    evaluation_table, comp_table = build_evaluation_outputs(
        analytics_path="outputs/bond_analytics.csv",
        bond_universe_path="data/raw/bond_universe.csv",
        treasury_curve_path="data/raw/treasury_curve.csv",
        max_comps=3,
    )

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    evaluation_path = outputs_dir / "daily_eval_table.csv"
    comp_path = outputs_dir / "comp_selection.csv"
    flagged_path = outputs_dir / "flagged_bonds.csv"

    evaluation_table.to_csv(evaluation_path, index=False)
    comp_table.to_csv(comp_path, index=False)
    evaluation_table.loc[
        evaluation_table["review_flag"].isin(["Review", "High Review"])
    ].to_csv(flagged_path, index=False)

    print("Evaluated pricing output")
    print(
        _format_for_display(
            evaluation_table[
                [
                    "bond_id",
                    "issuer",
                    "dirty_price",
                    "spread_to_curve",
                    "fair_spread",
                    "fair_model_dirty_price",
                    "price_residual",
                    "spread_residual_bps",
                    "comp_count",
                    "review_flag",
                ]
            ]
        ).to_string(index=False)
    )
    print(f"\nSaved evaluation table to {evaluation_path}")
    print(f"Saved comp selection to {comp_path}")
    print(f"Saved flagged bonds to {flagged_path}")


if __name__ == "__main__":
    main()
