"""Final tract sets for the spotlight finalists, after deep research (analysis/spotlight/deep/*.md).

Each finalist's tracts are the deep-research keep list. That list drops prisons, jails, single public housing
complexes and tracts in other neighborhoods, and adds the other half of a split tract where an old outline
needs it. Rebuilt or merged sets:
  U062   Watts rebuilt from 8 tracts (Jordan Downs and Nickerson Gardens tracts left out)
  U062X  the same without tract 2431 (Imperial Courts is about a third of its homes), as a check
  R004   both Owsley County tracts, so the tracts equal the county and match county series
  U027   North St. Louis, plus The Ville (1113) and Carr Square/Pruitt-Igoe (1275), which pass the screen on their own
  U039   West Baltimore, plus tract 1502 (Presbury St), which passes the screen on its own
  BOS_NUBIAN  Roxbury tracts 803 and 804.01 (Nubian Square), the tracts in Boston's life expectancy gap reporting
Backups with no deep research keep their screen tracts.
Stability and the 2010-2020 land match use the screen's rules (scripts/72_screen.py).

Output: analysis/spotlight/final_sets.csv (cand_id, role, tracts, n_tracts, match_2010_2020, stability_1990)
"""
import json, importlib.util, sys
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT

OUT = ROOT / "analysis" / "spotlight"
deep = [json.loads(l) for l in open(OUT / "deep.jsonl") if l.strip()]
deep = {d["cand_id"]: d for d in deep if "keep_tracts" in d}
cand = pd.read_csv(OUT / "candidates.csv", dtype={"tracts": str}).set_index("cand_id")

sets = {k: v["keep_tracts"] for k, v in deep.items()}
sets["U062X"] = [t for t in sets["U062"] if t != "06037243100"]
sets["R004"] = ["21189930100", "21189930200"]
# redlining candidates: adjacent tracts that pass the screen on their own and hold the places the story is about
sets["U027"] = sets["U027"] + ["29510111300", "29510127500"]   # The Ville and Homer G. Phillips; Carr Square and the Pruitt-Igoe site
sets["U039"] = sets["U039"] + ["24510150200"]                  # Sandtown block of Presbury St (Freddie Gray arrest site)
sets.setdefault("BOS_NUBIAN", ["25025080300", "25025080401"])
BACKUP = ["U043", "U039", "U027", "U017", "U032", "U063", "U011", "U020", "R015", "R019", "R027", "R021", "R035", "R047"]
for b in BACKUP: sets.setdefault(b, cand.loc[b, "tracts"].split(";"))

# reuse the screen's stability function without rerunning the screen
src = (ROOT / "scripts" / "72_screen.py").read_text()
start, stop = src.index("# ---------- stability ----------"), src.index("def stability(")
end = src.index("rows = []", stop)
ns = {"pd": pd, "np": np, "say": lambda *a: None}
exec("from common import RAW\n" + src[start:end], ns)

rows = []
for k, tr in sets.items():
    f20, stab, core = ns["stability"](tr)
    rows.append(dict(cand_id=k, role="finalist" if k in deep or k in ("U062X", "BOS_NUBIAN") else "backup",
                     tracts=";".join(tr), n_tracts=len(tr), match_2010_2020=round(f20, 3) if np.isfinite(f20) else np.nan,
                     stability_1990=round(stab, 3) if np.isfinite(stab) else np.nan))
f = pd.DataFrame(rows)
f.to_csv(OUT / "final_sets.csv", index=False)
print(f.to_string(index=False, columns=["cand_id", "role", "n_tracts", "match_2010_2020", "stability_1990"]))
