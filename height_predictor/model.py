"""Model functions for predicting height change over one year.

This module exposes a simple, non-medical heuristic:
- Children (< 18 years): apply an age- and sex-based annual growth velocity (cm/year).
- Adults (18–49 years): assume no change.
- Older adults (≥ 50 years): apply a small, age-bracket- and sex-dependent annual shrinkage.

These rules are intentionally simple and for demonstration purposes only. They are NOT medical advice.

Example:
    from height_predictor.model import predict_height_in_one_year

    result = predict_height_in_one_year(current_height_cm=140.0, age_years=12.0, sex="male")
    print(result["predicted_height_cm"], result["delta_cm"], result["rationale"])
"""

from typing import Literal, Dict


def _child_growth_velocity_cm_per_year(age_years: float, sex: Literal["male", "female"]) -> float:
    """Return a simple age- and sex-based annual growth velocity in cm/year.

    Heuristic (not medical advice):
    - 0 ≤ age < 5: 6.5 cm/year (rapid early growth)
    - 5 ≤ age < 12: 5.0 cm/year (steady childhood growth)
    - 12 ≤ age < 15: puberty peak
        * male: 7.0 cm/year
        * female: 6.0 cm/year
    - 15 ≤ age < 17:
        * male: 3.0 cm/year
        * female: 2.0 cm/year
    - 17 ≤ age < 18:
        * male: 1.0 cm/year
        * female: 0.5 cm/year
    """
    if age_years < 5:
        return 6.5
    if age_years < 12:
        return 5.0
    if age_years < 15:
        return 7.0 if sex == "male" else 6.0
    if age_years < 17:
        return 3.0 if sex == "male" else 2.0
    # 17 ≤ age < 18
    return 1.0 if sex == "male" else 0.5


def _older_adult_shrinkage_cm_per_year(age_years: float, sex: Literal["male", "female"]) -> float:
    """Return annual shrinkage (negative cm/year) for older adults.

    Heuristic (not medical advice):
    - 50–69 years:
        * male: -0.20 cm/year
        * female: -0.25 cm/year
    - ≥ 70 years:
        * male: -0.50 cm/year
        * female: -0.60 cm/year
    """
    if 50 <= age_years < 70:
        return -0.20 if sex == "male" else -0.25
    # age ≥ 70
    return -0.50 if sex == "male" else -0.60


def predict_height_in_one_year(
    current_height_cm: float,
    age_years: float,
    sex: Literal["male", "female"],
) -> dict:
    """Predict height one year from now using a simple heuristic.

    Args:
        current_height_cm: Current height in centimeters. Must be realistic (30–272 cm).
        age_years: Current age in years. Must be within [0, 120].
        sex: Biological sex for heuristic branching; one of "male" or "female".

    Returns:
        dict with keys:
            - predicted_height_cm (float): Predicted height after one year, in cm.
            - delta_cm (float): The change applied in centimeters.
            - rationale (str): Short explanation of the rule applied.

    Raises:
        ValueError: If any input is invalid.

    Notes:
        - This is a toy model for demonstration only; it is not a medical tool.
    """
    # Validate inputs
    if not isinstance(current_height_cm, (int, float)) or not isinstance(age_years, (int, float)):
        raise ValueError("height and age must be numeric")
    if not isinstance(sex, str) or sex not in {"male", "female"}:
        raise ValueError("sex must be either 'male' or 'female'")
    if not (30.0 <= float(current_height_cm) <= 272.0):
        raise ValueError("current_height_cm must be within a realistic range (30–272 cm)")
    if not (0.0 <= float(age_years) <= 120.0):
        raise ValueError("age_years must be within [0, 120]")

    age = float(age_years)
    height = float(current_height_cm)

    if age < 18.0:
        delta_cm = _child_growth_velocity_cm_per_year(age, sex)
        rationale = f"child growth velocity applied (sex={sex}, age={age:.1f})"
    elif age < 50.0:
        delta_cm = 0.0
        rationale = "adult stability assumed (18–49 years)"
    else:
        delta_cm = _older_adult_shrinkage_cm_per_year(age, sex)
        bracket = "50–69" if age < 70.0 else "≥70"
        rationale = f"older adult shrinkage applied (sex={sex}, age={age:.1f}, bracket={bracket})"

    predicted = height + delta_cm
    return {
        "predicted_height_cm": predicted,
        "delta_cm": delta_cm,
        "rationale": rationale,
    }