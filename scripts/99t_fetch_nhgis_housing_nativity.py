"""NHGIS tract tables for the El Segundo Barrio analyses (story-first, 2026-11-26): homes, household size, crowding,
plumbing, nativity, year of entry and residence five years earlier, 1960 to 2000.

Dataset tables (nominal tracts of each year):
  1960_tPH   NTSUP3 total housing units; NT9 occupied units by persons in unit; NT25 persons in households and group
             quarters; NT11 occupied units by persons per room; NT64 housing units by plumbing; NT23 foreign stock by
             nativity; NT33 persons 5+ by residence in 1955
  1970_Cnt4H NT42A persons per room (occupied units); NT59B plumbing (occupied units)
  1970_Cnt4Pb NT28 residence in 1965
  1980_STF1  NT37A persons per room; NT47A plumbing      1980_STF3 NT34 residence in 1975
  1990_STF1  NH21 persons per room                       1990_STF3 NH64 plumbing; NP43 residence in 1985; NP36 year of entry
  2000_SF3a  NH049A plumbing by occupants per room; NP024A residence in 1995 (house level); NP023A year of entry
Time series tables (nominal, one row per tract and year): A41 housing units, A43 occupancy, AU9 persons in group
quarters, AT5 nativity.
Output: data/raw/nhgis/extract_housing/
"""
import io, sys, time, zipfile, requests
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
K = read_env_file(Path.home() / ".claude/d4tp-process/.env")["IPUMS_API_KEY"]
H = {"Authorization": K, "Content-Type": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data/raw/nhgis/extract_housing"; OUT.mkdir(parents=True, exist_ok=True)
if list(OUT.rglob("*.csv")): sys.exit("already extracted")
t = lambda *x: {"dataTables": list(x), "geogLevels": ["tract"]}
body = {"datasets": {"1960_tPH": t("NTSUP3", "NT9", "NT25", "NT11", "NT64", "NT23", "NT33"),
                     "1970_Cnt4H": t("NT42A", "NT59B"), "1970_Cnt4Pb": t("NT28"),
                     "1980_STF1": t("NT37A", "NT47A"), "1980_STF3": t("NT34"),
                     "1990_STF1": t("NH21"), "1990_STF3": t("NH64", "NP43", "NP36"),
                     "2000_SF3a": t("NH049A", "NP024A", "NP023A")},
        "timeSeriesTables": {k: {"geogLevels": ["tract"]} for k in ("A41", "A43", "AU9", "AT5")},
        "timeSeriesTableLayout": "time_by_row_layout", "dataFormat": "csv_header", "description": "D4TP El Segundo: housing and nativity 1960-2000"}
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
