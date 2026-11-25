"""Public schools inside North Birmingham's four tracts, every school year 1986-87 to 2023-24, placed by street address.

Source: NCES Common Core of Data school directory via the Urban Institute Education Data Portal
(https://educationdata.urban.org/api/v1/schools/ccd/directory/{year}/?leaid=0100390, Birmingham City Schools; year = fall).
Directory coordinates are missing or wrong for many rows, so each distinct street address is matched with the Census
geocoder (benchmark Public_AR_Current, vintage Census2020_Current) and the school counts if its 2020 tract is one of the four.
Before 1998 the directory has no street addresses; a school is placed at the address its NCES ID carries in the first
later year that has one. Schools that closed before 1998 (no address in any year) are listed in the output as unplaced.
Street names are cleaned before matching (NORTH -> N, COURT -> CT; Huntsville Rd N was renamed F L Shuttlesworth Dr).
Three schools closed before 1998 and never carry an address; they are placed by hand from Bhamwiki (weak source, flagged
in the output): old Carver High, 3400 33rd Terrace N (closed 1998); Eagan Elementary, 1716 31st Ave N; Shields Elementary,
3969 14th Ave N. Charter schools (not in the district file) are added from the county directory, 2017 on.
Regular schools are CCD school_type 1; alternative (4) and virtual schools are listed but not counted as regular.
Outputs: analysis/spotlight/schools_geocoded_northbirmingham.csv (one row per school-year inside the tracts),
analysis/spotlight/schools_geocode_cache.csv
"""
import sys, time
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
T = set(pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U034"].tracts.split(";"))
CACHE = ROOT / "analysis/spotlight/schools_geocode_cache.csv"
cache = pd.read_csv(CACHE, dtype=str).set_index("key").tract.to_dict() if CACHE.exists() else {}


import re
def clean(st):
    st = st.upper().replace(".", "").replace("HUNTSVILLE RD N", "F L SHUTTLESWORTH DR")
    st = re.sub(r"\bNORTH\b", "N", st); st = re.sub(r"\bCOURT\b", "CT", st); st = re.sub(r"\bTERR\b", "TER", st)
    return re.sub(r"\s+", " ", st).strip()


def tract(street, city, zipc):
    street = clean(street); key = f"{street}|{zipc}".upper()
    if key in cache: return cache[key]
    p = dict(street=street, city=city or "Birmingham", state="AL", zip=zipc or "", benchmark="Public_AR_Current",
             vintage="Census2020_Current", layers="Census Tracts", format="json")
    for _ in range(3):
        try:
            m = requests.get("https://geocoding.geo.census.gov/geocoder/geographies/address", params=p, timeout=60).json()["result"]["addressMatches"]
            cache[key] = m[0]["geographies"]["Census Tracts"][0]["GEOID"] if m else ""; break
        except Exception: time.sleep(3)
    else: cache[key] = ""
    return cache[key]


HAND = {"010039000110": ("3400 33RD TER N", "Birmingham", "35207"), "010039000120": ("1716 31ST AVE N", "Birmingham", "35207"),
        "010039000183": ("3969 14TH AVE N", "Birmingham", "35234")}
rows, years, addr, unplaced = [], {}, {}, []
for y in range(1986, 2024):
    u, res = f"https://educationdata.urban.org/api/v1/schools/ccd/directory/{y}/?leaid=0100390", []
    while u:
        j = requests.get(u, timeout=120).json(); res += j.get("results", []); u = j.get("next")
    if y >= 2017:
        u = f"https://educationdata.urban.org/api/v1/schools/ccd/directory/{y}/?fips=1&county_code=1073&charter=1"
        while u:
            j = requests.get(u, timeout=120).json(); res += [r for r in j.get("results", []) if r.get("leaid") != "0100390"]; u = j.get("next")
    years[y] = res
    for r in res:
        st = (r.get("street_location") or "").strip()
        if st and r.get("ncessch") not in addr: addr[r["ncessch"]] = (st, r.get("city_location"), str(r.get("zip_location") or "")[:5])
for y, res in years.items():
    for r in res:
        st = (r.get("street_location") or "").strip()
        if st: a = (st, r.get("city_location"), str(r.get("zip_location") or "")[:5])
        elif r.get("ncessch") in addr: a = addr[r["ncessch"]]
        elif r.get("ncessch") in HAND: a = HAND[r["ncessch"]]
        else:
            unplaced.append(dict(year=y, ncessch=r.get("ncessch"), school=r.get("school_name"), enrollment=r.get("enrollment"))); continue
        st = a[0]; r = {**r, "city_location": a[1], "zip_location": a[2]}
        t = tract(st, r.get("city_location"), str(r.get("zip_location") or "")[:5])
        if t in T:
            name = r.get("school_name") or ""
            kind = "virtual" if "VIRTUAL" in name.upper() else ("regular" if r.get("school_type") == 1 else "other")
            rows.append(dict(year=y, ncessch=r.get("ncessch"), school=name, address=st, tract=t, kind=kind, charter=r.get("charter"),
                             placed_by="Bhamwiki" if r.get("ncessch") in HAND else "NCES address",
                             status=r.get("school_status"), enrollment=r.get("enrollment")))
    print(y, len(res), "district rows;", sum(1 for x in rows if x["year"] == y), "inside", flush=True)
pd.DataFrame([dict(key=k, tract=v) for k, v in cache.items()]).to_csv(CACHE, index=False)
u = pd.DataFrame(unplaced).groupby(["ncessch", "school"]).agg(first=("year", "min"), last=("year", "max"), enr=("enrollment", "max")).reset_index()
u.to_csv(ROOT / "analysis/spotlight/schools_unplaced_birmingham.csv", index=False); print("unplaced (closed before 1998):"); print(u.to_string(index=False))
d = pd.DataFrame(rows); d.to_csv(ROOT / "analysis/spotlight/schools_geocoded_northbirmingham.csv", index=False)
reg = d[d.kind == "regular"]; reg = reg.assign(enr=reg.enrollment.where(reg.enrollment > 0))
print(reg.groupby("year").agg(schools=("ncessch", "nunique"), students=("enr", "sum")).to_string())
print(d.pivot_table(index=["school", "address"], columns="year", values="enrollment", aggfunc="first").iloc[:, ::3].to_string())
