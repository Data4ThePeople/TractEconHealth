"""Claude's tie-out. Rebuilds every measure from the raw downloads with its own code (no imports from the build
scripts), recomputes every published number, and compares with data/processed and analysis/*.
Writes analysis/tieout.json. TIEOUT.md lists each number and label with its result."""
import base64, glob, json, re
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIPS = ("01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 "
        "38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56").split()
OUT = {}


def rd(folder, table):
    """Raw ACS table, estimates numeric, Census annotation sentinels (large negatives) -> NaN."""
    f = folder / f"{table}.parquet"
    d = pd.read_parquet(f).set_index("geoid")
    cols = [c for c in d.columns if c.startswith(table) and c.endswith("E")]
    e = d[cols].apply(pd.to_numeric, errors="coerce")
    return e.mask(e <= -100000000)


def labels(folder, table):
    l = pd.read_csv(folder / f"{table}_labels.csv")
    l = l[l["var"].str.match(rf"^{table}_\d+E$")]
    return dict(zip(l["var"], l["label"]))


def cols_where(folder, table, fn):
    return sorted(v for v, lab in labels(folder, table).items() if fn(lab.split("!!")))


def acs_measures(folder):
    t = {}
    pop = rd(folder, "B01003").B01003_001E
    gq = rd(folder, "B26001").B26001_001E
    t["pop"], t["gq_pop"] = pop, gq
    t["med_hh_income"] = rd(folder, "B19013").B19013_001E
    c = rd(folder, "C17002"); t["pct_above_200fpl"] = c.C17002_008E / c.C17002_001E * 100
    b = rd(folder, "B23001")
    ages = ("25 to 29 years:", "30 to 34 years:", "35 to 44 years:", "45 to 54 years:")
    base = cols_where(folder, "B23001", lambda p: len(p) == 4 and p[3] in ages)
    inlf = cols_where(folder, "B23001", lambda p: len(p) == 5 and p[3] in ages and p[4] == "In labor force:")
    emp = cols_where(folder, "B23001", lambda p: p[3:4] and p[3] in ages and
                     (p[-1] == "Employed" or p[-1] == "In Armed Forces"))
    assert len(base) == 8 and len(inlf) == 8 and len(emp) == 16, (len(base), len(inlf), len(emp))
    den = b[base].sum(axis=1)
    t["prime_lfpr"] = b[inlf].sum(axis=1) / den * 100
    t["prime_epop"] = b[emp].sum(axis=1) / den * 100
    t["prime_pop"] = den
    e = rd(folder, "B23025")
    t["unemp_rate"] = e.B23025_005E / e.B23025_003E * 100
    t["lf_2024"] = e.B23025_002E
    h = rd(folder, "B25140")
    over = h[["B25140_003E", "B25140_007E", "B25140_011E"]].sum(axis=1)
    occ = h.B25140_001E - h[["B25140_005E", "B25140_009E", "B25140_013E"]].sum(axis=1)
    t["pct_cost_burdened"] = over / occ * 100
    t["med_rent_pct_income"] = rd(folder, "B25071").B25071_001E
    s = rd(folder, "B22003"); t["pct_snap"] = s.B22003_002E / s.B22003_001E * 100
    m = rd(folder, "C27007")
    mv = cols_where(folder, "C27007", lambda p: p[-1].startswith("With Medicaid"))
    assert len(mv) == 6
    t["pct_medicaid"] = m[mv].sum(axis=1) / m.C27007_001E * 100
    u = rd(folder, "B27010")
    uv = cols_where(folder, "B27010", lambda p: p[-1] == "No health insurance coverage")
    assert len(uv) == 4
    t["pct_uninsured"] = u[uv].sum(axis=1) / u.B27010_001E * 100
    p = rd(folder, "B19057"); t["pct_public_assist"] = p.B19057_002E / p.B19057_001E * 100
    t["gini"] = rd(folder, "B19083").B19083_001E
    t["per_capita_income"] = rd(folder, "B19301").B19301_001E
    df = pd.DataFrame(t).replace([np.inf, -np.inf], np.nan)
    return df[df.index.str[:2].isin(FIPS)]


def pct_rank(s, higher_better):
    r = s.rank(method="average") / s.notna().sum() * 100
    return r if higher_better else 100 - r


ECON = {"med_hh_income": 1, "pct_above_200fpl": 1, "prime_lfpr": 1, "prime_epop": 1, "unemp_rate": 0,
        "lf_change": 1, "pct_cost_burdened": 0, "med_rent_pct_income": 0, "pct_snap": 0, "pct_medicaid": 0,
        "pct_uninsured": 0, "pct_public_assist": 0}
PLACES = {"OBESITY": "obesity", "DIABETES": "diabetes", "BPHIGH": "high_bp", "CHD": "chd", "COPD": "copd",
          "DISABILITY": "disability", "PHLTH": "physical_distress", "GHLTH": "fair_poor_health",
          "DEPRESSION": "depression", "MHLTH": "mental_distress", "CSMOKING": "smoking", "BINGE": "binge_drinking",
          "LPA": "inactivity", "SLEEP": "short_sleep",
          "FOODINSECU": "food_insecurity", "LONELINESS": "loneliness", "EMOTIONSPT": "no_emotional_support"}
CORE = list(PLACES.values())[:14]


def index(df, spec):
    ranks = pd.DataFrame({k: pct_rank(df[k], hb) for k, hb in spec.items()})
    have = ranks.notna().sum(axis=1)
    raw = ranks.mean(axis=1).where(have >= int(np.ceil(0.75 * len(spec))))
    return (raw - raw.min()) / (raw.max() - raw.min()) * 100


def compare(mine, theirs, cols, tol=1e-6):
    res = {}
    for c in cols:
        a, b = mine[c].reindex(theirs.index).astype(float), theirs[c].astype(float)
        both = a.notna() & b.notna()
        res[c] = {"max_abs_diff": float((a[both] - b[both]).abs().max()) if both.any() else None,
                  "blank_mismatch": int((a.isna() != b.isna()).sum())}
        res[c]["ok"] = (res[c]["max_abs_diff"] is None or res[c]["max_abs_diff"] < tol) and res[c]["blank_mismatch"] == 0
    return res


# ---------------- tract families (2010 <-> 2020) from the relationship file ----------------
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
for c in ["AREALAND_TRACT_20", "AREAWATER_TRACT_20", "AREALAND_TRACT_10", "AREAWATER_TRACT_10", "AREALAND_PART",
          "AREAWATER_PART"]:
    rel[c] = rel[c].astype(float)


def share(part_l, part_w, land, water):
    return np.where(land > 0, part_l / np.where(land > 0, land, 1), part_w / np.where(water > 0, water, 1))


s20 = share(rel.AREALAND_PART, rel.AREAWATER_PART, rel.AREALAND_TRACT_20, rel.AREAWATER_TRACT_20)
s10 = share(rel.AREALAND_PART, rel.AREAWATER_PART, rel.AREALAND_TRACT_10, rel.AREAWATER_TRACT_10)
rel = rel[rel.GEOID_TRACT_20.str[:2].isin(FIPS) & rel.GEOID_TRACT_10.notna()]  # 50 states + DC
s20 = share(rel.AREALAND_PART, rel.AREAWATER_PART, rel.AREALAND_TRACT_20, rel.AREAWATER_TRACT_20)
s10 = share(rel.AREALAND_PART, rel.AREAWATER_PART, rel.AREALAND_TRACT_10, rel.AREAWATER_TRACT_10)
# DATASETS: link on 2% of either tract's land; when either tract is all water, a 2% share of either tract's water
# also links them
lsh = lambda part, whole: np.where(whole > 0, part / np.where(whole > 0, whole, 1), 0)
by_land = (lsh(rel.AREALAND_PART, rel.AREALAND_TRACT_20) >= .02) | (lsh(rel.AREALAND_PART, rel.AREALAND_TRACT_10) >= .02)
all_water = (rel.AREALAND_TRACT_20 == 0) | (rel.AREALAND_TRACT_10 == 0)
by_water = all_water & ((lsh(rel.AREAWATER_PART, rel.AREAWATER_TRACT_20) >= .02) |
                        (lsh(rel.AREAWATER_PART, rel.AREAWATER_TRACT_10) >= .02))
links = rel[by_land | by_water]
parent = {}


def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for a in ("20_" + rel.GEOID_TRACT_20).unique():
    find(a)
for a in ("10_" + rel.GEOID_TRACT_10).unique():
    find(a)
for a, b in zip("20_" + links.GEOID_TRACT_20, "10_" + links.GEOID_TRACT_10):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
fam = pd.Series({k: find(k) for k in list(parent)})
sizes = fam.value_counts()
single = sum(1 for root, grp in fam.groupby(fam) if len(grp) == 2 and
             grp.index.str[3:].nunique() == 1)
one_one = sum(1 for root, grp in fam.groupby(fam) if (grp.index.str[:3] == "20_").sum() == 1 and
              (grp.index.str[:3] == "10_").sum() == 1)
OUT["families"] = {"families": int(len(sizes)), "one_to_one": int(one_one), "same_tract_families": int(single),
                   "largest": int(sizes.max())}

# ---------------- tracts ----------------
A24, A19 = RAW / "acs" / "2024", RAW / "acs" / "2019"
T = acs_measures(A24)
lf19 = rd(A19, "B23025").B23025_002E
f20 = fam[fam.index.str[:3] == "20_"]; f20.index = f20.index.str[3:]
f10 = fam[fam.index.str[:3] == "10_"]; f10.index = f10.index.str[3:]
lf24_fam = T.lf_2024.groupby(f20.reindex(T.index)).sum()
lf19_fam = lf19.groupby(f10.reindex(lf19.index)).sum()
chg = (lf24_fam / lf19_fam - 1) * 100
chg = chg.where(lf19_fam.reindex(chg.index) >= 100)
T["lf_change"] = f20.reindex(T.index).map(chg)

log = [("all", len(T))]
T = T[T["pop"] >= 500]; log.append(("pop 500+", len(T)))
T = T[T.gq_pop / T["pop"] < 0.5]; log.append(("gq under half", len(T)))
P = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet")
OUT["places_tract_file"] = {"tracts": int(P.locationname.nunique()), "measures": int(P.measureid.nunique()),
                            "rows_footnote_nonblank": int(P.data_value_footnote_symbol.notna().sum())}
allacs = rd(A24, "B01003").index
OUT["places_tract_file"]["match_acs"] = int(P.locationname.astype(str).str.zfill(11).drop_duplicates().isin(allacs).sum())
kp = P[P.stateabbr.isin(["KY", "PA"])]
OUT["places_tract_file"]["ky_pa_measures"] = sorted(kp.measureid.unique().tolist())
hr = P[P.measureid == "FOODINSECU"].stateabbr.unique()
OUT["places_tract_file"]["foodinsecu_states"] = int(len(hr))
OUT["places_tract_file"]["social_needs_missing"] = sorted(set(P.stateabbr.unique()) - set(hr) - {"KY", "PA"})
P = P[P.measureid.isin(PLACES)]
W = P.assign(g=P.locationname.astype(str).str.zfill(11)).pivot_table(index="g", columns="measureid",
                                                                       values="data_value").rename(columns=PLACES)
T = T.join(W, how="inner"); log.append(("has any PLACES value", len(T)))
T = T[T.obesity.notna()]; log.append(("has PLACES obesity (2023-survey measures)", len(T)))
T["econ_index"] = index(T, ECON)
T["health_index"] = index(T, {k: 0 for k in CORE})
T = T[T.econ_index.notna() & T.health_index.notna()]; log.append(("both indexes", len(T)))
OUT["tract_filter_log"] = log

TP = pd.read_parquet(ROOT / "data" / "processed" / "tracts.parquet")
OUT["tract_compare"] = compare(T, TP, ["pop", "med_hh_income", "pct_above_200fpl", "prime_lfpr", "prime_epop",
                                       "unemp_rate", "lf_change", "pct_cost_burdened", "med_rent_pct_income",
                                       "pct_snap", "pct_medicaid", "pct_uninsured", "pct_public_assist", "gini",
                                       "per_capita_income"] + list(PLACES.values()) + ["econ_index", "health_index"],
                               tol=1e-6)
OUT["tract_ids_same"] = bool(set(T.index) == set(TP.index))

# ---------------- statistics (own implementations) ----------------


def spear(x, y):
    m = x.notna() & y.notna()
    return float(np.corrcoef(x[m].rank(), y[m].rank())[0, 1])


def bend(x, y, n=901):
    x, y = np.asarray(x, float), np.asarray(y, float)
    sst = ((y - y.mean()) ** 2).sum()
    best = None
    for k in np.linspace(np.quantile(x, .05), np.quantile(x, .95), n):
        X = np.column_stack([np.ones_like(x), x, np.maximum(x - k, 0)])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((y - (X * coef).sum(axis=1)) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, k, coef)
    sse, k, coef = best
    X1 = np.column_stack([np.ones_like(x), x]); c1, *_ = np.linalg.lstsq(X1, y, rcond=None)
    r2_line = 1 - ((y - (X1 * c1).sum(axis=1)) ** 2).sum() / sst
    resid = y - (np.column_stack([np.ones_like(x), x, np.maximum(x - k, 0)]) * coef).sum(axis=1)
    iqr = lambda r: float(np.quantile(r, .75) - np.quantile(r, .25))
    out = {"k": float(k), "r2_hinge": 1 - sse / sst, "r2_line": float(r2_line), "slope_below": float(coef[1]),
           "slope_above": float(coef[1] + coef[2]), "resid_iqr_below": iqr(resid[x <= k]),
           "resid_iqr_above": iqr(resid[x > k])}
    if (x > 0).all():
        lx = np.log(x); XL = np.column_stack([np.ones_like(lx), lx]); cl, *_ = np.linalg.lstsq(XL, y, rcond=None)
        out["r2_log_line"] = float(1 - ((y - (XL * cl).sum(axis=1)) ** 2).sum() / sst)
    xs, ys = pd.Series(x), pd.Series(y)
    out["spearman_below"] = spear(xs[x <= k], ys[x <= k]); out["spearman_above"] = spear(xs[x > k], ys[x > k])
    return out


H = T[T.med_hh_income.notna()]
nat = bend(H.med_hh_income, H.health_index)
nat.update({"n": int(len(H)), "spearman": spear(H.med_hh_income, H.health_index),
            "spearman_econ_index": spear(T.econ_index, T.health_index)})
OUT["national"] = nat
cty = T.index.str[:5]
dm = lambda s: s - s.groupby(cty).transform("mean")
OUT["within_county"] = {"income": spear(dm(T.med_hh_income), dm(T.health_index)),
                        "econ_index": spear(dm(T.econ_index), dm(T.health_index))}
OUT["corr_with_health"] = {k: round(spear(T[k], T.health_index), 2) for k in
                           list(ECON) + ["per_capita_income", "gini"]}

# income groups (20 equal-count)
g = pd.qcut(H.med_hh_income, 20, labels=False)
grp = H.groupby(g)
tbl = pd.DataFrame({"income_median": grp.med_hh_income.median(), "n": grp.size(),
                    **{m: grp[m].median() for m in ["obesity", "diabetes", "smoking", "mental_distress"]},
                    "hi_p10_p90": grp.health_index.quantile(.9) - grp.health_index.quantile(.1),
                    "ob_p10_p90": grp.obesity.quantile(.9) - grp.obesity.quantile(.1)})
OUT["income_groups"] = tbl.round(2).reset_index().to_dict("records")

# states
st = []
H = H.join(TP[["stateabbr"]])
for s, gs in H.groupby("stateabbr"):
    row = {"state": s, "n": len(gs), "spearman": spear(gs.med_hh_income, gs.health_index)}
    if len(gs) >= 200:
        b = bend(gs.med_hh_income, gs.health_index, n=181)
        row.update({"ratio": b["slope_above"] / b["slope_below"], "gain": (b["r2_hinge"] - b["r2_line"]) * 100,
                    "above_pos": b["slope_above"] > 0})
    st.append(row)
st = pd.DataFrame(st)
fit = st.dropna(subset=["ratio"])
OUT["states"] = {"n_states": int(len(st)), "min": st.loc[st.spearman.idxmin(), ["state", "spearman"]].tolist(),
                 "max": st.loc[st.spearman.idxmax(), ["state", "spearman"]].tolist(), "n_fit": int(len(fit)),
                 "n_rising_above": int(fit.above_pos.sum()), "median_ratio": float(fit.ratio.median()),
                 "median_gain": float(fit.gain.median()),
                 "top_gain": fit.nlargest(3, "gain")[["state", "gain"]].round(1).values.tolist(),
                 "low_gain": fit.nsmallest(3, "gain")[["state", "gain"]].round(1).values.tolist()}
OUT["tract_pop"] = {"mean": float(T["pop"].mean()), "median": float(T["pop"].median())}

# ---------------- counties ----------------
AC = RAW / "acs_county"
C = acs_measures(AC / "2024")
lf19c = rd(AC / "2019", "B23025").B23025_002E
C["lf_change"] = (C.lf_2024 / lf19c.reindex(C.index) - 1) * 100
C["lf_change"] = C.lf_change.where(lf19c.reindex(C.index) >= 100)
clog = [("all", len(C))]
C = C[C["pop"] >= 500]; clog.append(("pop 500+", len(C)))
C = C[C.gq_pop / C["pop"] < 0.5]; clog.append(("gq under half", len(C)))
PC = pd.read_parquet(RAW / "places" / "places_county_2025.parquet")
OUT["places_county_file_counties"] = int(PC.locationid.nunique())
PC = PC[PC.data_value_type.str.startswith("Crude") & PC.measureid.isin(PLACES)]
WC = PC.pivot_table(index="locationid", columns="measureid", values="data_value").rename(columns=PLACES)
C = C.join(WC, how="inner"); clog.append(("has any PLACES value", len(C)))
C = C[C.obesity.notna()]; clog.append(("has PLACES obesity", len(C)))
C["econ_index"] = index(C, ECON)
C["health_index"] = index(C, {k: 0 for k in CORE})
C = C[C.econ_index.notna() & C.health_index.notna()]; clog.append(("both indexes", len(C)))
OUT["county_filter_log"] = clog
CHR = pd.read_csv(RAW / "chr" / "analytic_supplement_20260325.csv", dtype=str)
CHR = CHR[CHR.countycode != "000"].set_index("fipscode")
OUT["chr_all_match"] = bool(C.index.isin(CHR.index).all())
num = lambda c: pd.to_numeric(CHR[c], errors="coerce").reindex(C.index)
C["life_expectancy"], C["overdose_rate"], C["suicide_rate"] = num("v147_rawvalue"), num("v138_rawvalue"), num("v161_rawvalue")
od = (num("v138_numerator") / num("v138_denominator") * 1e5 - C.overdose_rate).abs()
sd = (num("v161_numerator") / num("v161_denominator") * 1e5 - C.suicide_rate).abs()
OUT["chr_crude_test"] = {"overdose_max_gap": float(od.max()), "suicide_median_gap": float(sd.median())}
CP = pd.read_parquet(ROOT / "data" / "processed" / "counties.parquet")
OUT["county_compare"] = compare(C, CP, ["pop", "med_hh_income", "lf_change", "pct_uninsured", "obesity",
                                        "econ_index", "health_index", "life_expectancy", "overdose_rate",
                                        "suicide_rate"])
cr = {}
for y in ["health_index", "life_expectancy", "overdose_rate", "suicide_rate"]:
    cr[y] = {"income": round(spear(C.med_hh_income, C[y]), 3), "econ_index": round(spear(C.econ_index, C[y]), 3),
             "blank": int(C[y].isna().sum()),
             "blank_pop_pct": round(float(C.loc[C[y].isna(), "pop"].sum() / C["pop"].sum() * 100), 1),
             "median_pop_blank": float(C.loc[C[y].isna(), "pop"].median()) if C[y].isna().any() else None,
             "median_pop_value": float(C.loc[C[y].notna(), "pop"].median())}
OUT["county_corr"] = cr

# ---------------- coverage numbers ----------------
idx = T.index
Q = pd.qcut(T.med_hh_income, 5, labels=False)
a = rd(A24, "B99192").reindex(idx)
sh = (a.B99192_001E - a.B99192_002E) / a.B99192_001E * 100
cov = {"income_any_nat": float((a.B99192_001E - a.B99192_002E).sum() / a.B99192_001E.sum() * 100),
       "income_all_nat": float(a.B99192_008E.sum() / a.B99192_001E.sum() * 100),
       "income_any_median": float(sh.median()), "income_any_by_fifth": sh.groupby(Q).median().round(1).tolist()}
for t in ["B99231", "B992701", "B992518", "B99221"]:
    d = rd(A24, t).reindex(idx); s = d[f"{t}_002E"] / d[f"{t}_001E"] * 100
    cov[t] = {"nat": round(float(d[f"{t}_002E"].sum() / d[f"{t}_001E"].sum() * 100), 1),
              "median": round(float(s.median()), 1), "by_fifth": s.groupby(Q).median().round(1).tolist()}
for y, f in [(2019, A19), (2024, A24)]:
    d = rd(f, "B99231"); d = d[d.index.str[:2].isin(FIPS)]
    cov[f"emp_alloc_{y}"] = round(float(d.B99231_002E.sum() / d.B99231_001E.sum() * 100), 1)
mo = pd.read_parquet(A24 / "B19013.parquet").set_index("geoid").reindex(idx)
rel_moe = pd.to_numeric(mo.B19013_001M, errors="coerce") / T.med_hh_income * 100
rel_moe = rel_moe.where(pd.to_numeric(mo.B19013_001M, errors="coerce") >= 0)
cov["income_moe_median"] = round(float(rel_moe.median()), 1)
cov["income_moe_by_fifth"] = rel_moe.groupby(Q).median().round(1).tolist()


def moe_share(t, n, d_):
    raw = pd.read_parquet(A24 / f"{t}.parquet").set_index("geoid").reindex(idx)
    g_ = lambda c: pd.to_numeric(raw[c], errors="coerce")
    num_, den_ = (g_(n + "E") if isinstance(n, str) else sum(g_(x + "E") for x in n)), g_(d_ + "E")
    mn = (g_(n + "M") if isinstance(n, str) else np.sqrt(sum(g_(x + "M") ** 2 for x in n)))
    md = g_(d_ + "M")
    p = num_ / den_
    inner = mn ** 2 - p ** 2 * md ** 2
    m = np.sqrt(inner.where(inner >= 0, mn ** 2 + p ** 2 * md ** 2)) / den_ * 100
    return m, p * 100


m200, _ = moe_share("C17002", "C17002_008", "C17002_001")
cov["fpl200_moe_median"] = round(float(m200.median()), 1)
for name, t, n, d_ in [("unemp", "B23025", "B23025_005", "B23025_003"), ("snap", "B22003", "B22003_002", "B22003_001"),
                       ("uninsured", "B27010", ["B27010_017", "B27010_033", "B27010_050", "B27010_066"], "B27010_001")]:
    m, p = moe_share(t, n, d_)
    ok = p.notna()
    cov[f"{name}_moe_over_half_pct"] = round(float(((m > p / 2) & ok).sum() / ok.sum() * 100), 1)
Pt = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet")
Pt = Pt[Pt.measureid.isin(list(PLACES)[:14])]
Pt = Pt[Pt.locationname.astype(str).str.zfill(11).isin(idx)]
Pt = Pt.assign(w=Pt.high_confidence_limit - Pt.low_confidence_limit)
Pt = Pt.assign(rw=Pt.w / Pt.data_value * 100)
ob = Pt[Pt.measureid == "OBESITY"]
cov["obesity_ci_median"] = round(float(ob.w.median()), 1); cov["obesity_median"] = round(float(ob.data_value.median()), 1)
rwm = Pt.groupby("measureid").rw.median()
cov["rel_ci_range"] = [round(float(rwm.min()), 0), round(float(rwm.max()), 0)]
OUT["coverage"] = cov

# ---------------- built viz ----------------
html = (ROOT / "dist" / "index.html").read_text()
m = re.search(r'\{"states":\[.*?\],"geos":', html)
start = m.start()
dec = json.JSONDecoder()
data, _ = dec.raw_decode(html[start:])
vz = {}
for geo, frame in [("tract", TP.sort_index()), ("county", CP.sort_index())]:
    G = data["geos"][geo]
    errs = {}
    for c in G["cols"]:
        q = np.frombuffer(base64.b64decode(c["data"]), dtype="<u2").astype(float)
        v = np.where(q == 65535, np.nan, c["min"] + q / 65534 * (c["max"] - c["min"]))
        src = frame[c["key"]].astype(float).to_numpy()
        step = (c["max"] - c["min"]) / 65534
        both = ~np.isnan(v) & ~np.isnan(src)
        errs[c["key"]] = {"max_err_in_steps": float(np.abs(v[both] - src[both]).max() / step) if step else 0,
                          "blank_mismatch": int((np.isnan(v) != np.isnan(src)).sum())}
    dec_v = {c["key"]: np.where(np.frombuffer(base64.b64decode(c["data"]), dtype="<u2") == 65535, np.nan,
                                c["min"] + np.frombuffer(base64.b64decode(c["data"]), dtype="<u2") / 65534 * (c["max"] - c["min"]))
             for c in G["cols"]}
    ys = ["health_index"] + (["life_expectancy", "overdose_rate", "suicide_rate"] if geo == "county" else [])
    shown = {f"{y}~med_hh_income": round(spear(pd.Series(dec_v["med_hh_income"]), pd.Series(dec_v[y])), 2) for y in ys}
    shown["n_default_view"] = int((~np.isnan(dec_v["med_hh_income"]) & ~np.isnan(dec_v["health_index"])).sum())
    vz[geo + "_page_rank_corr"] = shown
    vz[geo] = {"n": G["n"], "n_cols": len(G["cols"]), "worst_step_err": max(e["max_err_in_steps"] for e in errs.values()),
               "blank_mismatch": sum(e["blank_mismatch"] for e in errs.values()),
               "econ": sum(c["side"] == "econ" for c in G["cols"]),
               "health": sum(c["side"] == "health" for c in G["cols"])}
OUT["viz"] = vz
OUT["viz_notes"] = data["notes"]


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


(ROOT / "analysis" / "tieout.json").write_text(json.dumps(clean(OUT), indent=1))
print(json.dumps(clean({k: v for k, v in OUT.items() if k != "viz_notes"}), indent=1))
