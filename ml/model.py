"""
Loads the trained Isolation Forest and scaler at import time, then exposes
score_project() which takes raw features and returns a risk score.

Input features:
  R_ratio     - issuance volume vs peer average
  Vintage_Age - how old the project is
  M_flag      - 1 if it's a historically risky project type
  T_flag      - 1 if the volume is spiking

Output:
  A float between 0.0 and 1.0. Higher means sketchier.
  Anything >= 0.8 gets flagged as high risk on the ledger.
"""

import os
import numpy as np
import joblib

BASE = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(_BASE, "isoforest.joblib"))
scaler = joblib.load(os.path.join(_BASE, "scaler.joblib"))
norm_params = joblib.load(os.path.join(_BASE, "norm_params.joblib"))

FEATURE_COLS = ["R_ratio", "Vintage_Age", "M_flag", "T_flag"]
SCORE_MIN = _norm_params["score_min"]
SCORE_MAX = _norm_params["score_max"]


def score_project(features: dict) -> float:
    """
    Score a project for fraud risk using the Isolation Forest.

    Pass in a dict with R_ratio, Vintage_Age, M_flag, T_flag.
    Returns a risk score in [0.0, 1.0] — higher = more suspicious.
    """