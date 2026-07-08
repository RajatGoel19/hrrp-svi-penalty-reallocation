# v1.0.0 — Initial archived release

Reproducible analysis code and public input data accompanying the manuscript
**"Stratifying Hospital Readmission Penalties by Community Social Vulnerability:
A Budget-Neutral Reallocation Simulation."**

## What this release contains
- `Paper1_HRRP_Penalty_Reallocation.ipynb` — the single, top-to-bottom analysis notebook.
- `data/raw/`, `data/external/` — the public CMS and CDC/ATSDR input files (see note below).
- `outputs/tables/`, `outputs/figures/` — the exact tables and figure reported in the paper.
- `README.md`, `CODE_SUMMARY.md`, `Data_Download_Guide`, `Variable_Descriptions_Detailed` — documentation.

## Key results reproduced by the notebook
- Validation gate: reconstructed CMS FY2026 payment-adjustment factor with MAE 0.00016, r = 0.99 (92% within ±0.0005).
- Dollar-neutral counterfactual: reconstructed penalty total $368.4M (k = 0.997; residual $0.000M); $14.1M (3.8%) reallocated under SVI peer grouping.
- Penalized share 78.6% → 90.9% (n = 2,832) with 12.7% status flips; county-clustered trend slope −0.090 pp per unit SVI (p < 0.001).
- SVI is not an independent predictor of excess readmissions after adjusting for dual-eligible share (p = 0.25).

## Data note
Bundled CMS and CDC/ATSDR files are U.S. Government / public-domain works, included for
one-click reproducibility. The **Area Deprivation Index (Neighborhood Atlas)** is **not**
redistributed here (its terms restrict redistribution); obtain it via free registration as
described in the Data Download Guide. The notebook runs without it and treats the ADI
cross-index check as an optional sensitivity.

## How to run
```
pip install -r requirements.txt
jupyter notebook Paper1_HRRP_Penalty_Reallocation.ipynb   # run top to bottom
```
