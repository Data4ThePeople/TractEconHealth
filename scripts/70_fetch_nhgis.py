"""NHGIS extract for the community spotlight series (IPUMS API; key from ~/.claude/d4tp-process/.env).

Tract time series, nominal boundaries (each year on its own tract lines), 1970-2000 decennial:
  AV0 total population, B18 persons by race [5], CL6 persons below poverty, AX6 persons for whom poverty is determined,
  B79 median household income, AB2 median family income, B84 persons 16+ by labor force and employment status,
  BS7 households by income [4].
Tract time series standardized to 2010 tracts, 1990-2020: CL8 population, CM1 race [7], CM9 occupancy, CN1 tenure.
Shapefiles: 1970, 1980 and 1990 tracts (2008 TIGER/Line basis) and 2010 tracts (2010 TIGER/Line).
Output: data/raw/nhgis/extract/ (zips as delivered).
"""
import sys, time, requests
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
K = read_env_file(Path.home() / ".claude/d4tp-process/.env")["IPUMS_API_KEY"]
H = {"Authorization": K, "Content-Type": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data/raw/nhgis/extract"; OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.ipums.org/extracts?collection=nhgis&version=2"

nom = {"AV0": ["1970", "1980", "1990", "2000", "2010", "2020"], "B18": ["1970", "1980", "1990", "2000", "2010", "2020"],
       "CL6": ["1970", "1980", "1990", "2000"], "AX6": ["1970", "1980", "1990", "2000"],
       "B79": ["1980", "1990", "2000"], "AB2": ["1980", "1990", "2000"],
       "B84": ["1970", "1980", "1990", "2000"], "BS7": ["1970", "1980", "1990", "2000"]}
std = {"CL8": ["1990", "2000", "2010", "2020"], "CM1": ["1990", "2000", "2010", "2020"],
       "CM9": ["1990", "2000", "2010", "2020"], "CN1": ["1990", "2000", "2010", "2020"]}
tst = {k: {"years": v, "geogLevels": ["tract"]} for k, v in {**nom, **std}.items()}
body = {"timeSeriesTables": tst, "timeSeriesTableLayout": "time_by_column_layout",
        "shapefiles": ["us_tract_1970_tl2008", "us_tract_1980_tl2008", "us_tract_1990_tl2008", "us_tract_2010_tl2010"],
        "dataFormat": "csv_no_header", "description": "D4TP community spotlight series"}
r = requests.post(API, headers=H, json=body, timeout=120)
if r.status_code >= 300: sys.exit(f"{r.status_code} {r.text[:2000]}")
n = r.json()["number"]; print("extract", n)
while True:
    s = requests.get(f"https://api.ipums.org/extracts/{n}?collection=nhgis&version=2", headers=H, timeout=120).json()
    if s["status"] == "completed": break
    if s["status"] in ("failed", "canceled"): sys.exit(str(s)[:2000])
    time.sleep(30)
for kind, link in s["downloadLinks"].items():
    url = link["url"]; f = OUT / url.split("/")[-1]
    with requests.get(url, headers=H, stream=True, timeout=600) as d:
        d.raise_for_status(); f.write_bytes(d.content)
    print(kind, f.name, f.stat().st_size)
