# Findings (updated November 15, 2026)

Every number here comes from `analysis/results.json`, `analysis/county_results.json`, `analysis/binned.csv`,
`analysis/income_binned.csv`, `analysis/by_state.csv`, `analysis/corr_matrix.csv` and `analysis/coverage.json`.
Not yet tied out.

## The theory

Health tracks economic health closely at the low end, up to a point, and above that point the relationship turns
into scatter.

## Headline measure

Median household income, chosen by Eric on November 15. The economic index is kept in the viz as a second view.

## What the data show (tracts)

**1. The link is strong.** Across 77,708 tracts with a published median household income, the rank correlation
between income and the health index is 0.82. For the 12-measure economic index it is 0.71.

**2. Health improves fastest at the low end.** By median household income (20 equal groups of about 3,900 tracts):

| Income group (median) | Obesity | Diabetes | Smoking | Frequent mental distress |
|---|---|---|---|---|
| $30,867 | 45.8% | 20.2% | 22.7% | 21.8% |
| $56,417 | 38.2% | 14.2% | 16.5% | 18.5% |
| $75,973 | 34.6% | 12.1% | 13.6% | 17.0% |
| $102,174 | 30.7% | 10.5% | 10.9% | 15.6% |
| $197,000 | 23.6% | 8.6% | 6.8% | 12.5% |

Going from about $31,000 to about $56,000 cuts the middle tract's diabetes rate by 6 points. Going from about
$102,000 to about $197,000 cuts it by 2 points.

**3. With income on the x-axis, there is a bend, at about $110,000.** A line with one bend fits better than a
straight line (share of variation explained 67.1% against 60.3%). Resampling puts the bend between about $109,000
and $112,000. Below it, the health index rises 0.66 points per $1,000 of income; above it, 0.18 points, about 27%
of the lower rate. A straight line on the log of income explains 65.2%, close to the bent line, so the shape is a
steady flattening and the bend is a summary of it, not a threshold.

**4. Health keeps improving above the bend, and the spread narrows rather than widens.** This is where the data
part from the theory. Above $110,000 the rank correlation is 0.57 (0.71 below). The spread around the line is
smaller above the bend (middle half of tracts within 12.5 index points of the line, against 18.6 below). By
income group, the health index spread between the 10th and 90th percentile tract is 26 points in the lowest group,
about 40 points in the middle (around $79,000) and 13 points in the highest. Some of the narrowing at the top comes
from the index nearing its ceiling of 100. Obesity, which has no ceiling issue, shows the same thing: 18.4 points
between the 10th and 90th percentile tract in the lowest income group, 11.3 in the highest.

**5. Every state shows the same pattern.** Rank correlations run from 0.55 (North Dakota) to 0.86 (New Jersey). In
the 45 states with enough tracts to fit a bend, health still rises above the bend in all 45, at a median of 29% of
the rate below it. The bend adds a median 3.9 points of explained variation, most in Connecticut (11.9), Colorado
(10.0) and New Jersey (9.8), least in North Dakota (0.4), Mississippi (0.6) and Arkansas (0.7).

**6. Which economic measures go with health.** Rank correlation with the health index: income per person 0.82,
median household income 0.82, share above 200% of poverty 0.80, Medicaid share -0.69, SNAP share -0.68, uninsured
-0.48, prime-age participation 0.50. Weak: unemployment -0.26, public assistance -0.21, housing cost burden -0.11,
median rent share -0.10, labor force change 0.10.

## Counties

County view: 2,948 counties, ACS county income and CDC's own PLACES county estimates.

| County health measure | Rank correlation with median household income | With economic index |
|---|---|---|
| Health index (PLACES, modeled) | 0.82 | 0.70 |
| Life expectancy (counted deaths) | 0.73 | 0.70 |
| Drug overdose deaths | -0.25 | -0.33 |
| Suicides | -0.31 | -0.16 |

Life expectancy comes from death records, not the PLACES model, and income tracks it nearly as closely as the
modeled index. Overdose deaths and suicides follow county income much more loosely. Overdose rates are crude rates
and partly reflect each county's age mix.

## Why the PLACES model matters here

CDC builds tract health estimates from each area's age, sex, race and ethnicity, and education, plus county poverty
in the model fit and tract poverty at the prediction step (CDC FAQ, December 2025). So part of the tract link
between income and health is built into the estimates. CDC's own methods staff say so in print (Kong and Zhang,
2020; see `analysis/literature.md`). Two more signs:

- Within counties, the rank correlation is 0.74 for income and 0.79 for the economic index. Within a county, the
  model's tract differences come only from those demographic and poverty inputs.
- The economic measures most tied to poverty (income, share above 200% of poverty, SNAP, Medicaid) are the ones
  most tied to the health estimates. Measures the model does not use (housing cost burden, labor force change) show
  little link.

The county life expectancy result is the check that the link is not only a product of the model.

## Data quality (from the source coverage check in DATASETS.md)

- No tract health value is a direct measurement. The typical tract's obesity estimate has a 95% interval about 10
  points wide.
- The Census Bureau filled in some or all income for 37.8% of households (41.3% in the lowest-income fifth of
  tracts, 33.9% in the highest).
- The typical tract's income margin of error is 20.5% of the estimate (27.4% in the lowest-income fifth). Some of
  the spread among low-income tracts comes from this noise rather than from health.

## Published research

See `analysis/literature.md`. No published tract-level correlation between income and PLACES was found. Chetty et
al. (JAMA, 2016) find the income and life expectancy link is steepest at low incomes and continues all the way up,
which matches finding 3 and 4 here.

## Decisions (November 15, 2026, accepted by Eric)

1. Kentucky and Pennsylvania stay out, and the post says so. No fill from the 2024 PLACES release.
2. Housing cost burden, median rent share and labor force change stay in the economic index.
3. Framing: "steepest at the bottom, still rising at the top."
4. Headline economic measure: median household income. Viz gets a tract/county switch.
