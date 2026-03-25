"""
Step 1 of 2: Build features.csv from projects_clean.csv.
Computes R_ratio, T_flag, M_flag and ensures Vintage_Age is present.
Saves data/features.csv.
"""
import pandas as pd
import numpy as np

DATA = "data/projects_clean.csv"
OUT  = "data/features.csv"
TOTAL_ISSUED = "Total Credits  Issued"   # double-space — matches the actual column
YEAR_COLS = [str(y) for y in range(1996, 2026)]

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading projects_clean.csv …")
df = pd.read_csv(DATA)
print(f"  {len(df):,} rows × {df.shape[1]} columns")

# ── Fix 1: Methodology / Protocol missing → 'Unknown' ────────────────────────
meth_col = "Methodology / Protocol"
n_missing = df[meth_col].isna().sum()
df[meth_col] = df[meth_col].fillna("Unknown")
print(f"  Methodology missing filled: {n_missing:,}")

# ── Fix 2: Derive start_year + Vintage_Age if not already present ─────────────
if "Vintage_Age" not in df.columns:
    print("  Deriving start_year from year columns …")
    existing_years = [y for y in YEAR_COLS if y in df.columns]

    def first_issuance_year(row):
        for y in existing_years:
            val = row[y]
            if pd.notna(val) and val > 0:
                return int(y)
        return pd.NA

    df["start_year"] = df.apply(first_issuance_year, axis=1)
    df["start_year_missing"] = df["start_year"].isna().astype(int)
    df["Vintage_Age"] = (2026 - pd.to_numeric(df["start_year"], errors="coerce")).clip(lower=0)
    print(f"  Vintage_Age: resolved for {df['start_year'].notna().sum():,} projects")
else:
    print(f"  Vintage_Age already present — skipping derivation")

# ── Feature 1: R_ratio ────────────────────────────────────────────────────────
print("Computing R_ratio …")
df[TOTAL_ISSUED] = pd.to_numeric(df[TOTAL_ISSUED], errors="coerce")

peer_avg = df.groupby(["Voluntary Registry", "Type", "Country"])[TOTAL_ISSUED].transform("mean")
df["R_ratio"] = df[TOTAL_ISSUED] / peer_avg
df["R_ratio"] = df["R_ratio"].replace([np.inf, -np.inf], np.nan).fillna(1.0)
print(f"  R_ratio — median: {df['R_ratio'].median():.2f}  max: {df['R_ratio'].max():.1f}")

# ── Feature 2: M_flag ─────────────────────────────────────────────────────────
print("Computing M_flag …")
HIGH_RISK_TYPES = {
    "Wind", "Hydropower", "Solar - Centralized", "Solar - Distributed",
    "Biomass", "Fossil Fuel Switching", "Large Hydropower",
    "Renewable Energy", "Geothermal",
}
df["M_flag"] = df["Type"].apply(lambda t: 1 if pd.notna(t) and t in HIGH_RISK_TYPES else 0)
print(f"  M_flag=1: {df['M_flag'].sum():,} ({df['M_flag'].mean()*100:.1f}%)")

# ── Feature 3: T_flag ─────────────────────────────────────────────────────────
print("Computing T_flag …")
existing_years = [y for y in YEAR_COLS if y in df.columns]
year_data = df[existing_years].apply(pd.to_numeric, errors="coerce")
df["max_single_year"] = year_data.max(axis=1)

vintage_safe = pd.to_numeric(df["Vintage_Age"], errors="coerce").replace(0, np.nan)
df["historical_yearly_avg"] = df[TOTAL_ISSUED] / vintage_safe
df["historical_yearly_avg"] = df["historical_yearly_avg"].fillna(df[TOTAL_ISSUED])

df["T_flag"] = (
    (df["max_single_year"] > 3 * df["historical_yearly_avg"]) &
    (df["max_single_year"] > 10_000)
).astype(int)
print(f"  T_flag=1: {df['T_flag'].sum():,} ({df['T_flag'].mean()*100:.1f}%)")

# ── Save features.csv ─────────────────────────────────────────────────────────
features_df = df[[
    "Project ID", "Voluntary Registry", "Type", "Country",
    "R_ratio", "Vintage_Age", "M_flag", "T_flag",
]].copy()

before = len(features_df)
features_df = features_df.dropna(subset=["R_ratio", "Vintage_Age", "M_flag", "T_flag"])
after = len(features_df)
print(f"\nDropped {before - after:,} rows with NaN features. Keeping {after:,}.")

features_df.to_csv(OUT, index=False)
print(f"✅  Saved {OUT}  ({after:,} rows × {features_df.shape[1]} columns)")

print("\n── Feature summary ──────────────────────────────────────")
print(features_df[["R_ratio", "Vintage_Age", "M_flag", "T_flag"]].describe().round(2).to_string())
