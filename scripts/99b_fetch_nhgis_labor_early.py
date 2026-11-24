"""NHGIS tract tables for labor force status, 1950 and 1960 (persons 14 and over), for labor measures before 1970.

1990 STF3 NP66 (sex by age by work disability status by employment status) and 2000 SF3 NPCT035B (sex by age by labor
force status) and NPCT035D (civilian labor force by sex by age by employment status). Output: data/raw/nhgis/extract_labor_early/
"""
import io, sys, time, zipfile, requests
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
K = read_env_file(Path.home() / ".claude/d4tp-process/.env")["IPUMS_API_KEY"]
H = {"Authorization": K, "Content-Type": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data/raw/nhgis/extract_labor_early"; OUT.mkdir(parents=True, exist_ok=True)
if list(OUT.rglob("*.csv")): sys.exit("already extracted")
body = {"datasets": {"1950_tPH_Major": {"dataTables": ["NT23", "NT25"], "geogLevels": ["tract"]},
                     "1960_tPH": {"dataTables": ["NT39"], "geogLevels": ["tract"]}},
        "dataFormat": "csv_header", "description": "D4TP West Baltimore: labor force 1950, 1960"}
r = requests.post("https://api.ipums.org/extracts?collection=nhgis&version=2", headers=H, json=body, timeout=120)
if r.status_code >= 300: sys.exit(f"{r.status_code} {r.text[:1500]}")
n = r.json()["number"]; print("extract", n, flush=True)
while True:
    s = requests.get(f"https://api.ipums.org/extracts/{n}?collection=nhgis&version=2", headers=H, timeout=120).json()
    if s["status"] == "completed": break
    if s["status"] in ("failed", "canceled"): sys.exit(str(s)[:1500])
    time.sleep(20)
z = requests.get(s["downloadLinks"]["tableData"]["url"], headers=H, timeout=900); z.raise_for_status()
zipfile.ZipFile(io.BytesIO(z.content)).extractall(OUT)
for inner in list(OUT.rglob("*.zip")): zipfile.ZipFile(inner).extractall(inner.parent)
print("done", sorted(p.name for p in OUT.rglob("*") if p.is_file()))
