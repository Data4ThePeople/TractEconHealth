# Status

Project: TractEconHealth
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: none yet
Step: 1
Since: 2026-11-14

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | | |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |
| 3  | Social posts | | |
| 4a | Outreach list | | |
| 4b | Outreach drafts in Gmail | | |

## Stale

None.

## Log

- 2026-11-14 Step 1 opened.
- 2026-11-14 Topic: census-tract economic health vs. physical/mental health. ACS 2020-2024 5-year for economic measures; CDC PLACES for tract health measures; CDC WONDER overdose and suicide deaths for a county-level check. Aggregate index on each side (equal-weight average of percentile ranks), big scatter, then an interactive viz with measure pickers and a state filter. Eric's theory: health tracks economics at the low end up to a point, then scatters.
- 2026-11-14 Decisions accepted: labor force change via 2010-to-2020 tract crosswalk; overdose and suicide stay county-level (not in tract index); PLACES used with its modeling disclosed plus a county check; drop tracts under 500 people or mostly group quarters; food insecurity on the health side, SNAP on the economic side.
- 2026-11-14 Data pulled: ACS 2020-2024 and 2015-2019 tracts, PLACES 2025, tract relationship file, County Health Rankings March 2026 supplement (replaces CDC WONDER, whose API does not return counties). Kentucky and Pennsylvania lack PLACES 2025 health measures and drop out. First-pass findings in analysis/findings.md; draft viz in dist/index.html.
- 2026-11-15 Session moved from the desktop app to the IDE. Eric accepted all three open decisions: Kentucky and Pennsylvania left out (no 2024 fill); weak economic measures stay in the index; framing is "steepest at the bottom, still rising at the top." Viz dots made easier to see (opacity floor 5% to 10%, dark mode 1.8x). Next: source coverage check, tie-out, independent tie-out.
