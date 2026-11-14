"""ACS 5-year tables for every census tract (50 states + DC).
2020-2024 (vintage 2024): all economic tables. 2015-2019 (vintage 2019): B23025 only, for labor force change.
Saves one parquet per table and vintage with every estimate (E) and margin of error (M) column,
plus the variable labels so measures are built from labels, not hand-typed line numbers."""
import os, sys, time
import pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
from d4tp_env import get_key, load_env  # noqa: E402
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, STATES  # noqa: E402

load_env()
KEY = get_key("CENSUS_API_KEY")
TABLES = {2024: ["B01003", "B26001", "B19013", "C17002", "B23001", "B23025", "B25070", "B25071", "B25140",
                 "B22003", "C27007", "B27010", "B19057", "B19083", "B19301"],
          2019: ["B23025"]}

def get(url, params):
    msg = ""
    for i in range(8):
        try:
            r = requests.get(url, params=params, timeout=(30, 240))
            if r.status_code == 200:
                return r.json()
            msg = f"{r.status_code} {r.text[:300]}"
        except requests.RequestException as e:
            msg = str(e)
        print("retry", params.get("get"), params.get("in"), msg[:120], flush=True)
        time.sleep(10 * (i + 1))
    raise RuntimeError(f"{url} {params.get('get')} {params.get('in')}: {msg}")

def main():
    for year, tabs in TABLES.items():
        out = RAW / "acs" / str(year)
        out.mkdir(parents=True, exist_ok=True)
        base = f"https://api.census.gov/data/{year}/acs/acs5"
        for t in tabs:
            f = out / f"{t}.parquet"
            if f.exists():
                continue
            labels = requests.get(f"{base}/groups/{t}.json", timeout=60).json()["variables"]
            pd.DataFrame([{"var": k, "label": v["label"]} for k, v in labels.items()]).to_csv(out / f"{t}_labels.csv", index=False)
            frames = []
            tmp = out / "_state"
            tmp.mkdir(exist_ok=True)
            def one(st):
                c = tmp / f"{t}_{st}.parquet"
                if not c.exists():
                    rows = get(base, {"get": f"NAME,group({t})", "for": "tract:*", "in": f"state:{st}", "key": KEY})
                    d = pd.DataFrame(rows[1:], columns=rows[0])
                    d.loc[:, ~d.columns.duplicated()].to_parquet(c, index=False)
                return c
            with ThreadPoolExecutor(6) as ex:
                files = list(ex.map(one, STATES))
            frames = [pd.read_parquet(c) for c in files]
            df = pd.concat(frames, ignore_index=True)
            df = df.loc[:, ~df.columns.duplicated()]
            df["geoid"] = df["state"] + df["county"] + df["tract"]
            if df.geoid.duplicated().any():
                raise ValueError(f"duplicate tracts in {t} {year}")
            keep = ["geoid", "NAME"] + [c for c in df.columns if c.startswith(t) and c[-1] in "EM"]
            df[keep].to_parquet(f, index=False)
            print(year, t, len(df), "tracts", flush=True)

if __name__ == "__main__":
    main()
