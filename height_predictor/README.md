# height_predictor

Simple, non-medical heuristics to predict height change over one year. This is a toy example for demonstration only; it is not medical advice.

## Contents
- Core function: `predict_height_in_one_year` in `height_predictor/model.py`
- CLI entry point: `height_predictor/cli.py`
- Basic assertions: `height_predictor/test_predict.py`

## Quick start (CLI)

Run directly from the project root:

- Metric output (default):
  ```
  python -m height_predictor.cli --height 180.0 --age 35 --sex male
  ```

- Imperial output (feet/inches, inches rounded to 0.1):
  ```
  python -m height_predictor.cli --height 140 --age 12 --sex female --units imperial
  ```

You may also call:
```
python height_predictor/cli.py --height 170 --age 72 --sex male
```

Exit status:
- 0 on success
- Non-zero on invalid inputs (an error message is printed to stderr)

## Python API

```python
from height_predictor.model import predict_height_in_one_year

res = predict_height_in_one_year(current_height_cm=140.0, age_years=12.0, sex="male")
print(res["predicted_height_cm"], res["delta_cm"], res["rationale"])
```

Return format (dict):
- predicted_height_cm (float): Predicted height after one year, in cm
- delta_cm (float): Applied change in cm
- rationale (str): Explanation of the applied rule

## Heuristic (simplified)
- Children (< 18 years): age- and sex-based annual growth velocity:
  - 0–<5: 6.5 cm/yr
  - 5–<12: 5.0 cm/yr
  - 12–<15: puberty peak — male 7.0, female 6.0 cm/yr
  - 15–<17: male 3.0, female 2.0 cm/yr
  - 17–<18: male 1.0, female 0.5 cm/yr
- Adults (18–49): 0 cm/yr (stable)
- Older adults (≥ 50): shrinkage
  - 50–69: male −0.20, female −0.25 cm/yr
  - ≥ 70: male −0.50, female −0.60 cm/yr

Input validation:
- height: 30–272 cm
- age: 0–120 years
- sex: "male" or "female"

## Tests (no framework)
Run:
```
python height_predictor/test_predict.py
```

All dependencies are from the Python standard library.