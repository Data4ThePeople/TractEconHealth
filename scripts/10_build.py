"""Build tract measures and the two indexes -> data/processed/tracts.parquet (+ filter log).

Economic measures come from ACS 2020-2024 (labor force change also uses 2015-2019 via tract families).
Health measures come from CDC PLACES 2025 (crude prevalence, % of adults).
Each ACS measure is built by matching the Census Bureau's own variable labels, so a wrong line number
cannot slip in; every label match is asserted to find the expected number of lines."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, PROC

ACS = RAW / "acs"
NA_CODES = [-999999999, -888888888, -666666666, -555555555, -333333333, -222222222]


def table(t, year=2024):
    d = pd.read_parquet(ACS / str(year) / f"{t}.parquet")
    lab = pd.read_csv(ACS / str(year) / f"{t}_labels.csv").set_index("var").label
    for c in d.columns:
        if c.startswith(t):
            d[c] = pd.to_numeric(d[c], errors="coerce")
            if c.endswith("E"):
                d.loc[d[c].isin(NA_CODES), c] = np.nan
    return d.set_index("geoid"), lab


def pick(lab, test, n=None):
    """Estimate variables whose label passes test(parts), where parts is the label split on '!!' with ':' removed."""
    v = sorted(k for k, s in lab.items() if k.endswith("E") and test([p.rstrip(":") for p in s.split("!!")]))
    if n is not None and len(v) != n:
        raise ValueError(f"expected {n} lines, got {len(v)}: {v}")
    return v


def share(num, den):
    return (num / den).where(den > 0) * 100


def build_acs():
    out = {}
    d, _ = table("B01003"); out["pop"] = d.B01003_001E; out["name"] = d.NAME
    d, _ = table("B26001"); out["gq_pop"] = d.B26001_001E
    d, _ = table("B19013"); out["med_hh_income"] = d.B19013_001E

    d, lab = table("C17002")
    above = pick(lab, lambda p: p[-1] == "2.00 and over", 1)
    out["pct_above_200fpl"] = share(d[above[0]], d.C17002_001E)

    # prime age 25-54: B23001 sex by age by employment status
    d, lab = table("B23001")
    prime = {"25 to 29 years", "30 to 34 years", "35 to 44 years", "45 to 54 years"}
    popv = pick(lab, lambda p: len(p) == 4 and p[3] in prime, 8)
    lfv = pick(lab, lambda p: len(p) == 5 and p[3] in prime and p[4] == "In labor force", 8)
    empv = pick(lab, lambda p: p[3:4] and p[3] in prime and (p[-1] == "In Armed Forces" or p[-2:] == ["Civilian", "Employed"]), 16)
    pp = d[popv].sum(axis=1, min_count=1)
    out["prime_lfpr"] = share(d[lfv].sum(axis=1, min_count=1), pp)
    out["prime_epop"] = share(d[empv].sum(axis=1, min_count=1), pp)
    out["prime_pop"] = pp

    d, lab = table("B23025")
    out["unemp_rate"] = share(d.B23025_005E, d.B23025_003E)
    out["lf_2024"] = d.B23025_002E

    # housing cost burden, renters and owners: B25140
    d, lab = table("B25140")
    tot = pick(lab, lambda p: p == ["Estimate", "Total"], 1)  # all occupied housing units
    burd = pick(lab, lambda p: len(p) == 4 and p[3] == "Over 30 Percent", 3)  # Census label wording
    nc = pick(lab, lambda p: len(p) == 4 and p[3] == "Not Calculated", 3)
    base = d[tot[0]] - d[nc].sum(axis=1)
    out["pct_cost_burdened"] = share(d[burd].sum(axis=1, min_count=1), base)
    out["_b25140_lines"] = (burd, nc)

    d, _ = table("B25071"); out["med_rent_pct_income"] = d.B25071_001E
    d, _ = table("B22003"); out["pct_snap"] = share(d.B22003_002E, d.B22003_001E)
    d, lab = table("C27007")
    mv = pick(lab, lambda p: p[-1] == "With Medicaid/means-tested public coverage", 6)
    out["pct_medicaid"] = share(d[mv].sum(axis=1, min_count=1), d.C27007_001E)
    d, lab = table("B27010")
    uv = pick(lab, lambda p: p[-1] == "No health insurance coverage", 4)
    out["pct_uninsured"] = share(d[uv].sum(axis=1, min_count=1), d.B27010_001E)
    d, _ = table("B19057"); out["pct_public_assist"] = share(d.B19057_002E, d.B19057_001E)
    d, _ = table("B19083"); out["gini"] = d.B19083_001E
    d, _ = table("B19301"); out["per_capita_income"] = d.B19301_001E

    lines = out.pop("_b25140_lines")
    print("B25140 burdened lines:", lines[0], "not computed:", lines[1])
    a = pd.DataFrame(out)
    a.index.name = "geoid"
    return a


def lf_change(a):
    fam = pd.read_parquet(PROC / "tract_families.parquet")
    d19, _ = table("B23025", 2019)
    f10 = fam[fam.vintage == "10"].set_index("geoid").family
    f20 = fam[fam.vintage == "20"].set_index("geoid").family
    lf19 = d19.B23025_002E.groupby(f10.reindex(d19.index)).sum()
    lf24 = a.lf_2024.groupby(f20.reindex(a.index)).sum()
    g = (lf24 / lf19.reindex(lf24.index) - 1) * 100
    g = g.where(lf19.reindex(lf24.index) >= 100)  # too few workers in 2015-19 to compare
    a["lf_change"] = f20.reindex(a.index).map(g)
    a["family"] = f20.reindex(a.index)
    a["family_size"] = a.family.map(fam.groupby("family").size())
    return a


PLACES_KEEP = {  # measureid -> short name (all: share of adults, lower is better)
    "OBESITY": "obesity", "CSMOKING": "smoking", "DEPRESSION": "depression", "MHLTH": "mental_distress",
    "PHLTH": "physical_distress", "GHLTH": "fair_poor_health", "BINGE": "binge_drinking", "LPA": "inactivity",
    "SLEEP": "short_sleep", "DIABETES": "diabetes", "BPHIGH": "high_bp", "COPD": "copd", "CHD": "chd",
    "DISABILITY": "disability", "FOODINSECU": "food_insecurity", "LONELINESS": "loneliness",
    "EMOTIONSPT": "no_emotional_support",
}


def build_places():
    p = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet")
    p = p[p.data_value_type.str.startswith("Crude")]
    missing = set(PLACES_KEEP) - set(p.measureid)
    if missing:
        raise ValueError(f"PLACES measure ids not found: {missing}; available: {sorted(p.measureid.unique())}")
    p = p[p.measureid.isin(PLACES_KEEP)]
    w = p.pivot(index="locationname", columns="measureid", values="data_value").rename(columns=PLACES_KEEP)
    w.index = w.index.astype(str).str.zfill(11)
    w.index.name = "geoid"
    meta = p.drop_duplicates("locationname").set_index("locationname")[["stateabbr", "countyname", "countyfips"]]
    meta.index = meta.index.astype(str).str.zfill(11)
    return w.join(meta)


ECON = {  # name -> +1 if higher is better
    "med_hh_income": 1, "pct_above_200fpl": 1, "prime_lfpr": 1, "prime_epop": 1, "unemp_rate": -1,
    "lf_change": 1, "pct_cost_burdened": -1, "med_rent_pct_income": -1, "pct_snap": -1, "pct_medicaid": -1,
    "pct_uninsured": -1, "pct_public_assist": -1,
}
HEALTH_CORE = ["obesity", "smoking", "depression", "mental_distress", "physical_distress", "fair_poor_health",
               "binge_drinking", "inactivity", "short_sleep", "diabetes", "high_bp", "copd", "chd", "disability"]
HEALTH_HRSN = ["food_insecurity", "loneliness", "no_emotional_support"]


def index(df, cols, signs):
    r = pd.DataFrame({c: df[c].rank(pct=True) * 100 * (1 if s > 0 else -1) + (0 if s > 0 else 100)
                      for c, s in zip(cols, signs)})
    have = r.notna().sum(axis=1)
    return r.mean(axis=1).where(have >= np.ceil(0.75 * len(cols))), have


def main():
    a = lf_change(build_acs())
    h = build_places()
    df = a.join(h, how="left")
    log = [("all tracts (ACS 2020-2024, 50 states + DC)", len(df), df["pop"].sum())]
    df = df[df["pop"] >= 500]; log.append(("population 500 or more", len(df), df["pop"].sum()))
    df = df[(df.gq_pop / df["pop"]) < 0.5]; log.append(("group quarters under 50% of population", len(df), df["pop"].sum()))
    df = df[df.obesity.notna()]; log.append(("has PLACES estimates", len(df), df["pop"].sum()))

    hrsn_states = df.groupby("stateabbr")[HEALTH_HRSN].apply(lambda x: x.notna().mean()).round(3)
    df["econ_index"], df["econ_n"] = index(df, list(ECON), list(ECON.values()))
    df["health_index"], df["health_n"] = index(df, HEALTH_CORE, [-1] * len(HEALTH_CORE))
    df = df[df.econ_index.notna() & df.health_index.notna()]
    log.append(("has both indexes", len(df), df["pop"].sum()))
    for c in ["econ_index", "health_index"]:  # rescale 0-100
        df[c] = (df[c] - df[c].min()) / (df[c].max() - df[c].min()) * 100
    if df.index.duplicated().any():
        raise ValueError("duplicate geoids")
    PROC.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROC / "tracts.parquet")
    pd.DataFrame(log, columns=["step", "tracts", "population"]).to_csv(PROC / "filter_log.csv", index=False)
    hrsn_states.to_csv(PROC / "hrsn_coverage_by_state.csv")
    for s, n, p in log:
        print(f"{s:45s} {n:>7,} tracts  {p:>13,.0f} people")
    print("states with no food insecurity estimates:", list(hrsn_states.index[hrsn_states.food_insecurity == 0]))


if __name__ == "__main__":
    main()
