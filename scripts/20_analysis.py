"""Test the theory: does health track economics at the low end, then turn to scatter?
Outputs analysis/results.json, analysis/binned.csv, analysis/by_state.csv, analysis/corr_matrix.csv,
analysis/county.csv. All numbers in findings come from these files."""
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
        sse = ((y - X @ coef) ** 2).sum()
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


def main():
    OUT.mkdir(exist_ok=True)
    df = pd.read_parquet(PROC / "tracts.parquet")
    x, y = df.econ_index.to_numpy(), df.health_index.to_numpy()
    res = {"national": describe(x, y)}
    b = binned(df, "econ_index", "health_index")
    b["iqr"] = b.y_p75 - b.y_p25
    b["p10_p90"] = b.y_p90 - b.y_p10
    b.to_csv(OUT / "binned.csv")

    # how much of the health index varies between counties vs within them
    cm = df.groupby("countyfips").health_index.transform("mean")
    res["health_var_share_between_counties"] = float(cm.var() / df.health_index.var())
    em = df.groupby("countyfips").econ_index.transform("mean")
    res["econ_var_share_between_counties"] = float(em.var() / df.econ_index.var())
    # within-county relationship: demean both by county
    res["spearman_within_county"] = float(stats.spearmanr(df.econ_index - em, df.health_index - cm)[0])

    rows = []
    for st, g in df.groupby("stateabbr"):
        if len(g) < 200:
            d = {"n": len(g), "spearman_all": float(stats.spearmanr(g.econ_index, g.health_index)[0])}
        else:
            d = describe(g.econ_index.to_numpy(), g.health_index.to_numpy(), boot=0)
        rows.append({"state": st, **d})
    pd.DataFrame(rows).to_csv(OUT / "by_state.csv", index=False)

    econ = ["med_hh_income", "pct_above_200fpl", "prime_lfpr", "prime_epop", "unemp_rate", "lf_change",
            "pct_cost_burdened", "med_rent_pct_income", "pct_snap", "pct_medicaid", "pct_uninsured", "pct_public_assist",
            "gini", "per_capita_income", "econ_index"]
    health = ["obesity", "smoking", "depression", "mental_distress", "physical_distress", "fair_poor_health",
              "binge_drinking", "inactivity", "short_sleep", "diabetes", "high_bp", "copd", "chd", "disability",
              "food_insecurity", "loneliness", "no_emotional_support", "health_index"]
    df[econ + health].corr(method="spearman").loc[econ, health].round(3).to_csv(OUT / "corr_matrix.csv")

    # county check against counted deaths (County Health Rankings supplement, March 2026)
    chr_ = pd.read_csv(RAW / "chr" / "analytic_supplement_20260325.csv", dtype={"fipscode": str}, low_memory=False)
    chr_ = chr_[chr_.countycode != "000"].set_index("fipscode")
    c = df.groupby("countyfips").apply(lambda g: pd.Series({
        "econ_index": np.average(g.econ_index, weights=g["pop"]),
        "health_index": np.average(g.health_index, weights=g["pop"]),
        "pop": g["pop"].sum(), "tracts": len(g), "state": g.stateabbr.iloc[0]}))
    c["overdose_rate"] = pd.to_numeric(chr_.v138_rawvalue, errors="coerce").reindex(c.index)
    c["suicide_rate"] = pd.to_numeric(chr_.v161_rawvalue, errors="coerce").reindex(c.index)
    c["life_expectancy"] = pd.to_numeric(chr_.v147_rawvalue, errors="coerce").reindex(c.index)
    c.to_csv(OUT / "county.csv")
    res["county"] = {"counties": int(len(c)),
                     "matched_to_chr": int(c.index.isin(chr_.index).sum())}
    for m in ["overdose_rate", "suicide_rate", "life_expectancy", "health_index"]:
        s = c.dropna(subset=[m])
        res["county"][m] = describe(s.econ_index.to_numpy(), s[m].to_numpy(), boot=200) if len(s) > 200 else None
        res["county"][m + "_n_missing"] = int(c[m].isna().sum())

    (OUT / "results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
