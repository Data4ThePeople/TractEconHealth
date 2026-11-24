"""NHGIS tract population and tract maps for 1910, 1930, 1950 and 1960, to extend a spotlight's population chart before 1970.

Datasets: 1910_tPop_Misc (NT1 total population), 1930_tPop_Misc (NT1), 1950_tPH_Major (NT1), 1960_tPH (NTSUP2 total persons).
1940 comes from the existing extract (scripts/86_fetch_nhgis_1940.py). There is no 1920 tract file for Baltimore.
Shapefiles: us_tract_<year>_tl2008. Output: data/raw/nhgis/extract_early/ (unzipped)
"""
import io, sys, time, zipfile, requests
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
K = read_env_file(Path.home() / ".claude/d4tp-process/.env")["IPUMS_API_KEY"]
H = {"Authorization": K, "Content-Type": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data/raw/nhgis/extract_early"; OUT.mkdir(parents=True, exist_ok=True)
if list(OUT.rglob("*.csv")):
    sys.exit("already extracted")
API = "https://api.ipums.org/extracts?collection=nhgis&version=2"
body = {"datasets": {"1910_tPop_Misc": {"dataTables": ["NT1"], "geogLevels": ["tract"]},
                     "1930_tPop_Misc": {"dataTables": ["NT1"], "geogLevels": ["tract"]},
                     "1950_tPH_Major": {"dataTables": ["NT1"], "geogLevels": ["tract"]},
                     "1960_tPH": {"dataTables": ["NTSUP2"], "geogLevels": ["tract"]}},
        "shapefiles": ["us_tract_1910_tl2008", "us_tract_1930_tl2008", "us_tract_1950_tl2008", "us_tract_1960_tl2008"],
        "dataFormat": "csv_header", "description": "D4TP spotlights: tract population 1910-1960"}
r = requests.post(API, headers=H, json=body, timeout=120)
if r.status_code >= 300: sys.exit(f"{r.status_code} {r.text[:1500]}")
n = r.json()["number"]; print("extract", n, flush=True)
while True:
    s = requests.get(f"https://api.ipums.org/extracts/{n}?collection=nhgis&version=2", headers=H, timeout=120).json()
    if s["status"] == "completed": break
    if s["status"] in ("failed", "canceled"): sys.exit(str(s)[:1500])
    time.sleep(20)
for kind in ("tableData", "gisData"):
    z = requests.get(s["downloadLinks"][kind]["url"], headers=H, timeout=900); z.raise_for_status()
    zipfile.ZipFile(io.BytesIO(z.content)).extractall(OUT)
for inner in list(OUT.rglob("*.zip")):
    zipfile.ZipFile(inner).extractall(inner.parent)
print("done", sorted(p.name for p in OUT.rglob("*") if p.is_file())[:30])
