"""Test the theory: does health track economics at the low end, then turn to scatter?
Headline economic measure: median household income. The economic index is kept as a second view.
Outputs analysis/results.json, analysis/binned.csv (by income), analysis/by_state.csv, analysis/corr_matrix.csv,
analysis/county_results.json. All numbers in findings come from these files."""
import os, sys, json
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, PROC, ROOT

OUT = ROOT / "analysis"
rng = np.random.default_rng(20261114)


def hinge_fit(x, y, grid):
    """Continuous two-segment line: y = a + b*x + c*max(0, x-k). Returns best k and fit."""
    best = None
    X0 = np.column_stack([np.ones_like(x), x])
    for k in grid:
        X = np.column_stack([X0, np.maximum(0, x - k)])
        coef, res, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = ((y - (X * coef).sum(axis=1)) ** 2).sum()  # no BLAS matmul: numpy 2.0 on macOS raises false FP warnings
        if best is None or sse < best[1]:
            best = (k, sse, coef)
    k, sse, (a, b, c) = best
    return {"k": float(k), "sse": float(sse), "intercept": float(a), "slope_below": float(b), "slope_above": float(b + c)}


def describe(x, y, boot=200):
    lo, hi = np.percentile(x, [5, 95])
    grid = np.linspace(lo, hi, 91)
    f = hinge_fit(x, y, grid)
    lin = np.polyfit(x, y, 1)
    sse_lin = ((y - np.polyval(lin, x)) ** 2).sum()
    f["r2_line"] = float(1 - sse_lin / ((y - y.mean()) ** 2).sum())
    f["r2_hinge"] = float(1 - f["sse"] / ((y - y.mean()) ** 2).sum())
    if (x > 0).all():
        ll = np.polyfit(np.log(x), y, 1)
        f["r2_log_line"] = float(1 - ((y - np.polyval(ll, np.log(x))) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    pred = f["intercept"] + f["slope_below"] * x + (f["slope_above"] - f["slope_below"]) * np.maximum(0, x - f["k"])
    res = y - pred
    b, a = x < f["k"], x >= f["k"]
    f.update({
        "n": int(len(x)), "n_below": int(b.sum()), "n_above": int(a.sum()),
        "spearman_all": float(stats.spearmanr(x, y)[0]),
        "spearman_below": float(stats.spearmanr(x[b], y[b])[0]) if b.sum() > 30 else None,
        "spearman_above": float(stats.spearmanr(x[a], y[a])[0]) if a.sum() > 30 else None,
        "resid_iqr_below": float(np.subtract(*np.percentile(res[b], [75, 25]))) if b.sum() > 30 else None,
        "resid_iqr_above": float(np.subtract(*np.percentile(res[a], [75, 25]))) if a.sum() > 30 else None,
    })
    if boot:
        ks = []
        for _ in range(boot):
            i = rng.integers(0, len(x), len(x))
            ks.append(hinge_fit(x[i], y[i], grid)["k"])
        f["k_ci95"] = [float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5))]
    return f


def binned(df, xcol, ycol, nbins=50):
    q = pd.qcut(df[xcol], nbins, labels=False, duplicates="drop")
    g = df.groupby(q)
    return pd.DataFrame({
        "x_mid": g[xcol].median(), "n": g.size(),
        "y_p10": g[ycol].quantile(0.10), "y_p25": g[ycol].quantile(0.25), "y_med": g[ycol].median(),
        "y_p75": g[ycol].quantile(0.75), "y_p90": g[ycol].quantile(0.90)})


XH = "med_hh_income"  # headline economic measure


def main():
    OUT.mkdir(exist_ok=True)
    df = pd.read_parquet(PROC / "tracts.parquet")
    h = df[df[XH].notna()]
    res = {"headline_x": XH, "tracts_with_income": int(len(h)),
           "national": describe(h[XH].to_numpy(), h.health_index.to_numpy()),
           "national_index": describe(df.econ_index.to_numpy(), df.health_index.to_numpy())}
    b = binned(h, XH, "health_index")
    b["iqr"] = b.y_p75 - b.y_p25
    b["p10_p90"] = b.y_p90 - b.y_p10
    b.to_csv(OUT / "binned.csv")

    cm = h.groupby("countyfips").health_index.transform("mean")
    xm = h.groupby("countyfips")[XH].transform("mean")
    res["health_var_share_between_counties"] = float(cm.var() / h.health_index.var())
    res["spearman_within_county"] = float(stats.spearmanr(h[XH] - xm, h.health_index - cm)[0])
    em = df.groupby("countyfips").econ_index.transform("mean")
    res["spearman_within_county_index"] = float(stats.spearmanr(df.econ_index - em, df.health_index - df.groupby("countyfips").health_index.transform("mean"))[0])

    rows = []
    for st, g in h.groupby("stateabbr"):
        if len(g) < 200:
            d = {"n": len(g), "spearman_all": float(stats.spearmanr(g[XH], g.health_index)[0])}
        else:
            d = describe(g[XH].to_numpy(), g.health_index.to_numpy(), boot=0)
        rows.append({"state": st, **d})
    pd.DataFrame(rows).to_csv(OUT / "by_state.csv", index=False)

    econ = ["med_hh_income", "pct_above_200fpl", "prime_lfpr", "prime_epop", "unemp_rate", "lf_change",
            "pct_cost_burdened", "med_rent_pct_income", "pct_snap", "pct_medicaid", "pct_uninsured", "pct_public_assist",
            "gini", "per_capita_income", "econ_index"]
    health = ["obesity", "smoking", "depression", "mental_distress", "physical_distress", "fair_poor_health",
              "binge_drinking", "inactivity", "short_sleep", "diabetes", "high_bp", "copd", "chd", "disability",
              "food_insecurity", "loneliness", "no_emotional_support", "health_index"]
    df[econ + health].corr(method="spearman").loc[econ, health].round(3).to_csv(OUT / "corr_matrix.csv")

    # counties: ACS county income vs PLACES county health index and counted deaths (County Health Rankings)
    c = pd.read_parquet(PROC / "counties.parquet")
    cr = {"counties": int(len(c))}
    for m in ["health_index", "life_expectancy", "overdose_rate", "suicide_rate"]:
        for xk in [XH, "econ_index"]:
            s = c.dropna(subset=[m, xk])
            cr[f"{m}__{xk}"] = describe(s[xk].to_numpy(), s[m].to_numpy(), boot=200)
        cr[m + "_n_missing"] = int(c[m].isna().sum())
    (OUT / "county_results.json").write_text(json.dumps(cr, indent=2))
    (OUT / "results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items()}, indent=1))
    print(json.dumps({k: {kk: v[kk] for kk in ["n", "spearman_all", "r2_line", "r2_log_line", "r2_hinge", "k"] if kk in v} if isinstance(v, dict) else v for k, v in cr.items()}, indent=1))


if __name__ == "__main__":
    main()
