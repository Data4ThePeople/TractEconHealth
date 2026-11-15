# TractEconHealth

A Data 4 The People project that compares income and other economic measures with physical and mental health
for U.S. census tracts and counties.

The analysis has been checked twice, once by an independent rebuild (`TIEOUT.md`). There is no published post or public page yet.

## What it shows

An interactive scatter plot (`dist/index.html`) with one dot per census tract (77,918) or county (2,948). Pick
any of 15 economic measures and any of 18 health measures, nationally or for one state. The chart opens on median
household income against a health index. In the county view it also offers three measures counted from death
records: life expectancy, drug overdose deaths and suicides.

Add `#county` to the page address to open the county view, and `&x=<measure>&y=<measure>` to pick measures, for
example `#county&y=life_expectancy`.

## What's in the repo

- `scripts/`: numbered scripts that fetch the data (`01`-`06`), build tract and county measures (`10`, `11`), run the
  analysis (`20`, `21`), build the viz (`30`) and check the sources (`40`).
- `src/template.html`: the viz page. The build script packs the data into it.
- `dist/index.html`: the built viz, one self-contained file.
- `analysis/`: results files and working notes.
- `DATASETS.md`: each source, its limits, how gaps are filled, and the full method.

## Data sources

- U.S. Census Bureau, American Community Survey 5-year estimates, 2020-2024 and 2015-2019, tracts and counties
- CDC, PLACES: Local Data for Better Health, 2025 release, tract and county data
- U.S. Census Bureau, 2020 census tract relationship file
- County Health Rankings & Roadmaps, University of Wisconsin Population Health Institute, March 2026 release

## How to rebuild

Needs Python 3.9+ with pandas, numpy, scipy, requests and pyarrow, plus a free Census API key in the environment
as `CENSUS_API_KEY`. Run the scripts in `scripts/` in number order. Raw downloads go to `data/raw/` and are not
committed.

## Method notes

- The health measures are CDC model estimates, not surveys of each tract. CDC builds them partly from poverty and
  population makeup, so part of the link between a place's income and its health estimate is built into the
  estimates. Life expectancy from death records is the check that does not depend on that model.
- Kentucky and Pennsylvania are left out because the 2025 PLACES release lacks most measures for them.
- Tracts and counties with fewer than 500 people, or where half or more of residents live in group quarters, are
  left out.
- Full details are in `DATASETS.md`.
