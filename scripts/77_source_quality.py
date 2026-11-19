"""Grade the sources behind each finalist's timeline (analysis/spotlight/deep/<id>.md, section 2).

Each source link gets a tier:
  A  primary or scholarly: government records and data, court records, laws, academic papers and university
     archives or encyclopedias, federal research reports, NHGIS, Mapping Inequality.
  B  established reference or journalism: state history encyclopedias, newspapers, public radio, and named
     nonprofits and trade press.
  C  weak: Wikipedia, blogs, wikis, partisan or advocacy sites with no named sourcing.
A timeline entry takes the best tier among its links. Output: analysis/spotlight/source_quality.csv
"""
import re, glob, sys
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT

A_SUFFIX = (".gov", ".edu", ".mil", ".us")
A = {"dsl.richmond.edu", "nhgis.org", "nber.org", "everycrsreport.com", "law.cornell.edu", "law.justia.com", "case-law.vlex.com",
     "clearinghouse.net", "tarlton.law.utexas.edu", "pmc.ncbi.nlm.nih.gov", "muse.jhu.edu", "degruyterbrill.com", "ejournals.bc.edu",
     "eh.net", "fraser.stlouisfed.org", "bostonfed.org", "federalreservehistory.org", "collections.leventhalmap.org",
     "healthdata.org", "shepscenter.unc.edu", "countyhealthrankings.org", "educationdata.urban.org", "bostonhousing.org",
     "bostonplans.org", "archives.gov", "case.edu", "encyclopedia.chicagohistory.org", "plainshumanities.unl.edu"}
C = {"en.wikipedia.org", "en.wikipedia.com", "wsws.org", "daytonvistas.com", "bhamwiki.com", "coyotegulch.blog",
     "turtletalk.files.wordpress.com", "github.com", "reason.com", "criminallegalnews.org"}

def tier(u):
    d = urlparse(u).netloc.lower().removeprefix("www.")
    if d in C: return "C"
    if d in A or d.endswith(A_SUFFIX): return "A"
    return "B"

rows = []
for f in sorted(glob.glob(str(ROOT / "analysis/spotlight/deep/*.md"))):
    cid = Path(f).stem
    s = open(f).read()
    tl = re.search(r"## 2\.?.*?\n(.*?)\n## 3", s, re.S).group(1)
    lines = tl.splitlines()
    table = [l for l in lines if l.startswith("|") and not l.startswith("|---")][1:]  # drop header row
    listed = [l for l in lines if re.match(r"\d+\.\s", l)]
    entries = table if len(table) >= len(listed) else listed
    # rows that say "(above)" point back to an earlier link: match on the earlier link's text or domain words
    named = {}
    for txt, u in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", s):
        named[txt.lower()[:20]] = u
    for u in re.findall(r"https?://[^\s|)\];,]+", s):
        d = urlparse(u).netloc.lower().removeprefix("www.")
        named.setdefault(d.split(".")[0], u)
    best = []
    unconf = 0
    for e in entries:
        urls = re.findall(r"https?://[^\s|)\];,]+", e)
        if not urls:
            el = e.lower()
            urls = [u for k, u in named.items() if len(k) >= 5 and k in el]
        t = min((tier(u) for u in urls), default="none")
        best.append(t); unconf += "UNCONFIRMED" in e
    n = len(entries)
    rows.append(dict(cand_id=cid, entries=n, A=best.count("A"), B=best.count("B"), C_only=best.count("C"), no_link=best.count("none"),
                     unconfirmed=unconf, pct_A=round(100 * best.count("A") / n), pct_A_or_B=round(100 * (best.count("A") + best.count("B")) / n),
                     pct_wiki_or_weak_only=round(100 * (best.count("C") + best.count("none")) / n)))
q = pd.DataFrame(rows).sort_values(["pct_A_or_B", "pct_A"], ascending=False)
q.to_csv(ROOT / "analysis/spotlight/source_quality.csv", index=False)
print(q.to_string(index=False))
