# SVI nested-regression results (correction to §4c)

Reproduce with `python analysis/svi_nested_regressions.py` (reads
`data/processed/official_counterfactual.csv`). County-clustered (CR) standard errors throughout.
**All models run on one fixed complete-case sample (n = 2,359)** so the sequence is genuinely nested —
adding a variable, not also changing the rows.

## Why this exists

The first draft reported only the **fully adjusted** model and concluded that SVI adds "no independent
predictive information" beyond the dual-eligible share. A single fully-adjusted model can't support
that. The nested sequence below — adding one characteristic at a time on a fixed sample — shows exactly
which variable moves the SVI coefficient.

## Results (FY2026, n = 2,359, county-clustered)

| Model | SVI β [95% CI] | p | R² |
|---|---|---|---|
| 1. ERR ~ SVI | +0.026 [0.017, 0.035] | <0.001 | 0.017 |
| ERR ~ dual (ref.) | — | — | 0.030 |
| 2. ERR ~ SVI + dual | **+0.017 [0.008, 0.027]** | **<0.001** | 0.036 |
| 3. + ownership | +0.015 [0.005, 0.024] | 0.003 | 0.040 |
| 4. + size | +0.014 [0.004, 0.023] | 0.005 | 0.042 |
| 5. + region (**full**) | +0.009 [−0.004, 0.021] | 0.17 | 0.063 |

- **SVI vs dual:** Spearman ρ = 0.315 (~10% shared rank variance) — modest, **not** redundant.
- **Incremental R² of SVI over dual alone = 0.0066.**
- **VIFs** (full model) all < 2.1 (highest region_South = 2.08).
- dual in the full model: β = 0.078, p < 0.001.

## Interpretation

- Adding **dual** attenuates SVI (0.026 → 0.017) but it stays clearly significant (p < 0.001): SVI and
  dual are only modestly correlated and are **not** redundant (so "adjust for one, drop the other"
  does not follow).
- SVI remains significant after adding **ownership** and **size**.
- SVI becomes non-significant **only when census REGION enters** (model 5), which also produces the
  single largest jump in R² (0.042 → 0.063). **Region — not the dual share — is the attenuating
  variable.**
- VIFs < 2.1, so the attenuation is not a variance-inflation artifact. Whether region is a legitimate
  control or an over-adjustment — region is a coarser measure of the same place-based variation SVI is
  constructed to capture — is an **open specification question**; the fully adjusted model is reported
  as a **sensitivity**, not the primary characterization.

SVI carries a small but statistically significant independent association with readmissions beyond the
incumbent dual measure (models 2–4). The paper does not claim SVI is a materially better predictor; its
value is as a transparent redistribution lever, and the headline budget-neutral reallocation
(~$14.1M, 3.8%) does not depend on this regression.

_Correction prompted by independent methodological feedback from two external readers (nested,
fixed-sample models; add one variable at a time). Analysis and headline reallocation results are
unchanged._
