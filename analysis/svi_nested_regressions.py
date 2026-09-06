"""
Nested county-clustered regressions of the excess-readmission ratio (ERR) on the community
Social Vulnerability Index (SVI) and the incumbent dual-eligible proportion.

Purpose
-------
The manuscript's first draft reported only the *fully adjusted* model
(ERR ~ SVI + dual + ownership + size + region), in which SVI is not significant (beta=0.009,
p=0.17), and framed SVI as adding "no independent predictive information" beyond the dual share.
A single fully-adjusted model cannot support that claim. This script reports the full nested
sequence, adding one characteristic at a time on a SINGLE fixed sample, so the reader can see
exactly which variable moves the SVI coefficient.

All models run on the SAME complete-case sample (hospitals with SVI, dual, ownership, region, and a
discharge count for log-size), n = 2,359. Running the sub-models on the full n = 2,832 and the fully
adjusted model on a smaller set would confound "adjustment" with "dropping 17% of hospitals," so the
sequence is deliberately kept nested.

Result (FY2026, county-clustered SEs, n = 2,359)
------------------------------------------------
  1. ERR ~ SVI                       SVI beta = +0.026  p < 0.001         R2 = 0.017
     ERR ~ dual                      dual beta = +0.064  p < 0.001        R2 = 0.030
  2. ERR ~ SVI + dual                SVI beta = +0.017  p < 0.001         R2 = 0.036   <- SVI survives dual
  3.        + ownership              SVI beta = +0.015  p = 0.003         R2 = 0.040   <- survives
  4.        + size (log discharges)  SVI beta = +0.014  p = 0.005         R2 = 0.042   <- survives
  5.        + region  (FULL model)   SVI beta = +0.009  p = 0.17          R2 = 0.063   <- dies here
  SVI-dual correlation: Spearman rho = 0.315 (~10% shared rank variance) -- modest, NOT redundant.
  Incremental R2 of SVI over dual alone = 0.0066.
  VIFs all < 2.1 (highest region_South = 2.08).

Interpretation
--------------
- Adding the dual share attenuates SVI (0.026 -> 0.017) but leaves it clearly significant
  (p < 0.001): SVI and dual are only modestly correlated and are NOT redundant.
- SVI remains significant after adding ownership and size.
- SVI becomes non-significant ONLY when census REGION enters, which also produces the largest single
  jump in R^2 (0.042 -> 0.063). Region is the attenuating variable, not the dual share.
- VIFs < 2.1, so the attenuation is not a variance-inflation artifact. Whether region is a legitimate
  control or an over-adjustment -- region is a coarser measure of the same place-based variation SVI
  is constructed to capture -- is an open specification question. The fully adjusted model is reported
  as a sensitivity, not as the primary characterization.

Bottom line: SVI carries a small but statistically significant independent association with
readmissions beyond the incumbent dual measure (models 2-4). The paper does not claim SVI is a
materially better predictor; its value is as a transparent redistribution lever, and the headline
budget-neutral reallocation (~$14.1M, 3.8%) does not depend on this regression.

Run
---
  python analysis/svi_nested_regressions.py
Requires: pandas, numpy, statsmodels, scipy. Reads data/processed/official_counterfactual.csv
(produced by the main notebook, §4).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import spearmanr, pearsonr

CF = Path(__file__).resolve().parents[1] / "data" / "processed" / "official_counterfactual.csv"
COVARS = ["mean_err", "svi_overall", "dual_proportion", "ownership_cat", "region", "logsize", "cluster"]


def main():
    df = pd.read_csv(CF).copy()
    df["logsize"] = np.log(df["total_discharges"].replace(0, np.nan))
    # ONE fixed complete-case sample for every model (keeps the sequence genuinely nested)
    d = df.dropna(subset=COVARS)

    def fit(formula):
        return smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["cluster"]})

    def row(tag, m):
        if "svi_overall" in m.params.index:
            b, p = m.params["svi_overall"], m.pvalues["svi_overall"]
            lo, hi = m.conf_int().loc["svi_overall"]
            print(f"  {tag:<28} SVI beta={b:+.4f} [{lo:+.4f}, {hi:+.4f}]  p={p:.3g}   R2={m.rsquared:.4f}")
        else:
            print(f"  {tag:<28} (dual only)                              R2={m.rsquared:.4f}")
        return m

    print(f"Nested models on ONE fixed complete-case sample n={len(d)} "
          f"(county clusters {d['cluster'].nunique()}), cluster-robust SEs:\n")
    m1 = row("1. ERR ~ SVI",                 fit("mean_err ~ svi_overall"))
    md = row("   ERR ~ dual",                fit("mean_err ~ dual_proportion"))
    m2 = row("2. ERR ~ SVI + dual",          fit("mean_err ~ svi_overall + dual_proportion"))
    m3 = row("3.   + ownership",             fit("mean_err ~ svi_overall + dual_proportion + C(ownership_cat)"))
    m4 = row("4.   + size",                  fit("mean_err ~ svi_overall + dual_proportion + C(ownership_cat) + logsize"))
    m5 = row("5.   + region (FULL)",         fit("mean_err ~ svi_overall + dual_proportion + C(ownership_cat) + logsize + C(region)"))

    print(f"\n  dual (full model): beta={m5.params['dual_proportion']:+.4f}  p={m5.pvalues['dual_proportion']:.3g}")
    print(f"  incremental R2 of SVI over dual = R2(SVI+dual) - R2(dual) = "
          f"{m2.rsquared:.4f} - {md.rsquared:.4f} = {m2.rsquared - md.rsquared:.4f}")
    print(f"  R2 jump when region is added = {m4.rsquared:.4f} -> {m5.rsquared:.4f} "
          f"(delta {m5.rsquared - m4.rsquared:.4f}); the single largest increment.")
    print(f"  SVI vs dual: Pearson r={pearsonr(d['svi_overall'], d['dual_proportion'])[0]:.3f}, "
          f"Spearman rho={spearmanr(d['svi_overall'], d['dual_proportion'])[0]:.3f} "
          f"(~{100*spearmanr(d['svi_overall'], d['dual_proportion'])[0]**2:.0f}% shared rank variance)")

    X = pd.get_dummies(d[["svi_overall", "dual_proportion", "ownership_cat", "region", "logsize"]],
                       drop_first=True).astype(float)
    Xc = sm.add_constant(X)
    print("\n  VIF (full-model predictors):")
    for i, c in enumerate(Xc.columns):
        if c != "const":
            print(f"    {c:<26}{variance_inflation_factor(Xc.values, i):>6.2f}")


if __name__ == "__main__":
    main()
