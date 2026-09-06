# SVI nested-regression results (correction to §4c)

Reproduce with `python analysis/svi_nested_regressions.py` (reads
`data/processed/official_counterfactual.csv`). County-clustered (CR) standard errors throughout.

## Why this exists

The first draft reported only the **fully adjusted** model and concluded that SVI adds "no independent
predictive information" beyond the dual-eligible share. A single fully-adjusted model can't support
that. The nested sequence below — adding one characteristic at a time — shows exactly which variable
moves the SVI coefficient.

## Sample

The primary sequence uses covariates that are **complete for every hospital** (SVI, dual, ownership,
census region), so **all n = 2,832 hospitals are retained** — none are dropped. Hospital *size* is the
only covariate with missing values (a discharge-based measure is missing/zero for 473 hospitals), so
size enters **only as a robustness check**, measured two ways (log Medicare payments, complete; log
discharges, n = 2,359). Neither changes the conclusion. This keeps the sequence nested on a fixed
sample without discarding ~17% of hospitals to force a common size variable.

## Results (FY2026, n = 2,832, county-clustered)

| Model | SVI β [95% CI] | p | R² |
|---|---|---|---|
| 1. ERR ~ SVI | +0.024 [0.015, 0.032] | <0.001 | 0.014 |
| ERR ~ dual (ref.) | — | — | 0.028 |
| 2. ERR ~ SVI + dual | **+0.015 [0.006, 0.024]** | **<0.001** | 0.033 |
| 3. + ownership | +0.014 [0.005, 0.022] | 0.003 | 0.035 |
| 4. + region (**full**) | +0.007 [−0.004, 0.019] | 0.23 | 0.054 |

- **Robustness (+ size):** log Medicare payments (n=2,832) → SVI β=0.006, p=0.30; log discharges
  (n=2,359) → SVI β=0.009, p=0.17. Conclusion invariant.
- **SVI vs dual:** Spearman ρ = 0.305 (~9% shared rank variance) — modest, **not** redundant.
- **Incremental R² of SVI over dual alone = 0.005.** dual in full model: β=0.069, p<0.001.
- **VIFs** all < 2.2.

## Interpretation

- Adding **dual** attenuates SVI (0.024 → 0.015) but it stays clearly significant (p < 0.001): SVI and
  dual are only modestly correlated and are **not** redundant (so "adjust for one, drop the other" does
  not follow).
- SVI remains significant after adding **ownership** (and after adding **size** either way).
- SVI becomes non-significant **only when census region enters** (model 4), which also produces the
  single largest jump in R² (0.035 → 0.054). **Region — not the dual share — is the attenuating
  variable.**
- VIFs < 2.2, so the attenuation is not a variance-inflation artifact. Whether region is a legitimate
  control or an over-adjustment — region is a coarser measure of the same place-based variation SVI is
  constructed to capture — is an **open specification question**; the fully adjusted model is reported
  as a **sensitivity**, not the primary characterization.

SVI carries a small but statistically significant independent association with readmissions beyond the
incumbent dual measure. The paper does not claim SVI is a materially better predictor; its value is as
a transparent redistribution lever, and the headline budget-neutral reallocation (~$14.1M, 3.8%) does
not depend on this regression.

_Correction prompted by independent methodological feedback from two external readers (nested models;
add one variable at a time; keep the full cohort). Analysis and headline reallocation results are
unchanged._
