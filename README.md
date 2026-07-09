# Paper 1 - HRRP Penalty Reallocation under Social-Risk Adjustment

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21269652.svg)](https://doi.org/10.5281/zenodo.21269652)

**Research question.** Does stratifying Medicare's Hospital Readmissions Reduction Program (HRRP)
by **community social vulnerability (SVI)** instead of dual-eligible proportion change which
hospitals are penalized for excess readmissions - and does it shift penalty burden off hospitals
serving the most vulnerable communities? A **policy-simulation** study (not causal inference) of
U.S. acute-care hospitals using only public data.

- **Reporting:** RECORD (primary) + PROGRESS-Plus (equity).
- **Guardrail:** no fabricated numbers; every figure and statistic is produced by the notebook and written to `outputs/`.
- **Reproduce everything:** `pip install -r requirements.txt`, then open **`Paper1_HRRP_Penalty_Reallocation.ipynb`** and **Run All** (loads data from the bundled `data/` folder - no downloads).

---

## 1. Locked design decisions
| Item | Choice |
|---|---|
| Primary social-risk index | **CDC/ATSDR SVI** overall county ranking (`RPL_THEMES`). ADI = optional sensitivity. |
| Adjustment mechanism | **Peer-group re-stratification** - replace dual-proportion peer groups with SVI quintiles. |
| Primary endpoint | **Payment-reduction reallocated** (pp of base operating DRG payments; **translated to approximate $** via Medicare inpatient payments). |
| Secondary endpoint | **Penalty-status reclassification** (penalized under SVI vs actual). |
| Uncertainty | Hospital-level nonparametric bootstrap, 2,000 resamples, percentile 95% CIs. |

---

## 2. Data (sources, contents, linkage)

All CMS and CDC inputs are public and **bundled in `data/`**; the notebook loads them from disk (no downloads).
The Area Deprivation Index (section 2.6) is the one exception: it is registration-gated at the Neighborhood
Atlas and is **not redistributed here** (obtain it separately; the ADI cross-check is optional).
See **`Data_Download_Guide.docx`** (project root) for each source's link and step-by-step download instructions.

### 2.1 CMS HRRP Excess Readmission Ratios - `data/raw/hospital_readmissions.csv`
- **Source:** CMS Provider Data Catalog - `https://data.cms.gov/provider-data/dataset/9n3s-kdb3`
  (dataset id `9n3s-kdb3`).
- **Edition:** FY2026 (performance period 07/01/2021–06/30/2024). ~2.1 MB.
- **Shape:** 18,330 rows = hospital × measure; **3,055** facilities with ≥1 reportable measure.
- **Columns:** Facility Name, **Facility ID** (6-digit CCN), State, **Measure Name**, Number of
  Discharges, Footnote, **Excess Readmission Ratio (ERR)**, Predicted/Expected Readmission Rate,
  Number of Readmissions, Start/End Date.
- **Measures (6):** READM-30 for AMI, CABG, COPD, HF, HIP-KNEE (THA/TKA), PN.

### 2.2 CMS Hospital General Information - `data/raw/hospital_general_info.csv`
- **Source:** CMS Provider Data Catalog - `https://data.cms.gov/provider-data/dataset/xubh-q36u`
  (dataset id `xubh-q36u`). ~1.5 MB; **5,432** hospitals; 38 columns.
- **Used columns:** Facility ID, State, **ZIP Code**, **County/Parish**, **Hospital Type**
  (acute-care vs critical-access), **Hospital Ownership**, Hospital overall (star) rating.
- Derived: `ownership_cat` (For-profit / Nonprofit / Government), `is_acute`, `is_critical_access`,
  normalized county name for the SVI join.

### 2.3 CDC/ATSDR Social Vulnerability Index 2022 (county) - `data/external/SVI_2022_US_county.csv`
- **Source:** `https://svi.cdc.gov/Documents/Data/2022/csv/states_counties/SVI_2022_US_county.csv`.
- ~2.3 MB; **3,144** counties; 158 columns.
- **Used:** ST_ABBR, COUNTY, **FIPS**, **RPL_THEMES** (overall vulnerability percentile, 0–1;
  higher = more vulnerable), RPL_THEME1–4 (socioeconomic, household, minority/language, housing/transport).
- Missing values coded `-999` → set to NA.

### 2.4 HRRP Supplemental Data File (the penalty file) - `data/raw/hrrp_impact_file.xlsx`
- **Source (direct download):**
  `https://www.cms.gov/files/zip/fy2026-hospital-readmissions-reduction-program-supplemental-data-file.zip`
  (FY2026 edition, from the FY2026 IPPS Final-Rule page).
- ~1.7 MB ZIP → sheet **`FR FY 2026`** (header on row 2), **2,946** hospitals.
- **Per-hospital columns:** Hospital CCN, **Payment adjustment factor (PAF)**, **Dual proportion**,
  **Peer group assignment** (1–5), **Neutrality modifier**, and for each of the 6 conditions:
  Number of eligible discharges, **ERR**, **Peer-group median ERR**, Penalty indicator (Y/N),
  **DRG payment ratio** (condition payments ÷ total base operating DRG payments).
- This single file enables both the actual penalty *and* its recomputation under a new grouping.

### 2.5 Medicare Inpatient Hospitals - by Provider - `data/external/medicare_inpatient_by_provider.csv`
- **Source:** data.cms.gov catalog, dataset **"Medicare Inpatient Hospitals - by Provider"** (most recent release).
  Direct file used:
  `https://data.cms.gov/sites/default/files/2026-04/d9525c59-002b-45b3-af22-c81061a62dcd/mup_inp_ry26_p04_v10_dy24_prv.csv`
- ~1.8 MB. **Used columns:** `Rndrng_Prvdr_CCN` (CCN), `Tot_Mdcr_Pymt_Amt` (total Medicare inpatient payments).
- **Purpose:** the dollar base for translating payment-reduction changes (pp) into approximate dollars; linked to the cohort by CCN.

### 2.6 Area Deprivation Index (ADI 2023) - `data/external/adi-download.zip` → `data/external/adi/`
- **Source:** Neighborhood Atlas (`neighborhoodatlas.medicine.wisc.edu`), **2023** national block-group file,
  12-digit FIPS, all states. **Requires a free registration** - the only manually-downloaded input.
- ~12 MB CSV (`US_2023_ADI_Census_Block_Group_v4_0_1.csv`). **Used:** `FIPS` (block group), `ADI_NATRANK` (national percentile).
- **Purpose:** county-aggregated (median) deprivation index for a **cross-index sensitivity** vs SVI; the notebook auto-extracts the zip.

### 2.7 Linkage
- HRRP/Supplemental ↔ Hospital Info on **Facility ID = CCN**.
- Hospital ↔ county SVI on **(state, normalized county name)**; 6 independent-city name collisions
  dropped (~97% county match; a ZIP-to-county-FIPS crosswalk could further reduce the ~3% unmatched).

### 2.8 Optional future extensions
| Extension | For | Source |
|---|---|---|
| IPPS **Impact File** (exact base operating DRG $) | replace the Medicare-payment **proxy** with exact $ | CMS IPPS final-rule data files |
| RUCA rurality codes | finer rural / safety-net stratification | USDA ERS |

### 2.9 Derived datasets (`data/processed/`)
`analytic_facility.csv` (merged FY2026 table) · `official_supplemental.csv` (official + reproduced PAF) ·
`official_counterfactual.csv` (SVI recompute, pp) · `official_counterfactual_dollars.csv` (per-hospital $ reallocation).
Large CSVs are git-ignored and regenerated by the pipeline.

---

## 3. Method (validated)
The official HRRP payment adjustment factor is reproduced as
`PAF = 1 − min(0.03, neutrality × Σ_condition[ DRG-payment-ratio × max(0, ERR − peer-median) ])`.
The counterfactual replaces each condition's **peer-group median ERR** (currently computed within
dual-proportion groups) with the median **within SVI quintiles**, then recomputes the PAF with the
same formula. Reclassification and the per-hospital change in payment reduction are the endpoints.

---

## 4. Code - one notebook
All logic lives in a single self-contained, executed notebook:
**`Paper1_HRRP_Penalty_Reallocation.ipynb`** - 7 sections run top-to-bottom:

0. Setup, configuration, helpers
1. Load data from the bundled `data/` directory (no downloads; sources documented for provenance)
2. Build the facility-level dataset (FY2026 ERR + Hospital info + SVI)
3. **Reproduce the official HRRP payment adjustment factor - validation gate**
4. **PRIMARY** - recompute penalties under SVI peer grouping vs the actual dual-eligible grouping
5. Robustness - current-year FY2026 flag reallocation
6. Figure - reallocation + flag-rate parity (embedded inline)

Outputs are also written to `outputs/tables/*.csv` and `outputs/figures/fig_equity_reallocation.png`.
A **detailed per-cell walkthrough** (purpose, key functions, inputs, outputs) is in **`CODE_SUMMARY.md`**.

---

## 5. Results

### 5.1 Validation gate - we reproduce CMS's actual penalty
MAE **0.00016**, r **0.99**, **92%** within ±0.0005; recovers the **78.2%** penalty rate; peer
groups confirmed as dual-proportion quintiles (5 × n=589, dual proportion rising monotonically).

### 5.2 PRIMARY - official recompute under SVI peer grouping, **dollar-neutral** (FY2026, n=2,832)
- Penalty status changed for **12.7%** of hospitals; total penalty **dollars** held constant (k=0.997).
- **SVI is NOT independently associated** with ERR after adjusting for dual proportion (β=0.007, p=0.25; dual β=0.071, p<0.001), county-clustered - its outcome signal overlaps dual. Trend slope **−0.090** (p<0.001). The paper is **re-centered on the reallocation**, with SVI as a transparent redistribution lever, not a better predictor.
- Per-hospital change in payment reduction (pp of base operating DRG payments):

| SVI quintile (5 = most vulnerable) | n | Mean Δ (pp) | 95% CI |
|---|---|---|---|
| 1 | 569 | +0.034 | +0.013, +0.053 |
| 2 | 567 | +0.020 | +0.004, +0.036 |
| 3 | 563 | +0.020 | +0.001, +0.037 |
| 4 | 566 | −0.014 | −0.036, +0.004 |
| 5 | 567 | **−0.041** | −0.060, −0.023 |

→ Four of five CIs exclude 0 (Q4 borderline); penalty burden shifts **off** the most-vulnerable hospitals **onto** the least-vulnerable.
By ownership (mean Δ): For-profit −0.005, Government −0.001, Nonprofit +0.008.
By region: South −0.019, West +0.009, Midwest +0.021, Northeast +0.033.

### 5.3 ROBUSTNESS - simplified operationalization (FY2026 flag, n=2,825)
Replacing the official formula with a simpler facility-level median flag reproduces the pattern:
non-stratified flag rate 43.5%→63.7% across SVI quintiles (Q5/Q1 = **1.46**), SVI-stratified ≈ 1.00.
Confirms the reallocation is not an artifact of the official formula.

### 5.4 Absolute dollars (approximate, dollar-neutral)
Dollar-neutrality is anchored to the reconstructed-formula penalty total **~$368.4M** (matched cohort; within ~1% of the published-PAF total **~$364.9M**).
Under **dollar-neutral** SVI grouping **$14.1M (3.8% of the reconstructed total) is reallocated**, exactly offset (columns sum to ~0):
most-vulnerable quintiles gain relief (Q4 −$4.1M, Q5 −$7.0M), least-vulnerable absorb more
(Q1 +$4.7M, Q2 +$3.1M, Q3 +$3.3M). Per-hospital base proxied by total Medicare inpatient payments (`data.cms.gov`).

### 5.5 Sensitivity (index & cut-points)
Direction holds in **every** specification - tertiles, quintiles, deciles, and all four SVI sub-themes
(socioeconomic, household/disability, minority/language, housing/transport): most-vulnerable relief,
least-vulnerable increase. Strongest for socioeconomic/household/minority themes, weakest for
housing/transport. **Cross-index check:** the **Area Deprivation Index (ADI 2023)** - only ~7% shared rank
variance with SVI (ρ=0.27) - reproduces the same direction (most-deprived −0.021 pp, least-deprived +0.008 pp),
so the reallocation is **not specific to SVI** (`outputs/tables/sensitivity_index_cutpoints.csv`).

---

## 6. Limitations
- **Dollar-neutral is the primary spec** (total penalty *dollars* held constant; $ columns sum to ~0).
  The *count* penalized still rises (more hospitals incur a *smaller* penalty); the reallocation is the result.
- **Relative** payment-reduction (pp), not absolute **$** - now reported as approximate dollars via total Medicare inpatient payments (a proxy for the base operating DRG base).
- **SVI not independently predictive** (p=0.25 after dual adjustment) - paper re-centered on the *reallocation*; SVI is a transparent redistribution lever, not a better predictor.
- **Ecological** assignment (county SVI ≠ patient mix); triangulate with patient-level social risk.
- Name-based county join (~97%); CAHs are statutorily HRRP-exempt (cohort = acute-care subsection-(d)).

---

## 7. Manuscript (`manuscript/`)
**Submission-ready paper:** `Stratifying Hospital Readmission Penalties by Community Social Vulnerability.docx` (and matching `.pdf`) - full Word
manuscript with abstract, Background, Methods, Results (real numbers), Discussion, Limitations,
Conclusion, declarations, references, Tables 1–3, and Figure 1. Authors: Rajat Goel, Jess Schwartz,
Aashis Luitel, Joseph Tronco (University of the Cumberlands).
Working drafts: `paper1_methods.md`, `paper1_outline.md`, `references.md`. (The superseded FY2021 `paper1_results_preliminary.md` has been moved to `Archive/`.)

*Status: pipeline runs end-to-end on real public data; primary finding validated against CMS's own penalties.*
