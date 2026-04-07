from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.review_pack import (
    build_flagged_summary,
    build_summary_metrics,
    create_review_pack_markdown,
    generate_charts,
    load_evaluation_table,
)


def main() -> None:
    evaluation_table = load_evaluation_table("outputs/daily_eval_table.csv")
    summary = build_summary_metrics(evaluation_table)
    flagged = build_flagged_summary(evaluation_table)

    chart_dir = Path("outputs") / "charts"
    generate_charts(evaluation_table, chart_dir)

    summary_path = Path("outputs") / "review_summary.csv"
    flagged_path = Path("outputs") / "review_pack_flagged.csv"
    markdown_path = Path("outputs") / "review_pack.md"

    summary.to_csv(summary_path, index=False)
    flagged.to_csv(flagged_path, index=False)
    markdown_path.write_text(
        create_review_pack_markdown(summary, flagged, chart_dir),
        encoding="utf-8",
    )

    print("Review pack generated")
    print(summary.to_string(index=False))
    print(f"\nSaved review summary to {summary_path}")
    print(f"Saved flagged review table to {flagged_path}")
    print(f"Saved markdown review pack to {markdown_path}")
    print(f"Saved charts to {chart_dir}")


if __name__ == "__main__":
    main()
