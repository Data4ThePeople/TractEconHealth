"""Claude's own tie-out for North and East Flint (U013): rebuild post numbers by a second path.

1. 2020 people, Black, white, housing units and vacant units straight from the 2020 redistricting file for the
   eight 2020 tracts (Census API) vs. the NHGIS 2010-tract numbers used in the post.
2. 2010 the same from the 2010 redistricting file for the 2010 tracts.
3. Medicaid ages 19-64 and uninsured ages 19-64 re-pulled from ACS 2020-2024 C27007 / B27010 by a separate query.
4. Every number in a fixed list of post sentences checked against the analysis CSVs.
Writes analysis/spotlight/tieout_northflint.csv.
"""
import sys
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
A = ROOT / "analysis/spotlight"
T20 = pd.read_csv(A / "final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")
P = pd.read_csv(A / "people_homes_northflint.csv", dtype={"year": str}).set_index(["area", "measure", "year"]).value
NF = "North and East Flint"
rows = []
def chk(item, post, check, tol):
    rows.append(dict(item=item, post=post, check=round(check, 3), ok=abs(post - check) <= tol))

def api(path, v):
    r = requests.get(f"https://api.census.gov/data/{path}", params={"get": ",".join(v), "for": "tract:*", "in": "state:26 county:049", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = "26049" + d.tract
    for x in v: d[x] = pd.to_numeric(d[x])
    return d[d.geoid.isin(T20)]

d20 = api("2020/dec/pl", ["P1_001N", "P1_003N", "P1_004N", "H1_001N", "H1_003N"])
for m, v in (("people", "P1_001N"), ("white", "P1_003N"), ("black", "P1_004N"), ("homes", "H1_001N"), ("vacant_homes", "H1_003N")):
    chk(f"2020 {m}: NHGIS vs PL direct", P[(NF, m, "2020")], d20[v].sum(), 0.5)
d10 = api("2010/dec/pl", ["P001001", "P003002", "P003003"] if False else ["P001001", "P001003", "P001004", "H001001"])
chk("2010 people: NHGIS vs PL direct (same tract IDs)", P[(NF, "people", "2010")], d10.P001001.sum(), 0.5)
chk("2010 white", P[(NF, "white", "2010")], d10.P001003.sum(), 0.5)
chk("2010 black", P[(NF, "black", "2010")], d10.P001004.sum(), 0.5)
chk("2010 homes", P[(NF, "homes", "2010")], d10.H001001.sum(), 0.5)

# ACS insurance, second pull
c = [f"C27007_{i:03d}E" for i in range(1, 22)]
dc = api("2024/acs/acs5", c)
med1964 = dc[["C27007_007E", "C27007_017E"]].sum().sum(); den1964 = dc[["C27007_006E", "C27007_016E"]].sum().sum()
I = pd.read_csv(A / "insurance_northflint.csv").set_index(["area", "measure"])
chk("Medicaid 19-64 % (C27007 male+female 19-64)", I.loc[(NF, "medicaid_19_64_pct"), "pct"], 100 * med1964 / den1964, 0.05)
# B27010: ages 19-34 are cells 018 (total), 020 (employer only), 033 (no coverage); ages 35-64 are 034, 036, 050
b = api("2024/acs/acs5", ["B27010_018E", "B27010_020E", "B27010_033E", "B27010_034E", "B27010_036E", "B27010_050E"])
den = b.B27010_018E.sum() + b.B27010_034E.sum()
chk("Uninsured 19-64 % (B27010)", I.loc[(NF, "uninsured_19_64_pct"), "pct"], 100 * (b.B27010_033E.sum() + b.B27010_050E.sum()) / den, 0.05)
chk("Employer-only 19-64 %", I.loc[(NF, "employer_only_19_64_pct"), "pct"], 100 * (b.B27010_020E.sum() + b.B27010_036E.sum()) / den, 0.05)

# post sentence numbers vs CSVs (display rounding)
ch = lambda m, a, d: P[(a, f"{m}_change_pct", d)]
chk("people 1990s -13", -13, ch("people", NF, "1990-2000"), 0.5); chk("2000s -20", -20, ch("people", NF, "2000-2010"), 0.5)
chk("2010s -29", -29, ch("people", NF, "2010-2020"), 0.5); chk("rest of Flint 2010s -19", -19, ch("people", "Rest of Flint", "2010-2020"), 0.5)
chk("people 1990 23,592", 23592, P[(NF, "people", "1990")], 0.5); chk("people 2020 11,704", 11704, P[(NF, "people", "2020")], 0.5)
chk("children 2010s -31", -31, ch("children", NF, "2010-2020"), 0.5)
ad = 100 * ((P[(NF, "people", "2020")] - P[(NF, "children", "2020")]) / (P[(NF, "people", "2010")] - P[(NF, "children", "2010")]) - 1)
chk("adults 2010s -28", -28, ad, 0.5)
chk("children share 2000 32", 32, P[(NF, "children_pct", "2000")], 0.5); chk("children share 2020 28", 28, P[(NF, "children_pct", "2020")], 0.5)
chk("black 2010s -25", -25, ch("black", NF, "2010-2020"), 0.5)
chk("black share 2020 47", 47, P[(NF, "black_pct", "2020")], 0.5); chk("black share 1990 32", 32, P[(NF, "black_pct", "1990")], 0.5)
chk("homes -43% since 1990", 43, 100 * (1 - P[(NF, "homes", "2020")] / P[(NF, "homes", "1990")]), 0.5)
chk("homes lost 2010s ~2,500", 2500, P[(NF, "homes", "2010")] - P[(NF, "homes", "2020")], 50)
W = pd.read_csv(A / "wards_demolitions_northflint.csv").set_index("key")
chk("wards 3+4 land 85%", 85, 100 * (W.loc["Ward 3", "share_of_tract_land"] + W.loc["Ward 4", "share_of_tract_land"]), 0.5)
chk("ward 5 land 11%", 11, 100 * W.loc["Ward 5", "share_of_tract_land"], 0.5)
chk("demolition parcels single family 519", 519, W.loc["2015-2019 single family parcels", "value"], 0)
L = pd.read_csv(A / "labor_northflint.csv", dtype={"year": str}).set_index(["year", "area", "measure"])
chk("working 1990 ~7,000", 7000, L.loc[("1990", NF, "epop"), "num"], 100); chk("working 2020-24 ~3,800", 3800, L.loc[("2020-2024", NF, "epop"), "num"], 100)
chk("prime epop 56", 56, L.loc[("2020-2024", NF, "prime_epop"), "value"], 0.5); chk("county prime epop 76", 76, L.loc[("2020-2024", "Genesee County", "prime_epop"), "value"], 0.5)
for a, v in ((NF, 66), ("Genesee County", 30), ("Michigan", 20), ("United States", 16)): chk(f"Medicaid 19-64 {a} {v}", v, I.loc[(a, "medicaid_19_64_pct"), "pct"], 0.5)
for a, v in ((NF, 11), ("Genesee County", 8), ("Michigan", 7), ("United States", 12)): chk(f"uninsured 19-64 {a} {v}", v, I.loc[(a, "uninsured_19_64_pct"), "pct"], 0.5)
chk("children Medicaid 87", 87, I.loc[(NF, "medicaid_under19_pct"), "pct"], 0.5)
chk("employer-only 19 vs 57", 19, I.loc[(NF, "employer_only_19_64_pct"), "pct"], 0.5); chk("US employer-only 57", 57, I.loc[("United States", "employer_only_19_64_pct"), "pct"], 0.5)
# food (2026-11-26): PLACES re-read straight from the parquet, not from food_northflint.csv
pl = pd.read_parquet(ROOT / "data/raw/places/places_tract_2025.parquet")
pl = pl[pl.measureid.isin(["FOODINSECU", "FOODSTAMP", "LACKTRPT"])].copy()
pl["v"] = pd.to_numeric(pl.data_value); pl["w"] = pd.to_numeric(pl.totalpop18plus)
def wavg(d): return (d.v * d.w).sum() / d.w.sum()
for m, vals in (("FOODINSECU", (47, 21, 17, 17)), ("FOODSTAMP", (54, 21, 16, 14)), ("LACKTRPT", (25, 11, 9, 9))):
    d = pl[pl.measureid == m]
    for lab, sel, v in zip(("here", "Genesee", "MI", "US"), (d.locationname.astype(str).isin(T20), d.countyfips.astype(str) == "26049", d.stateabbr == "MI", d.v.notna()), vals):
        chk(f"{m} {lab} {v}", v, wavg(d[sel]), 0.5)
fi = pl[(pl.measureid == "FOODINSECU") & pl.locationname.astype(str).isin(T20)]
chk("food insecurity tract range low 34", 34, fi.v.min(), 0.5); chk("food insecurity tract range high 63", 63, fi.v.max(), 0.5); chk("food insecurity tracts = 8", 8, len(fi), 0)
fa = pd.read_csv(ROOT / "data/raw/usda_fara/Food Access Research Atlas.csv", dtype={"CensusTract": str})
fa = fa[fa.CensusTract.isin(T20)]
chk("LILA half mile all 8", 8, fa.LILATracts_halfAnd10.sum(), 0); chk("LILA 1 mile 4", 4, fa.LILATracts_1And10.sum(), 0)
import zipfile
z = zipfile.ZipFile(ROOT / "data/raw/snap/snap-retailer-locator-data2005-2025.zip")
sn = pd.read_csv(z.open(z.namelist()[0]), dtype=str, encoding="latin-1")
dav = sn[(sn.State == "MI") & sn["Street Name"].str.strip().str.upper().eq("DAVISON RD") & sn["Street Number"].str.strip().eq("1916")]
later = dav[~dav["Store Name"].str.contains("Kroger", case=False)]
chk("other grocers at 1916 Davison after Kroger (records)", 1, int(len(later) > 0), 0)
chk("Davison Rd Kroger just outside tracts (under 0.01 mile)", 0, pd.read_csv(A / "grocers_northflint.csv").query("`Store Name` == 'Kroger 112'").miles_from_tracts.iloc[0], 0.01)
k115 = pd.read_csv(A / "grocers_northflint.csv").query("`Store Name` == 'Kroger 115'")
chk("Richfield Rd Kroger inside tracts, authorized 1991, no end date", 1, int(k115.miles_from_tracts.iloc[0] == 0 and k115["Authorization Date"].iloc[0].endswith("1991") and str(k115["End Date"].iloc[0]).strip() in ("", "nan")), 0)
out = pd.DataFrame(rows); out.to_csv(A / "tieout_northflint.csv", index=False)
print(out.to_string()); print("FAILS:", (~out.ok).sum())
