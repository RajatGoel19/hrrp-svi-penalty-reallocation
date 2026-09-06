# SVI nested-regression results (correction to §4c)

Reproduce with `python analysis/svi_nested_regressions.py` (reads
`data/processed/official_counterfactual.csv`). County-clustered (CR) standard errors throughout.

## Why this exists

The manuscript originally reported only the **fully adjusted** model and concluded that SVI adds
"no independent predictive information" about readmissions beyond the dual-eligible share (β=0.007,
p=0.25). That single model is **over-adjusted**: ownership, region, and size plausibly sit on the
pathway between community vulnerability and measured readmissions, so conditioning on them absorbs
SVI's association. The nested sequence below shows what the data actually say.

## Results (FY2026)

| Model | n | SVI β (p) | dual β (p) | R² |
|---|---|---|---|---|
| 1. ERR ~ SVI | 2,832 | **+0.024 (p<0.001)** | — | 0.014 |
| 2. ERR ~ dual | 2,832 | — | +0.059 (p<0.001) | 0.028 |
| 3. ERR ~ SVI + dual | 2,832 | **+0.015 (p<0.001)** | +0.051 (p<0.001) | 0.033 |
| 4. + ownership + region + size | 2,359\* | +0.009 (p=0.17) | +0.078 (p<0.001) | 0.063 |

\* The full model drops 473 hospitals that lack a discharge count for `log(size)`. The manuscript's
reported full-model figure (β=0.007, p=0.25, n=2,832) uses the same covariates on the full cohort; the
direction and conclusion are identical.

- **SVI vs dual:** Spearman ρ = 0.305 (≈9.3% shared rank variance) — the two measures are far from
  identical.
- **VIFs** (full model): all < 2.1 (SVI 1.48, dual 1.52, region_South 2.08) → **no collinearity**; the
  attenuation of SVI from model 3 to model 4 is shared variance with those (plausibly mediating)
  hospital characteristics, not variance-inflation instability.

## Interpretation

SVI carries a **small but statistically significant independent association** with readmissions beyond
the incumbent dual measure (model 3, p<0.001; incremental R² ≈ 0.005). It attenuates to
non-significance **only** after further adjusting for ownership, region, and size. We therefore do not
claim SVI is a materially stronger predictor than the dual-eligible share — its independent outcome
signal is modest and specification-dependent — but neither is it inert. The paper's contribution is the
**budget-neutral reallocation** (≈$14.1M, 3.8%), which is independent of SVI's predictive value.

_Correction prompted by a methodological point from an external reader (three nested models vs. a
single over-adjusted model); analysis and headline reallocation results are unchanged._
