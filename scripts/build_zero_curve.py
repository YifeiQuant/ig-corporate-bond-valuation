from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.curve import build_zero_curve, format_curve_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a Treasury zero curve for a chosen evaluation date."
    )
    parser.add_argument(
        "--input",
        default="data/raw/treasury_curve.csv",
        help="Path to the Treasury par-yield history CSV.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Evaluation date in YYYY-MM-DD format. Defaults to the latest date in the file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the bootstrapped zero curve CSV.",
    )
    parser.add_argument(
        "--coupon-freq",
        type=int,
        default=2,
        help="Coupon frequency used when bootstrapping the par curve.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    as_of_date, zero_curve = build_zero_curve(
        path=args.input,
        eval_date=args.date,
        coupon_freq=args.coupon_freq,
    )
    display_curve = format_curve_table(zero_curve)

    print(f"Treasury zero curve as of {as_of_date.date()}")
    print(display_curve.to_string(index=False))

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("data/processed") / f"zero_curve_{as_of_date.date()}.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    zero_curve.to_csv(output_path, index=False)
    print(f"\nSaved zero curve to {output_path}")


if __name__ == "__main__":
    main()
