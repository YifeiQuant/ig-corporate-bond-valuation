from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_evaluation_table(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ("evaluation_date", "maturity_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def build_summary_metrics(evaluation_table: pd.DataFrame) -> pd.DataFrame:
    summary = {
        "evaluation_date": evaluation_table["evaluation_date"].dt.strftime("%Y-%m-%d").iloc[0],
        "bond_count": int(len(evaluation_table)),
        "review_count": int(evaluation_table["review_flag"].isin(["Review", "High Review"]).sum()),
        "high_review_count": int((evaluation_table["review_flag"] == "High Review").sum()),
        "avg_abs_spread_residual_bps": float(evaluation_table["spread_residual_bps"].abs().mean()),
        "avg_abs_price_residual": float(evaluation_table["price_residual"].abs().mean()),
        "max_abs_spread_residual_bps": float(evaluation_table["spread_residual_bps"].abs().max()),
        "max_abs_price_residual": float(evaluation_table["price_residual"].abs().max()),
    }
    return pd.DataFrame([summary])


def build_flagged_summary(evaluation_table: pd.DataFrame) -> pd.DataFrame:
    flagged = evaluation_table.loc[
        evaluation_table["review_flag"].isin(["Review", "High Review"])
    ].copy()
    flagged = flagged.sort_values(
        ["review_flag", "spread_residual_bps"],
        ascending=[False, False],
    )
    return flagged[
        [
            "bond_id",
            "issuer",
            "dirty_price",
            "fair_model_dirty_price",
            "price_residual",
            "spread_to_curve",
            "fair_spread",
            "spread_residual_bps",
            "comp_count",
            "review_flag",
            "review_reason",
        ]
    ]


def create_review_pack_markdown(
    summary: pd.DataFrame,
    flagged: pd.DataFrame,
    chart_dir: str | Path,
) -> str:
    row = summary.iloc[0]
    lines = [
        "# Review Pack",
        "",
        f"Evaluation date: {row['evaluation_date']}",
        f"Universe size: {int(row['bond_count'])} bonds",
        f"Review population: {int(row['review_count'])} bonds",
        f"High review population: {int(row['high_review_count'])} bonds",
        f"Average absolute spread residual: {row['avg_abs_spread_residual_bps']:.2f} bps",
        f"Average absolute price residual: {row['avg_abs_price_residual']:.4f}",
        "",
        "## Key observations",
        "",
        "- This run uses a small public bond sample, so a few names drive most of the review counts.",
        "- Observed prices come from holdings data and vendor marks rather than recent trade prints.",
        "- The comp model is rule-based, so it is easy to trace why a bond ended up with a given peer set.",
        "- Large residuals here say more about sample size and comp coverage than about tradable signals on their own.",
        "",
        "## Flagged bonds",
        "",
        "| Bond | Flag | Spread Residual (bps) | Price Residual | Comp Count | Reason |",
        "|------|------|----------------------:|---------------:|-----------:|--------|",
    ]

    for row in flagged.itertuples(index=False):
        lines.append(
            f"| {row.bond_id} | {row.review_flag} | {row.spread_residual_bps:.2f} | "
            f"{row.price_residual:.4f} | {int(row.comp_count)} | {row.review_reason} |"
        )

    chart_dir = Path(chart_dir)
    lines.extend(
        [
            "",
            "## Charts",
            "",
            f"- Spread residual chart: `{chart_dir / 'spread_residuals.png'}`",
            f"- Price residual chart: `{chart_dir / 'price_residuals.png'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def generate_charts(evaluation_table: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    color_map = {"Normal": "#4C956C", "Review": "#F4A259", "High Review": "#BC4B51"}
    colors = [color_map.get(flag, "#577590") for flag in evaluation_table["review_flag"]]

    spread_chart = output_dir / "spread_residuals.png"
    plt.figure(figsize=(10, 5))
    plt.bar(evaluation_table["bond_id"], evaluation_table["spread_residual_bps"], color=colors)
    plt.axhline(10, color="#6C757D", linestyle="--", linewidth=1)
    plt.axhline(-10, color="#6C757D", linestyle="--", linewidth=1)
    plt.ylabel("Spread Residual (bps)")
    plt.title("Observed vs Fair Spread Residuals")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(spread_chart, dpi=150)
    plt.close()

    price_chart = output_dir / "price_residuals.png"
    plt.figure(figsize=(10, 5))
    plt.bar(evaluation_table["bond_id"], evaluation_table["price_residual"], color=colors)
    plt.axhline(0.5, color="#6C757D", linestyle="--", linewidth=1)
    plt.axhline(-0.5, color="#6C757D", linestyle="--", linewidth=1)
    plt.ylabel("Price Residual")
    plt.title("Observed vs Fair Model Price Residuals")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(price_chart, dpi=150)
    plt.close()

    return [spread_chart, price_chart]
