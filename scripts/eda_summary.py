import pandas as pd
import sys

try:
    p = pd.read_csv("data/projects_clean.csv")
except Exception as e:
    print("ERROR reading CSV:", e)
    sys.exit(1)
print("rows,cols:", p.shape)
print("\n--- Registry (top 10) ---")
print(p["Voluntary Registry"].value_counts().head(10).to_string())
if "Type" in p.columns:
    print("\n--- Project Types (top 10) ---")
    print(p["Type"].value_counts().head(10).to_string())
if "Country" in p.columns:
    print("\n--- Countries (top 10) ---")
    print(p["Country"].value_counts().head(10).to_string())
issue_years = [str(y) for y in range(1996, 2026) if str(y) in p.columns]
if issue_years:
    yearly_total = p[issue_years].apply(pd.to_numeric, errors="coerce").sum(axis=0)
    yearly_total.index = yearly_total.index.astype(int)
    peak = yearly_total.idxmax()
    peakval = yearly_total.max()
    nonzero = yearly_total[yearly_total > 0]
    low = nonzero.idxmin()
    lowval = nonzero.min()
    print(
        f"\n--- Yearly totals ---\nFound years: {len(issue_years)}; Peak: {peak} ({peakval / 1e6:.2f}M); Lowest non-zero: {low} ({lowval / 1e6:.3f}M)"
    )
col = next(
    (c for c in p.columns if "total credits" in c.lower() and "issued" in c.lower()),
    None,
)
if col:
    issued = pd.to_numeric(p[col], errors="coerce").dropna()
    issued = issued[issued > 0]
    print("\n--- Total issued stats (millions) ---")
    print(
        f"count: {len(issued):,}, median: {issued.median() / 1e6:.3f}M, mean: {issued.mean() / 1e6:.3f}M, max: {issued.max() / 1e6:.3f}M"
    )
    print("\n--- Top projects by total issued ---")
    top = p.sort_values(col, ascending=False).head(10)[
        ["Project ID", "Project Name", col, "Voluntary Registry", "Type", "Country"]
    ]
    print(top.to_string(index=False))
else:
    print("WARNING: could not find Total Credits Issued column")
