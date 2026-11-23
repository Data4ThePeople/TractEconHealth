"""NHGIS 1940 census tracts (major cities) for the HOLC grade-by-race check in the West Dayton post.

Dataset 1940_tPH_Major: NT1 population, NT2 population by race, NT27 occupied dwellings by tenure,
NT28 tenure by race, NT36 median home value. Shapefile us_tract_1940_tl2008.
Output: data/raw/nhgis/extract_1940/ (zips as delivered, then unzipped)
"""
import io, sys, time, zipfile, requests
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
K = read_env_file(Path.home() / ".claude/d4tp-process/.env")["IPUMS_API_KEY"]
H = {"Authorization": K, "Content-Type": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data/raw/nhgis/extract_1940"; OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.ipums.org/extracts?collection=nhgis&version=2"
if list(OUT.rglob("*.csv")):
    sys.exit("already extracted")
body = {"datasets": {"1940_tPH_Major": {"dataTables": ["NT1", "NT2", "NT27", "NT28", "NT36"], "geogLevels": ["tract"]}},
        "shapefiles": ["us_tract_1940_tl2008"], "dataFormat": "csv_header", "description": "D4TP West Dayton: 1940 tracts for HOLC race check"}
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
print("done", sorted(p.name for p in OUT.rglob("*") if p.is_file())[:20])
