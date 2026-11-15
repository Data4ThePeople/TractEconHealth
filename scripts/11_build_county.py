"""Build county measures and indexes -> data/processed/counties.parquet (+ county_filter_log.csv).

Same ACS measure definitions as tracts (10_build.build_acs, pointed at the county tables). Health from the PLACES
2025 county release (CDC's own county estimates, not averaged tracts). Labor force change compares the same county
code in 2015-2019 and 2020-2024; blank where the code does not exist in both (Connecticut planning regions).
County-only measures: life expectancy, drug overdose deaths and suicides from County Health Rankings (March 2026).
Same filters and index rules as tracts; percentile ranks are taken across counties."""
import importlib.util, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, PROC
spec = importlib.util.spec_from_file_location("b", os.path.join(os.path.dirname(__file__), "10_build.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
b.ACS = RAW / "acs_county"


def main():
    a = b.build_acs()
    d19, _ = b.table("B23025", 2019)
    lf19 = d19.B23025_002E.reindex(a.index)
    a["lf_change"] = ((a.lf_2024 / lf19 - 1) * 100).where(lf19 >= 100)

    p = pd.read_parquet(RAW / "places" / "places_county_2025.parquet")
    p = p[p.data_value_type.str.startswith("Crude") & p.measureid.isin(b.PLACES_KEEP)]
    w = p.pivot(index="locationid", columns="measureid", values="data_value").rename(columns=b.PLACES_KEEP)
    w.index = w.index.astype(str).str.zfill(5)
    meta = p.drop_duplicates("locationid").set_index("locationid")[["stateabbr", "locationname"]]
    meta.index = meta.index.astype(str).str.zfill(5)
    df = a.join(w.join(meta), how="left")
    df["countyfips"] = df.index

    log = [("all counties (ACS 2020-2024, 50 states + DC)", len(df), df["pop"].sum())]
    df = df[df["pop"] >= 500]; log.append(("population 500 or more", len(df), df["pop"].sum()))
    df = df[(df.gq_pop / df["pop"]) < 0.5]; log.append(("group quarters under 50% of population", len(df), df["pop"].sum()))
    df = df[df.obesity.notna()]; log.append(("has PLACES estimates", len(df), df["pop"].sum()))
    df["econ_index"], df["econ_n"] = b.index(df, list(b.ECON), list(b.ECON.values()))
    df["health_index"], df["health_n"] = b.index(df, b.HEALTH_CORE, [-1] * len(b.HEALTH_CORE))
    df = df[df.econ_index.notna() & df.health_index.notna()]
    log.append(("has both indexes", len(df), df["pop"].sum()))
    for c in ["econ_index", "health_index"]:
        df[c] = (df[c] - df[c].min()) / (df[c].max() - df[c].min()) * 100

    chr_ = pd.read_csv(RAW / "chr" / "analytic_supplement_20260325.csv", dtype={"fipscode": str}, low_memory=False)
    chr_ = chr_[chr_.countycode.astype(str).str.zfill(3) != "000"].set_index("fipscode")
    for k, v in {"life_expectancy": "v147", "overdose_rate": "v138", "suicide_rate": "v161"}.items():
        df[k] = pd.to_numeric(chr_[v + "_rawvalue"], errors="coerce").reindex(df.index)
    if df.index.duplicated().any():
        raise ValueError("duplicate county codes")
    df.to_parquet(PROC / "counties.parquet")
    pd.DataFrame(log, columns=["step", "counties", "population"]).to_csv(PROC / "county_filter_log.csv", index=False)
    for s, n, pp in log:
        print(f"{s:45s} {n:>6,} counties {pp:>13,.0f} people")
    print("lf_change blank:", int(df.lf_change.isna().sum()), list(df.index[df.lf_change.isna()])[:12])
    print("CHR blank:", {k: int(df[k].isna().sum()) for k in ["life_expectancy", "overdose_rate", "suicide_rate"]})
    print("states:", df.stateabbr.nunique())


if __name__ == "__main__":
    main()
