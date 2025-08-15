"""Basic assertions for height prediction heuristics (no test framework required).

Run directly:
    python height_predictor/test_predict.py
"""

from height_predictor.model import predict_height_in_one_year


def test_child_growth_increases_height() -> None:
    current = 130.0
    res = predict_height_in_one_year(current_height_cm=current, age_years=12.0, sex="male")
    assert res["delta_cm"] > 0.0, "Child growth should increase height (positive delta)"
    assert res["predicted_height_cm"] > current, "Predicted height should be greater than current"


def test_adult_stable_returns_zero_delta() -> None:
    current = 180.0
    res = predict_height_in_one_year(current_height_cm=current, age_years=35.0, sex="female")
    assert res["delta_cm"] == 0.0, "Adult stability (18–49) should yield zero delta"
    assert res["predicted_height_cm"] == current, "Predicted height should equal current for stable adults"


def test_older_adult_shrink_returns_negative_delta() -> None:
    current = 170.0
    res = predict_height_in_one_year(current_height_cm=current, age_years=72.0, sex="male")
    assert res["delta_cm"] < 0.0, "Older adult shrinkage should reduce height (negative delta)"
    assert res["predicted_height_cm"] < current, "Predicted height should be less than current for older adults"


if __name__ == "__main__":
    # Execute tests when run as a script
    test_child_growth_increases_height()
    test_adult_stable_returns_zero_delta()
    test_older_adult_shrink_returns_negative_delta()
    print("All tests passed.")