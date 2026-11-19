# Status

Project: TractEconHealth
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: income-health-viz (paused at 2g; resumes 2026-11-20 morning)
Step: 2g
Since: 2026-11-19

Also open: Step 1 for the community spotlight series (10 neighborhoods: 5 urban, 5 rural)

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-11-19 | |
| 2a | Draft with brackets resolved | 2026-11-19 | |
| 2b | Eric's edit, Claude's look-over | 2026-11-19 | |
| 2c | Slice markup | 2026-11-19 | |
| 2d | Hero 1680x1080 + alt text | 2026-11-19 | |
| 2e | SEO | 2026-11-19 | |
| 2f | Pushed to Prismic (draft) | 2026-11-19 | |
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
- 2026-11-15 Source coverage check done (DATASETS.md). Literature notes in analysis/literature.md. Eric chose median household income as the headline economic measure and asked for a tract/county switch; county view built from ACS county tables, PLACES 2025 county release and County Health Rankings counted deaths. Findings rewritten around income. Next: Claude's tie-out, then independent tie-out.
- 2026-11-15 Claude's tie-out done (TIEOUT.md, scripts/50_tieout.py): all built data and numbers match after fixes to one spread figure, the income margin of error (annotation codes had been counted) and nine wording items. ACS release date filled in (January 29, 2026). Next: independent tie-out.
- 2026-11-15 Independent tie-out done: all data values, counts and statistics match. Fixed its display and wording findings (county name encoding, Census caps on income and rent share, median line, eight wording items, method lines clarified). Next: Eric confirms Step 1.
- 2026-11-19 Step 1 confirmed by Eric. Step 2a opened: slug income-health-viz, standard visualization post (layout of disease-vaccination-viz and substance-use-treatment-viz). Eric drafts Purpose; Claude drafted the other sections.
- 2026-11-19 Step 2a confirmed by Eric (Purpose drafted by Claude at Eric's request; index section, life expectancy chart, Read this first box with checks and outside research; Dwyer-Lindgren 60% confirmed). Step 2b opened: Eric edits POST.md.
- 2026-11-19 Steps 2b-2e confirmed by Eric (look-over edits 1-9; embed 940px; hero from the chart at hero scale; SEO fields, three FAQ answers, fentanyl link). Step 2f opened.
- 2026-11-19 Pushed to Prismic as a draft in the Migration Release (document av8gzxEAACgAvhgm, 66 slices, 2 images). Tags and author empty. Awaiting Eric's check of 2f.
- 2026-11-19 During 2g: life expectancy chart line recolored to the dashboard's orange, pointer sentence and direct link to the county life expectancy view added under it, email chart linked to that view. Prismic draft updated in place (same document).

- 2026-11-19 During 2g: the 541 tracts at the Census income cap ($250,001) are no longer drawn in the hero or the interactive chart when income is on the axis; both say so; they stay in the correlation and the median line. Prismic draft updated.
- 2026-11-19 2f confirmed. 2g drafted (EMAIL.md), not yet confirmed.
- 2026-11-19 Eric paused income-health-viz at 2g (2g, 3, 4 resume tomorrow morning) and opened Step 1 for a follow-on series: 10 community spotlights, low income and poor health, 5 urban (week 1) and 5 rural (week 2). Screen at least 100 candidates, research each with subagents, look for compounding causes with a distinct story each; West Dayton is a must. Drop places whose tracts changed too much to compare over time. Present a top 10 with backups.
- 2026-11-19 Spotlight Phase A (screen) done: 11,207 qualifying tracts, 4,053 neighborhoods, 131 candidates (67 urban, 48 rural, 16 micropolitan; 101 pass the 1990 boundary test). Sources added to DATASETS.md: PLACES 2024 for KY/PA, RUCA 2020, 2020 tract boundaries, NHGIS 1970-2020 tract series and 1990-2010 crosswalk. Rural tract history starts in 1990; rural history before that will come from county data.
- 2026-11-19 Spotlight Phase B (triage) done: 13 agents researched all 131 candidates (analysis/spotlight/research/, triage.jsonl). Phase C started: 20 finalists (analysis/spotlight/finalists.csv), 10 deep-research agents, two each, with head-to-head calls for the Delta, coal and tribal slots.
- 2026-11-19 Spotlight Phase C: deep research back for 20 finalists (analysis/spotlight/deep/, deep.jsonl). Tract sets cleaned (prisons, jails, single housing complexes, other neighborhoods dropped; Watts rebuilt; Owsley both tracts) in final_sets.csv; history rerun to history_final.csv. Nubian Square (Boston) check still running.
- 2026-11-19 Spotlight Phase D: SPOTLIGHTS.md written (top 10, backups A-H, dropped finalists) for Eric's approve/reject by number.
