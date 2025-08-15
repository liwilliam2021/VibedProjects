"""Command-line interface for the height_predictor package.

Usage examples:
    python -m height_predictor.cli --height 180.0 --age 35 --sex male
    python height_predictor/cli.py --height 140 --age 12 --sex female --units imperial

All inputs are provided in metric units (height in cm, age in years). The --units
flag only affects output formatting.
"""

from __future__ import annotations

import argparse
import sys
from typing import Literal, Optional

from .model import predict_height_in_one_year


def _cm_to_feet_inches_str(cm: float) -> str:
    """Convert centimeters to a "X ft Y.Y in" string, inches rounded to 0.1.

    Handles rounding that may cause inches to reach exactly 12.0.
    """
    total_inches = round(cm / 2.54, 1)
    feet = int(total_inches // 12)
    rem_inches = round(total_inches - feet * 12, 1)
    if rem_inches >= 12.0:  # handle edge cases due to rounding
        feet += 1
        rem_inches = 0.0
    return f"{feet} ft {rem_inches:.1f} in"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="height_predictor",
        description="Predict height one year from now using simple, non-medical heuristics.",
    )
    parser.add_argument("--height", type=float, required=True, help="Current height in centimeters (e.g., 180.0)")
    parser.add_argument("--age", type=float, required=True, help="Current age in years (e.g., 35)")
    parser.add_argument(
        "--sex",
        type=str,
        required=True,
        choices=["male", "female"],
        help="Sex for heuristic branching: 'male' or 'female'",
    )
    parser.add_argument(
        "--units",
        type=str,
        choices=["cm", "imperial"],
        default="cm",
        help="Output units for predicted height (default: cm). 'imperial' prints feet+inches.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = predict_height_in_one_year(
            current_height_cm=float(args.height),
            age_years=float(args.age),
            sex=args.sex,  # type: ignore[arg-type]
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # unexpected errors
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    predicted_cm = float(result["predicted_height_cm"])
    delta_cm = float(result["delta_cm"])
    rationale = str(result["rationale"])

    sign = "+" if delta_cm > 0 else ("−" if delta_cm < 0 else "")
    # Use Unicode minus for readability in CLI
    if args.units == "imperial":
        predicted_str = _cm_to_feet_inches_str(predicted_cm)
        print(f"Predicted height in 1 year: {predicted_str} (delta {sign}{abs(delta_cm):.1f} cm) — {rationale}")
    else:
        print(f"Predicted height in 1 year: {predicted_cm:.1f} cm (delta {sign}{abs(delta_cm):.1f} cm) — {rationale}")


if __name__ == "__main__":
    main()