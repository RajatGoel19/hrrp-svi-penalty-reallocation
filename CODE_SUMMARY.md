# Code Summary — `Paper1_HRRP_Penalty_Reallocation.ipynb`

A per-cell walkthrough of the notebook. It runs top-to-bottom; every cell depends on the ones
above it. The notebook loads the bundled public data from `data/` (shipped with the submission),
then reproduces CMS's penalty, recomputes it under a community-vulnerability peer grouping, and
quantifies the reallocation.

**Data flow:** load bundled data → build merged table → reproduce official penalty (gate) → SVI counterfactual
(pp + $) → statistics → sensitivity → robustness → figure.

**Convention:** odd-numbered descriptions below are markdown headers; the substantive work is in the
code cells. Section numbers (§0–§7) match the headings in the notebook.

---

## §0 — Setup, configuration, and helpers *(code)*
**Purpose:** establish everything the rest of the notebook reuses.
- **Imports:** `os, re, zipfile, math, pathlib, numpy, pandas, matplotlib`.
- **Paths:** `PROJECT_ROOT = Path.cwd()`; creates `data/{raw,external,processed}` and `outputs/{tables,figures}`.
- **Constants:** `PENALTY_CAP = 0.03` (HRRP's 3% maximum payment cut), `N_SOCIAL_QUINTILES = 5`,
  `N_BOOTSTRAP = 2000`, `RANDOM_SEED = 42`, `CI_LEVEL = 0.95`, `PRIMARY_SVI_COL = 'RPL_THEMES'`,
  the six HRRP `CONDITIONS` (AMI, COPD, HF, pneumonia, CABG, THA/TKA) and their lowercase `TAGS`.
- **Helper functions:**
  - `norm_county(name)` — upper-cases and strips "COUNTY/PARISH/BOROUGH/…" so hospital and SVI county names join.
  - `ownership_category(x)` — collapses CMS's ownership strings into For-profit / Nonprofit / Government.
  - `REGION` — dict mapping each state to its census region.
  - `ci(a)` — percentile 95% confidence interval from a bootstrap array.
  - `_ncdf(z)` — standard-normal CDF (via `math.erf`) used for p-values.
  - `ols_cluster(y, X, clusters)` — ordinary least squares with **county-cluster-robust (CR1)** standard
    errors; returns coefficients, SEs, and p-values. Used wherever SVI appears (hospitals in a county
    share one SVI value, so naïve SEs would be too small).
  - `spearman(a, b)` — Spearman rank correlation + approximate p-value.

**Output:** prints the project root (sanity check that paths resolved).

---

## §1 — Load bundled public data *(code)*
**Purpose:** load every input from the `data/` directory that ships with the submission (no network).
- **`DATA_FILES` manifest:** maps each dataset to its bundled path —
  `data/raw/hospital_readmissions.csv` (HRRP ERR), `hospital_general_info.csv`, `hrrp_impact_file.xlsx`
  (FY2026 HRRP supplemental); `data/external/SVI_2022_US_county.csv` (CDC/ATSDR SVI 2022) and
  `medicare_inpatient_by_provider.csv` (dollar base).
- **Optional ADI:** `ADI_DIR = data/external/adi`; if only `adi-download.zip` is present, it is
  unzipped locally into `data/external/adi/` (Neighborhood Atlas, used for the cross-index sensitivity).
- **Presence gate:** asserts every manifest file exists (raising a clear "include the data/ folder"
  message if not), then prints an `[OK]` line per file confirming what loaded.
- **Sources (for re-obtaining the data):** each file is public — CMS Provider Data Catalog
  (HRRP ERR, Hospital General Info), the FY2026 IPPS/LTCH Final-Rule HRRP supplemental ZIP,
  data.cms.gov Medicare Inpatient by Provider, CDC/ATSDR SVI 2022, and the Neighborhood Atlas ADI
  (free registration). See `Data_Download_Guide` for the per-source links and steps.

---

## §2 — Build the facility-level dataset *(code)*
**Purpose:** merge the FY2026 ERR file + hospital info + SVI into one hospital-per-row table.
- `weighted_mean(err, w)` — discharge-weighted mean ERR (falls back to unweighted if weights missing).
- `build_readmissions()` — reads the ERR file, groups by `Facility ID` → `state`,
  `n_measures_reported`, `mean_err_wt` (discharge-weighted composite ERR), `total_discharges`.
- `load_general_info()` — reads Hospital General Info → `facility_id, state, zip, county_norm,
  hospital_type, ownership_cat, is_acute`.
- `load_svi()` — reads the CDC SVI county file → `state, county_norm, county_fips, svi_overall`
  (overall percentile) and `svi_t1…t4` (the four sub-themes); recodes the `-999` missing flag to NaN.
- Merges all three, computes `svi_quintile` (national quintiles, 5 = most vulnerable).
- **Output:** `data/processed/analytic_facility.csv`; prints facility counts and SVI match rate.

---

## §3 — Reproduce the official HRRP penalty (validation gate) *(code)*
**Purpose:** prove we can rebuild CMS's *actual* penalty before changing anything (the trust check).
- `_find_col(cols, *tokens)` — fuzzy, case-insensitive column finder (CMS headers vary year to year
  and carry stray spaces).
- `load_impact(path)` — locates the data sheet (the one whose header contains "payment adjustment
  factor" and "ccn"), reads it, and standardizes columns to: `ccn, paf, dual_proportion, peer_group,
  neutrality`, plus per-condition `err_*, med_* (peer-group median), drg_* (DRG payment ratio)`.
- `total_excess(err, drg, med)` — Σ over the six conditions of `DRG_ratio × max(0, ERR − peer_median)`
  (the program's "excess readmission payment ratio").
- Reconstructs `PAF = 1 − min(0.03, neutrality × total_excess)` and compares to the published PAF.
- **Output:** `data/processed/official_supplemental.csv`; prints **MAE, r, % within ±0.0005** and the
  penalty rate. (FY2026: MAE ≈ 0.0002, r ≈ 0.99, 78.2% penalized — gate passes.)

---

## §4 — PRIMARY: SVI peer grouping vs the actual dual grouping (dollar-neutral) *(code)*
**Purpose:** the core experiment — re-group hospitals by community vulnerability and recompute penalties.
- `row_medians(err, quint)` / `svi_median_matrix(err_mat, quint)` — per-condition median ERR within
  each group, broadcast back to hospitals.
- `solve_k_dollar(exc, nu, pay, target)` — bisection that finds the single neutrality-scaling factor
  `k` so that **payment-weighted** total penalty dollars under SVI grouping equal the actual total
  (enforces **dollar-neutrality** — the reallocation neither adds nor removes money).
- Builds the analytic cohort `cf`: official supplemental + SVI (+ sub-themes, county FIPS) + Medicare
  payments + hospital size; keeps hospitals with all of {SVI, neutrality, PAF, payments}. Adds
  `svi_quintile`, `region`, and a `cluster` id (state_county). Joins **county-aggregated ADI**.
- Computes observed reduction `red_obs`; recomputes excess + reduction under SVI medians; solves
  dollar-neutral `k`; then `delta_pp = (red_svi − red_obs)×100` and `delta_dollars = pay × (red_svi − red_obs)`.
- **Bootstrap (2,000×):** resample hospitals, recompute group medians + `k` + per-quintile mean change →
  percentile **95% CIs**.
- **Outputs:** `outputs/tables/official_reallocation_by_svi.csv` (Table 2),
  `data/processed/official_counterfactual.csv`; prints cohort size, `k`, the "$ conserved" check,
  % status changed, and means by quintile / ownership / region.

---

## §4b — Dollar reallocation *(code)*
**Purpose:** convert the percentage-point change into dollars.
- Aggregate actual penalty `$ = Σ (1 − paf) × pay`; dollars reallocated `= Σ|delta_dollars| / 2`.
- Net dollars and mean dollars-per-hospital by SVI quintile.
- **Outputs:** `outputs/tables/official_reallocation_dollars_by_svi.csv` (Table 3),
  `data/processed/official_counterfactual_dollars.csv`; prints the aggregate penalty and the
  reallocated total (which conserves to ≈ 0 across quintiles).

---

## §4c — Statistical analysis (county-clustered) *(code)*
**Purpose:** characterize SVI vs the incumbent measure and test the gradient.
1. **SVI vs dual proportion** — Spearman ρ + shared variance (are they distinct?).
1b. **SVI vs ADI** — Spearman ρ (are the two deprivation indices distinct?).
2. **Trend** — regress `delta_pp` on continuous SVI, county-clustered → slope, 95% CI, p (is the
   reallocation monotonic?).
3. **Nested association models** (full cohort, all n=2,832 hospitals; county-clustered) — regress
   `mean_err` on SVI, adding one block at a time: SVI alone β=0.024 (p<0.001); dual alone β=0.059;
   **SVI+dual β=0.015 (p<0.001** — SVI adds signal beyond the incumbent measure; incremental R²=0.005);
   +ownership β=0.014 (p=0.003); **+region → β=0.007 (p=0.23)**. SVI stays significant until **census
   region** enters (the single largest R² increment, 0.035→0.054); region — not the dual share — is what
   attenuates it. Size enters only as a robustness (log payments n=2,832, β=0.006; or log discharges
   n=2,359, β=0.009), so no hospitals are dropped and the conclusion is invariant. VIFs <2.2, so this is not
   a variance-inflation artifact; whether region is a legitimate control or an over-adjustment (a coarser
   measure of the same place-based variation SVI captures) is an open specification question, and the full
   model is reported as a sensitivity. Reproduce with `analysis/svi_nested_regressions.py`.

---

## §4d — Sensitivity to index and cut-points *(code)*
**Purpose:** confirm the reallocation isn't an artifact of one index or one set of cut-points.
- `_med_mat(err, q)` — group-median matrix that works for any number of groups.
- `run_cf(group_values, ngroups)` — re-runs the full dollar-neutral counterfactual for an arbitrary
  grouping and returns `delta_pp`.
- Runs it for SVI overall (tertiles / quintiles / deciles), each of the four SVI sub-themes, and the
  **Area Deprivation Index (ADI)**, reporting the most- vs least-vulnerable mean change.
- **Output:** `outputs/tables/sensitivity_index_cutpoints.csv` (Table 4). Direction holds throughout.

---

## §5 — Robustness: simplified operationalization *(code)*
**Purpose:** show the result survives a much simpler rule than the official formula.
- Restricts to acute-care hospitals with ERR + SVI; `flags(perf, quint)` marks a hospital if its mean
  ERR exceeds a benchmark median — under a **non-stratified** (national median) vs an
  **SVI-stratified** (within-quintile median) benchmark.
- Reports % reclassified, the flag rate per quintile under each scheme, and the Q5/Q1 flag-rate ratio
  (1.46 → 1.00 under stratification).
- **Output:** `outputs/tables/disparate_impact_flagrates.csv`.

---

## §6 — Figure 1 *(code)*
**Purpose:** the paper's single figure.
- **Panel A:** bars (± 95% CI) of the mean change in payment reduction by SVI quintile (official FY2026).
- **Panel B:** flag rates by quintile under non-stratified vs SVI-stratified benchmarks (the parity result).
- **Output:** `outputs/figures/fig_equity_reallocation.png` (embedded in the manuscript).

---

## §7 — Summary *(markdown)*
Plain-language recap: the gate passes, the reallocation shifts penalties off the most vulnerable
hospitals (dollar-neutral, county-clustered trend p < 0.001), SVI carries a small,
specification-dependent independent association beyond dual-eligibility (significant alongside dual,
ownership, and size; attenuating to non-significance only when census region is added), and a
simplified check reproduces the direction.

---

## Outputs at a glance
| File | Written by | Contents |
|---|---|---|
| `data/processed/analytic_facility.csv` | §2 | merged FY2026 ERR + hospital + SVI table |
| `data/processed/official_supplemental.csv` | §3 | supplemental file + reproduced PAF |
| `data/processed/official_counterfactual.csv` | §4 | per-hospital pp reallocation + covariates |
| `data/processed/official_counterfactual_dollars.csv` | §4b | per-hospital dollar reallocation |
| `outputs/tables/official_reallocation_by_svi.csv` | §4 | Table 2 (pp by quintile + CIs) |
| `outputs/tables/official_reallocation_dollars_by_svi.csv` | §4b | Table 3 ($ by quintile) |
| `outputs/tables/sensitivity_index_cutpoints.csv` | §4d | Table 4 (index/cut-point sensitivity) |
| `outputs/tables/disparate_impact_flagrates.csv` | §5 | flag rates by quintile |
| `outputs/figures/fig_equity_reallocation.png` | §6 | Figure 1 |
