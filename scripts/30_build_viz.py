"""Pack tract data into src/template.html -> dist/index.html (one self-contained file).
Each measure is stored as 16-bit integers scaled between its min and max (65535 = missing), base64-encoded.
Nothing is precomputed for display: trend line, correlation and axes are computed in the page."""
import base64, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import PROC, ROOT

ECON = [  # key, label, unit, direction note, group
    ("econ_index", "Economic index", "idx", "0 to 100, higher is better", ""),
    ("med_hh_income", "Median household income", "$", "Higher is better", "Income"),
    ("per_capita_income", "Income per person", "$", "Higher is better", "Income"),
    ("pct_above_200fpl", "People above 200% of poverty line", "%", "Higher is better", "Income"),
    ("prime_lfpr", "Labor force participation, ages 25-54", "%", "Higher is better", "Work"),
    ("prime_epop", "Share employed, ages 25-54", "%", "Higher is better", "Work"),
    ("unemp_rate", "Unemployment rate", "%", "Lower is better", "Work"),
    ("lf_change", "Labor force change, 2015-19 to 2020-24", "%", "Higher is better", "Work"),
    ("pct_cost_burdened", "Households paying 30%+ of income for housing", "%", "Lower is better", "Housing"),
    ("med_rent_pct_income", "Median rent as share of income", "%", "Lower is better", "Housing"),
    ("pct_snap", "Households receiving SNAP", "%", "Lower is better", "Assistance and coverage"),
    ("pct_medicaid", "People on Medicaid or other means-tested coverage", "%", "Lower is better", "Assistance and coverage"),
    ("pct_uninsured", "People without health insurance", "%", "Lower is better", "Assistance and coverage"),
    ("pct_public_assist", "Households with cash public assistance", "%", "Lower is better", "Assistance and coverage"),
    ("gini", "Income inequality (Gini index)", "g", "Not in the index", "Assistance and coverage"),
]
HEALTH = [
    ("health_index", "Health index", "idx", "0 to 100, higher is better", ""),
    ("obesity", "Obesity", "%", "Share of adults", "Physical"),
    ("diabetes", "Diabetes", "%", "Share of adults", "Physical"),
    ("high_bp", "High blood pressure", "%", "Share of adults", "Physical"),
    ("chd", "Coronary heart disease", "%", "Share of adults", "Physical"),
    ("copd", "COPD", "%", "Share of adults", "Physical"),
    ("disability", "Any disability", "%", "Share of adults", "Physical"),
    ("physical_distress", "Frequent physical distress", "%", "Share of adults", "Physical"),
    ("fair_poor_health", "Fair or poor general health", "%", "Share of adults", "Physical"),
    ("depression", "Depression (ever diagnosed)", "%", "Share of adults", "Mental"),
    ("mental_distress", "Frequent mental distress", "%", "Share of adults", "Mental"),
    ("smoking", "Current smoking", "%", "Share of adults", "Behaviors"),
    ("binge_drinking", "Binge drinking", "%", "Share of adults", "Behaviors"),
    ("inactivity", "No leisure-time physical activity", "%", "Share of adults", "Behaviors"),
    ("short_sleep", "Short sleep (under 7 hours)", "%", "Share of adults", "Behaviors"),
    ("food_insecurity", "Food insecurity", "%", "Share of adults; not in index; 39 states", "Social needs"),
    ("loneliness", "Loneliness", "%", "Share of adults; not in index; 39 states", "Social needs"),
    ("no_emotional_support", "Lack of social and emotional support", "%", "Share of adults; not in index; 39 states", "Social needs"),
]
STATE_NAMES = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut",
 "DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana",
 "IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan",
 "MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
 "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
 "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
 "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


def pack(v):
    v = v.astype(float).to_numpy()
    ok = np.isfinite(v)
    lo, hi = float(v[ok].min()), float(v[ok].max())
    q = np.full(len(v), 65535, dtype="<u2")
    q[ok] = np.round((v[ok] - lo) / (hi - lo if hi > lo else 1) * 65534).astype("<u2")
    return lo, hi, b64(q)


def main():
    df = pd.read_parquet(PROC / "tracts.parquet").sort_index()
    log = pd.read_csv(PROC / "filter_log.csv")
    states = sorted(df.stateabbr.unique(), key=lambda s: STATE_NAMES[s])
    sidx = {s: i for i, s in enumerate(states)}
    counties = sorted((df.countyname + ", " + df.stateabbr).unique())
    cidx = {c: i for i, c in enumerate(counties)}
    cols = []
    for side, spec in (("econ", ECON), ("health", HEALTH)):
        for k, label, unit, dirn, grp in spec:
            lo, hi, data = pack(df[k])
            cols.append({"key": k, "label": label, "unit": unit, "dir": dirn, "group": grp, "side": side,
                         "min": lo, "max": hi, "data": data})
    t = df.index.str[5:]
    tract = [f"{int(x[:4])}" + (f".{x[4:]}" if x[4:] != "00" else "") for x in t]
    kept = int(log.tracts.iloc[-1])
    notes = f"""
<p><b>What each dot is.</b> One census tract, a neighborhood of about 4,000 people. {kept:,} tracts are shown. Tracts
with fewer than 500 people, or where half or more of residents live in group quarters such as prisons, dormitories
or nursing homes, are left out.</p>
<p><b>Economic measures</b> come from the Census Bureau's American Community Survey, 2020-2024 five-year estimates.
Labor force change compares 2015-2019 with 2020-2024, matching 2010 and 2020 tract boundaries. The economic index
averages each tract's national percentile rank on the twelve measures listed above Gini, each turned so that
higher is better.</p>
<p><b>Health measures</b> come from CDC PLACES, 2025 release, mostly based on the 2023 Behavioral Risk Factor
Surveillance System. These are model estimates, not survey results for each tract. CDC builds them from a national
survey using each tract's mix of age, sex, race and ethnicity, and education, along with county and tract poverty.
Because of that, part of the link between a tract's income and its health estimate is built into the estimate
itself. The health index averages the national percentile rank of the fourteen measures from obesity through short
sleep, turned so that higher is better. Food insecurity, loneliness and emotional support are not in the index
because CDC has them for only 39 states and DC.</p>
<p><b>Kentucky and Pennsylvania are not shown.</b> The 2025 PLACES release has no estimates for these two states for
measures based on 2023 survey data.</p>
<p><b>Correlation is not cause.</b> The chart shows which tracts have both conditions. It does not show that one
causes the other. Every value is an estimate with a margin of error, larger in small tracts.</p>"""
    data = {"n": len(df), "cols": cols, "states": [STATE_NAMES[s] for s in states],
            "state": b64(df.stateabbr.map(sidx).to_numpy().astype("u1")),
            "county": b64((df.countyname + ", " + df.stateabbr).map(cidx).to_numpy().astype("<u2")),
            "counties": counties, "tract": tract, "notes": notes}
    html = (ROOT / "src" / "template.html").read_text().replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "index.html").write_text(html)
    print(f"dist/index.html {len(html)/1e6:.1f} MB, {len(df):,} tracts, {len(cols)} measures")


if __name__ == "__main__":
    main()
