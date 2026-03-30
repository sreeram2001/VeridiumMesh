"""
Training script for the Isolation Forest model.

Pipeline:
  1. Load features.csv (built by scripts/build_features.py)
  2. Fit a StandardScaler on the 4 input features
  3. Train an IsolationForest with contamination=0.1
  4. Compute normalisation params (score_min, score_max)
  5. Save everything: isoforest.joblib, scaler.joblib, norm_params.joblib

"""