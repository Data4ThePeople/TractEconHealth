# Sourcing pass brief (shared by all sourcing agents)

Data 4 The People is publishing a 10-part "community spotlight" series. In each published story, every sentence about the neighborhood's history will link to a source, so readers can follow up on any part of it. Your job is to turn a researched timeline into one where every entry is backed by the best available source, and that source has actually been opened and checked.

## Input
- `analysis/spotlight/deep/<id>.md`: the timeline (section 2) and the "how the cuts compound" paragraph (section 3). Each entry has a source.
- `analysis/spotlight/source_quality.csv`: how many entries rest on strong vs. weak sources.
- All paths are under /Users/ericpachman/PycharmProjects/TractEconHealth.

## Source tiers
- **A:** primary or scholarly. Government records and reports, statutes, court opinions and dockets, federal data, academic articles and books, university archives and digital collections, Mapping Inequality, NHGIS.
- **B:** established reference or journalism. State history encyclopedias (TSHA, e-WV, Encyclopedia of Alabama, Mississippi Encyclopedia), newspapers, public radio.
- **Weak:** Wikipedia, blogs, wikis, sites with no named sourcing. A weak source may never be the only source for an entry.

## For every timeline entry, and every factual claim in section 3
1. **Weak or missing source:** go to the record behind it.
   - For a Wikipedia citation, fetch the Wikipedia page and read its reference for that claim. Then fetch that reference.
   - Good places to find the record: govinfo.gov, congress.gov, courtlistener.com, law.justia.com, archive.org, HathiTrust, Google Books, JSTOR stable pages, state archives and agency sites, university repositories, EPA, CDC, MSHA, EIA, FDIC and BLS.
2. **Tier A or B source:** open it and confirm it says what the entry says (date, number, wording). Fix the entry if it doesn't.
3. **Can't open the source** (paywall, newspaper archive, blocked site): write down the full citation (publication, date, headline, author, page) in the list for Eric to pull. Do not mark the claim confirmed.
4. **Nothing reliable found:** mark the entry DROP or REWORD, and suggest wording the sources do support.
5. **Prefer the original record over a write-up of it.** For example, use the court opinion rather than a news story about it, or the agency report rather than an encyclopedia summary. Keep a good secondary source as a second link when it reads better for a general reader.

WebSearch may be limited or out of budget in this session. If a search fails, work by fetching pages directly: Wikipedia references, known agency URLs, archive.org and Google Books. Don't stop because search is unavailable.

## Output: write `analysis/spotlight/sourced/<id>.md`

1. **A one-line summary.**
2. **A table:**

   `# | Date | Claim (as the source supports it) | Number | Source 1 (tier, title, publisher, date, page or section) | URL 1 | Source 2 (optional) | URL 2 | Status | Note`

   - Status is one of: VERIFIED (you opened it and it supports the claim), CHANGED (fixed to match the source; say what changed), PULL (needs Eric to pull a paywalled or archived item), REWORD, or DROP.
3. **Section 3 claims checked:** each sentence of the deep file's "how the cuts compound" paragraph, marked VERIFIED, CHANGED or UNSUPPORTED, with its source.
4. **For Eric to pull:** the full citation for each item, and which entry it would confirm.
5. **A counts line:** entries, how many rest on tier A, tier B, still weak, and PULL.

## Rules
- Do not edit the deep files. Do not invent numbers or citations.
- A source counts only if you actually fetched it and read the passage. Quote the key phrase (under 25 words) in the Note column for any number.
- Plain American English, no em dashes. No political commentary: describe what institutions, agencies, companies and courts did.

FINAL REPLY: one line of JSON per place, and nothing else:
{"id":"...","entries":N,"tier_A":N,"tier_B":N,"weak_left":N,"pull":N,"dropped_or_reworded":N,"biggest_change":"..."}
