"""ACS 5-year tables for every county (50 states + DC), same tables as 01_fetch_acs.py -> data/raw/acs_county/<year>/.
One request per table: all counties at once."""
import importlib.util, os, sys
import pandas as pd, requests
spec = importlib.util.spec_from_file_location("f", os.path.join(os.path.dirname(__file__), "01_fetch_acs.py"))
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
from common import RAW, STATES

def main():
    for year, tabs in f.TABLES.items():
        out = RAW / "acs_county" / str(year); out.mkdir(parents=True, exist_ok=True)
        base = f"https://api.census.gov/data/{year}/acs/acs5"
        for t in tabs:
            p = out / f"{t}.parquet"
            if p.exists(): continue
            lab = requests.get(f"{base}/groups/{t}.json", timeout=60).json()["variables"]
            pd.DataFrame([{"var": k, "label": v["label"]} for k, v in lab.items()]).to_csv(out / f"{t}_labels.csv", index=False)
            rows = f.get(base, {"get": f"NAME,group({t})", "for": "county:*", "key": f.KEY})
            d = pd.DataFrame(rows[1:], columns=rows[0]); d = d.loc[:, ~d.columns.duplicated()]
            d = d[d.state.isin(STATES)]
            d["geoid"] = d.state + d.county
            if d.geoid.duplicated().any(): raise ValueError(f"duplicate counties {t} {year}")
            d[["geoid", "NAME"] + [c for c in d.columns if c.startswith(t) and c[-1] in "EM"]].to_parquet(p, index=False)
            print(year, t, len(d), "counties", flush=True)

if __name__ == "__main__":
    main()
