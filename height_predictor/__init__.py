"""
height_predictor package

Provides simple, non-medical heuristics for predicting height change over one year.
Use predict_height_in_one_year from height_predictor.model for core logic.
"""

from .model import predict_height_in_one_year

__all__ = ["predict_height_in_one_year"]