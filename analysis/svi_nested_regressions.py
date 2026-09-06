"""
Nested county-clustered regressions of the excess-readmission ratio (ERR) on the community
Social Vulnerability Index (SVI) and the incumbent dual-eligible proportion.

Purpose
-------
The manuscript's §4c originally reported only the *fully adjusted* model
(ERR ~ SVI + dual + ownership + region + size), in which SVI is not significant (beta=0.007,
p=0.25), and framed SVI as adding "no independent predictive information" beyond the dual share.
That single model is over-adjusted: it conditions on hospital characteristics (ownership, region,
size) that plausibly lie on the pathway between community vulnerability and measured readmissions,
which absorbs SVI's association. This script reports the full nested sequence so the reader can see
what is actually going on.

Result (FY2026, county-clustered SEs)
-------------------------------------
  1. ERR ~ SVI            SVI beta = +0.024  p < 0.001        (n = 2,832)
  2. ERR ~ dual           dual beta = +0.059  p < 0.001       (n = 2,832)
  3. ERR ~ SVI + dual     SVI beta = +0.015  p < 0.001        (n = 2,832)  <-- SVI adds signal beyond dual
                          dual beta = +0.051  p < 0.001
  4. + ownership+region+size  SVI beta = +0.007  p = 0.25     (n = 2,359*) <-- attenuates only here
  VIFs all < 2.1  ->  no collinearity; the attenuation is shared variance with (plausibly mediating)
  hospital characteristics, not instability.

  * The full model drops hospitals lacking a discharge count for log(size).

Takeaway: SVI carries a small but statistically significant independent association with readmissions
beyond the incumbent dual measure (model 3, p<0.001; incremental R^2 ~ 0.005). It attenuates to
non-significance only after adjusting for ownership, region, and size. The paper therefore does not
claim SVI is a materially better predictor; its value is as a transparent redistribution lever.

Run
---
  python analysis/svi_nested_regressions.py
Requires: pandas, numpy, statsmodels. Reads data/processed/official_counterfactual.csv
(produced by the main notebook, §4).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import pearsonr, spearmanr

CF = Path(__file__).resolve().parents[1] / "data" / "processed" / "official_counterfactual.csv"


def fit(formula, d):
    return smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["cluster"]})


def line(name, m, var, lab):
    print(f"   {name:<26}{lab:<6} beta={m.params[var]:+.4f}  SE={m.bse[var]:.4f}  "
          f"p={m.pvalues[var]:.3g}  R2={m.rsquared:.3f}")


def main():
    df = pd.read_csv(CF).copy()
    df["logsize"] = np.log(df["total_discharges"].replace(0, np.nan))

    dA = df.dropna(subset=["mean_err", "svi_overall", "dual_proportion", "cluster"])
    print(f"Models 1-3 on full sample n={len(dA)} (county clusters {dA['cluster'].nunique()}), "
          f"cluster-robust SEs:")
    line("1. ERR ~ SVI",        fit("mean_err ~ svi_overall", dA), "svi_overall", "SVI")
    line("2. ERR ~ dual",       fit("mean_err ~ dual_proportion", dA), "dual_proportion", "dual")
    m3 = fit("mean_err ~ svi_overall + dual_proportion", dA)
    line("3. ERR ~ SVI + dual", m3, "svi_overall", "SVI")
    line("3. ERR ~ SVI + dual", m3, "dual_proportion", "dual")

    dB = df.dropna(subset=["mean_err", "svi_overall", "dual_proportion",
                           "ownership_cat", "region", "logsize", "cluster"])
    m4 = fit("mean_err ~ svi_overall + dual_proportion + C(ownership_cat) + C(region) + logsize", dB)
    print(f"\n4. FULL model (+ ownership + region + size) n={len(dB)}:")
    line("4. full", m4, "svi_overall", "SVI")
    line("4. full", m4, "dual_proportion", "dual")

    pr = pearsonr(dA["svi_overall"], dA["dual_proportion"])
    sr = spearmanr(dA["svi_overall"], dA["dual_proportion"])
    print(f"\nSVI vs dual: Pearson r={pr[0]:.3f}; Spearman rho={sr[0]:.3f} "
          f"(shared rank variance {100*sr[0]**2:.1f}%)")

    X = pd.get_dummies(dB[["svi_overall", "dual_proportion", "ownership_cat", "region", "logsize"]],
                       drop_first=True).astype(float)
    Xc = sm.add_constant(X)
    print("\nVIF (full-model predictors):")
    for i, c in enumerate(Xc.columns):
        if c == "const":
            continue
        print(f"   {c:<28}{variance_inflation_factor(Xc.values, i):>6.2f}")


if __name__ == "__main__":
    main()
