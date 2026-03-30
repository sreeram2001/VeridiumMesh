"""
VeridiumMesh — Feature Engineering Script
==========================================
Reads the cleaned Berkeley VROD dataset (data/projects_clean.csv) and
computes the 4 ML input features used by the Isolation Forest model:

  - R_ratio     : Issuance volume relative to peer average for the project type
  - Vintage_Age : Current year minus the project vintage year
  - M_flag      : 1 if the project type is in the high-risk category set
  - T_flag      : 1 if R_ratio exceeds the spike threshold (3.0)

Output: data/features.csv

Usage:
  PYTHONPATH=. python scripts/build_features.py
"""

# TODO: Implement feature engineering pipeline
# See VeridiumAI/scripts/build_features.py for reference implementation
