# Stage 3C Design — Spatial Heterogeneity and Local Context

- Date: 2026-10-07
- Branch: `subway/preprocessing-pipeline`
- Design status: **HUMAN APPROVED 2026-10-07**
- Prerequisite: Stage 3B H1/H2 **HUMAN APPROVED 2026-10-07**
- Stage 3B result: four primary H1/H2 tests Holm-nonrejected; H1/H2 **NOT SUPPORTED under the frozen specification**
- Scope: Secondary 2 only
- This design does **not** reopen Stage 2 preprocessing or Stage 3B confirmatory specifications.

## 1. Research objective

Stage 3C addresses the remaining Secondary 2 question:

> “이러한 차이는 서울 내 역·행정동별로 어떻게 다르며, 지역의 고령인구와 기후대응 공간 조건과 어떤 관계가 있는가?”

The purpose is **not** to search for a statistically significant local result after the citywide Stage 3B result was not supported.

The purpose is:

1. describe whether station-level age-differential responses to hot/cold days are heterogeneous across Seoul;
2. test whether that heterogeneity is systematically associated with two pre-selected local-context variables:
   - administrative-dong senior population share;
   - observed climate-shelter supply per 10,000 residents.

A null moderation result is a valid outcome. Stage 3C must not tune thresholds, time windows, station subsets, or models to recover H1/H2.

## 2. Approved analysis architecture

Stage 3C uses a two-layer design.

### Layer A — station-level descriptive heterogeneity

For each of the 243 mapped/current-study-area stations, construct a daily boarding age ratio and estimate station-specific hot/cold coefficients.

Purpose:
- describe the distribution and geography of station-level coefficients;
- support maps and descriptive heterogeneity summaries.

Layer A is **not** a multiple-testing exercise.

Forbidden:
- station-level significance labels;
- counts of “significant stations”;
- top/bottom-10 significance rankings;
- choosing stations because their coefficients support the hypothesis;
- classifying stations as high-risk or low-risk from these coefficients alone.

### Layer B — pooled local-context moderation

Use the full 243-station daily panel in one pooled model.

Purpose:
- formally test whether station-level age-differential hot/cold responses vary systematically with:
  1. senior population share;
  2. observed climate-shelter supply per 10,000 residents.

This pooled moderation model is the Stage 3C primary inferential analysis.

## 3. Fixed study population and spatial coverage

Use only the already approved current Seoul mapped subset:

- 243 mapped station identities;
- 173 unique administrative dongs containing those stations;
- 426 total Seoul administrative dongs in the contextual spatial layers.

Do not reinterpret the 173 dongs as a representative sample of all 426 Seoul dongs.

Required wording:

> “현재 분석대상 243개 지하철역이 위치한 173개 행정동”

The existing station-to-dong strict mapping is authoritative for Stage 3C.

Do not:
- remap stations;
- use nearest-dong fallback;
- repair coordinates;
- assign unresolved/outside stations to Seoul dongs.

The 15 current-study-area-outside stations and the 16 Task5 unresolved spatial identities remain outside this analysis.

## 4. Transport outcome and common-valid support

Primary event remains **boarding only**, consistent with Stage 3B.

For every station-date, aggregate only cells satisfying the approved age-comparison validity rule.

The one current-Seoul `senior > total` cell remains unmodified and must be excluded from **both** senior and non-senior station-day aggregates.

For station (s), date (d):

[
R_{sd}=logleft(rac{Senior_{sd}}{NonSenior_{sd}}ight)
]

No pseudocount is allowed.

### Pre-fit zero-count gate

Before any Stage 3C model fit:

- inspect all 243 × 366 station-day boarding pairs;
- if either senior or non-senior count is zero for any required station-day, **BLOCK** the log-ratio design;
- do not add 0.5, 1, or any other arbitrary correction;
- do not silently drop zero-count station-days;
- return to human review for a count-based redesign.

This is a mathematical-definition gate, not a post-result specification change.

## 5. Extreme-temperature definitions

Reuse Stage 3B frozen definitions exactly.

Primary:
- Hot: `temperature_max >= 32.75°C` — 2024 Seoul ASOS108 empirical p90;
- Cold: `temperature_min <= -3.05°C` — empirical p10.

Sensitivity only:
- Severe hot: `temperature_max >= 33.675°C` — p95;
- Severe cold: `temperature_min <= -4.8°C` — p05.

Do not introduce additional temperature thresholds.

These are study-specific relative extremes, not official KMA heat-wave/cold-wave warning definitions.

Stage 3C does **not** reopen the 10–16 daytime hypothesis.

## 6. Local-context variables

Stage 3C uses exactly two primary contextual moderators.

### 6.1 Senior population share

Use the approved 2024 Q2 direct administrative-dong population product.

Variable:

[
SeniorPopulationShare_j
=
rac{Population65Plus_j}{PopulationTotal_j}
]

This is a **local-context attribute of the station’s administrative dong**.

It is not:
- the residence distribution of subway passengers;
- the age composition of station users;
- an individual-level characteristic.

### 6.2 Observed climate-shelter supply

Map the 412 prepared climate-shelter points to the validated 426 administrative-dong polygons using strict point-in-polygon.

For dong (j):

[
SheltersPer10k_j
=
rac{MappedShelterCount_j}{PopulationTotal_j}
	imes 10,000
]

Interpretation:

> observed climate-response-space supply condition

Do not automatically call it:
- “shelter shortage”;
- “policy blind spot”;
- “climate vulnerability”;
- “actual accessibility”.

The shelter source remains a snapshot with unresolved temporal-completeness limitations; it is not proven to be a complete 2024 census.

## 7. Shelter spatial-assignment contract

Use the validated administrative-dong geometry in EPSG:5179.

Shelter point rules:

1. validate finite coordinate values and the existing source CRS contract;
2. project to EPSG:5179;
3. assign only by strict within exactly one polygon;
4. if no strict match, inspect boundary touch;
5. record `ZERO_MATCH`, `BOUNDARY_POINT`, or `MULTIPLE_MATCH` explicitly;
6. do not buffer, snap, nudge, repair, nearest-join, or manually assign.

A dong with no mapped shelter receives **mapped shelter count = 0**.

However, unmapped/ambiguous shelter points are not converted into zero and must be quantified separately.

### Shelter mapping review gate

Before moderation fitting, report:

- source shelter point count;
- strict-mapped count;
- zero-match count;
- boundary-point count;
- multiple-match count;
- invalid-coordinate count if any;
- percentage mapped.

If any point is not uniquely mapped, preserve it as an exception and quantify the impact before fitting. A nonzero exception count is not automatically fatal, but unexpected CRS/schema failures are BLOCKING.

## 8. Nearest-shelter distance — descriptive only

For each of the 243 stations, calculate the straight-line distance in meters to the nearest observed shelter after both are represented in an approved projected CRS, using EPSG:5179 for consistency.

Variable:

[
NearestShelterDistanceM_s
]

Use only as descriptive spatial context.

Do not interpret it as:
- walking-network distance;
- travel time;
- actual accessibility;
- service adequacy.

It is not included in the primary moderation model.

## 9. Standardization of moderators

Primary inferential moderators are standardized before model fitting.

Standardization population:

- the **173 unique administrative dongs containing at least one of the 243 analyzed stations**;
- each dong receives equal weight exactly once.

Do not compute the z-score over 243 station rows because dongs with multiple stations would receive disproportionate weight.

For moderator (X_j):

[
Z_j = rac{X_j-ar X}{s_X}
]

where mean and sample standard deviation are calculated over the 173 unique dongs; use deterministic sample SD (`ddof=1`).

Then attach the standardized dong values back to the 243 stations.

Expected QA:
- unique-dong z-score mean approximately 0;
- unique-dong sample SD approximately 1;
- no missing or infinite moderator values.

## 10. Moderator collinearity gate

Before fitting the primary model, inspect the two moderators over the 173 unique station-containing dongs.

Required diagnostics:
- Pearson correlation;
- descriptive ranges;
- design-matrix rank after all frozen terms are constructed.

Do not remove one moderator simply because correlation is nonzero or “high”.

If the joint specification becomes rank-deficient or numerically unidentified:
- **BLOCK**;
- do not replace the joint model with whichever single-moderator model yields stronger results;
- return to human review.

Separate population-only or shelter-only regressions are not primary analyses.

## 11. Layer A model — descriptive station heterogeneity

For each station separately, fit the pre-specified descriptive model:

[
R_{sd}
=
alpha_s
+
eta_{hot,s}Hot_d
+
eta_{cold,s}Cold_d
+
Month_d
+
DOW_d
+
epsilon_{sd}
]

Because the regression is station-specific, the intercept is station-specific by construction.

Required station-level outputs:
- (eta_{hot,s});
- (eta_{cold,s});
- valid day count;
- station identity and ADM_CD.

Do not use station-level p-values or significance decisions in reporting.

Primary Layer A summaries:
- median;
- IQR;
- minimum;
- maximum;
- proportion positive;
- proportion negative;
- continuous spatial map.

Layer A answers:

> how heterogeneous are the descriptive station-level coefficients?

It does not answer:

> which individual station has a statistically significant causal effect?

## 12. Layer B primary model — joint spatial moderation

Primary outcome:

[
R_{sd}=log(Senior_{sd}/NonSenior_{sd})
]

Primary pooled specification:

[
R_{sd}
=
alpha_s
+
delta_d
+
eta_1(Hot_d	imes Z^{pop}_s)
+
eta_2(Cold_d	imes Z^{pop}_s)
+
eta_3(Hot_d	imes Z^{shelter}_s)
+
eta_4(Cold_d	imes Z^{shelter}_s)
+
Controls
+
epsilon_{sd}
]

where:

- (alpha_s): station fixed effects;
- (delta_d): date fixed effects.

Because station FE absorb time-invariant moderator main effects, do not separately estimate the moderator main effects.

Because date FE absorb citywide daily Hot/Cold main effects, do not separately estimate Hot/Cold main effects.

### Frozen differential calendar controls

To reduce confounding from location-specific seasonal and weekly age-composition structure, include:

- (Z^{pop}_s 	imes Month_d);
- (Z^{shelter}_s 	imes Month_d);
- (Z^{pop}_s 	imes DOW_d);
- (Z^{shelter}_s 	imes DOW_d).

These controls are frozen before Stage 3C results are inspected.

Do not drop them because a simpler model gives stronger moderation coefficients.

## 13. Primary estimands and interpretation

Exactly four primary moderation tests:

1. Hot × senior-population-share z-score;
2. Cold × senior-population-share z-score;
3. Hot × shelters-per-10k z-score;
4. Cold × shelters-per-10k z-score.

Interpretation example:

A positive Hot × population coefficient means that, under the model, stations located in dongs with a one-SD higher senior population share show a relatively more positive / less negative senior-vs-non-senior boarding ratio change on hot days.

It does **not** establish:
- why passengers traveled;
- passenger residence;
- causal local-context effects;
- that elderly residents themselves used that station;
- that shelters caused or prevented subway use.

## 14. Inference and covariance

Use OLS for the continuous station-day log-ratio outcome.

Primary covariance:

**two-way clustered standard errors**
- cluster dimension 1: `ADM_CD` — expected 173 clusters;
- cluster dimension 2: `date` — expected 366 clusters.

This aligns:
- local-context moderators with their administrative-dong grouping;
- extreme exposure/common day shocks with date grouping.

The primary estimand is a **station-weighted association** over the 243 analyzed stations.

Do not describe it as an equal-weight estimate over 173 dongs.

Implementation must verify that the statistical library’s two-way clustering is actually using both cluster dimensions and produces finite covariance/SE values.

## 15. Multiple testing

One primary family contains exactly four tests:

1. Hot × population;
2. Cold × population;
3. Hot × shelter supply;
4. Cold × shelter supply.

For all four report:
- coefficient;
- standard error;
- pointwise 95% CI;
- raw two-sided p-value;
- Holm-adjusted p-value;
- alpha = 0.05.

Do not omit non-significant or opposite-direction results.

Do not introduce one-sided tests.

## 16. Sensitivity analysis

Run one pre-specified sensitivity only:

- replace p90/p10 Hot/Cold indicators with Stage 3B p95/p05 severe definitions;
- keep the same outcome, same 243 stations, same two moderators, same FE, same controls, and same two-way clustering.

Sensitivity is not a new primary family.

Do not:
- add other thresholds;
- add alternative time windows;
- add extra regression families;
- use sensitivity-only significance to overwrite the primary conclusion.

## 17. Moran/LISA and exploratory spatial statistics

Do **not** run Moran’s I or LISA in Stage 3C.

Reason:
- Secondary 2 is already directly addressed by descriptive station heterogeneity and joint local-context moderation;
- adding cluster-search procedures would expand the question and multiple-testing burden;
- visually adjacent station coefficients must not be called a statistically significant spatial cluster without a dedicated spatial-autocorrelation design.

Moran/LISA can be a future extension only if separately justified and approved.

## 18. Decision rules

### Case A — descriptive heterogeneity + supported moderation

Allowed conclusion:

> Citywide H1/H2 were not supported, but the relative age response varies systematically with the specified local context.

### Case B — descriptive heterogeneity, moderation not supported

Allowed conclusion:

> Station-level coefficients vary descriptively, but the variation is not clearly or systematically associated with senior population share or observed shelter supply under the pre-specified model.

### Case C — limited descriptive heterogeneity + moderation not supported

Allowed conclusion:

> Evidence for age-differential extreme-temperature response is limited both citywide and across the tested local-context dimensions.

If a primary moderation coefficient is opposite to an expected vulnerability narrative, report that direction as estimated.

Do not automatically translate any coefficient into “more vulnerable”, “safer”, or “policy blind spot”.

## 19. Required figures

Limit Stage 3C to three report-oriented figures.

### Figure 1 — station hot/cold heterogeneity

One figure containing hot and cold station coefficients as paired panels.

- 243 station locations;
- continuous diverging scale centered at zero;
- same conceptual scale treatment for hot/cold where feasible;
- no significance marker;
- no top-10 annotation.

### Figure 2 — administrative-dong local context

One figure containing two panels:

- raw `senior_population_share`;
- raw `shelters_per_10k`.

Display all 426 dongs for geographic context, while clearly distinguishing the 173 dongs containing analyzed stations.

The regression z-scores remain based only on the 173 unique station-containing dongs.

### Figure 3 — primary moderation effects

Display the four primary moderation estimates with pointwise 95% CI and zero reference.

Caption must state:
- OLS station-day log ratio;
- station/date FE;
- moderator×month/DOW controls;
- ADM_CD/date two-way clustered SE;
- Holm applies to p-values, while displayed 95% CI are pointwise unless simultaneous intervals are explicitly implemented.

## 20. Expected artifacts

Suggested Stage 3C outputs:

### Tables/data

`subway/results/tables/spatial_context_2024.csv`
- 426 dong raw contextual values;
- population;
- mapped shelter count;
- shelters_per_10k;
- station-presence indicator;
- shelter-mapping provenance/QA fields where appropriate.

`subway/results/tables/station_spatial_context_2024.csv`
- 243 stations;
- ADM_CD;
- raw and standardized moderators;
- nearest_shelter_distance_m;
- existing mapping identity/provenance fields needed for audit.

`subway/results/tables/station_extreme_heterogeneity.csv`
- station hot/cold Layer A coefficients;
- valid-day count;
- no significance classification.

### Models

`subway/results/models/spatial_moderation_primary.csv`

`subway/results/models/spatial_moderation_sensitivity.csv`

`subway/results/models/spatial_moderation_summary.json`

### Figures

`subway/results/figures/station_extreme_heterogeneity.png`

`subway/results/figures/spatial_context.png`

`subway/results/figures/spatial_moderation_effects.png`

### Documentation

`subway/docs/analysis/11-spatial-heterogeneity.md`

Update report-map, methodology-log, and AI-usage-log minimally after execution and review.

## 21. Pre-fit QA gates

Before any Stage 3C primary model fit, all of the following must pass:

1. 243 current-study-area mapped station identities are present exactly once in station context.
2. Their unique ADM_CD count is 173.
3. station-day boarding aggregation has the expected complete date coverage unless a documented source exception explains otherwise.
4. senior and non-senior paired station-day counts are strictly positive.
5. common-valid support excludes the senior>total cell from both age groups.
6. every analyzed station has exactly one ADM_CD.
7. shelter source count and strict mapping statuses are fully accounted.
8. population total is positive for all required station-containing dongs.
9. `shelters_per_10k` is finite for all 173 required dongs.
10. z-scores are computed on 173 unique dongs, not repeated station rows.
11. z-score mean≈0 and sample SD≈1 for each moderator.
12. moderator correlation is reported.
13. primary design matrix is full rank.
14. all four primary interaction columns exist.
15. station FE and date FE are present.
16. frozen moderator×month and moderator×DOW controls are present.
17. two-way cluster groups are exactly ADM_CD and date.
18. covariance and reported inferential quantities are finite.
19. Stage 2, Stage 3A, and Stage 3B accepted inputs/artifacts remain unchanged.
20. no network dependency and no absolute local path enters deterministic artifacts.

Any scientific-specification failure returns to human review instead of silent substitution.

## 22. Implementation boundaries

Prefer a focused Stage 3C analysis module and runner reusing approved Stage 2/3A data contracts.

Do not refactor unrelated preprocessing code.

Do not alter:
- Stage 2 raw/clean/processed contracts;
- Stage 3B confirmatory thresholds;
- H1/H2 results;
- station-dong authority decisions.

No new external dataset is required.

No holiday data, 2023/2025 ridership, regional data, ML model, or congestion dataset is added in this Stage.

## 23. Stage 3C stop condition

Stage 3C ends after:

1. shelter/context construction and QA;
2. Layer A descriptive station heterogeneity;
3. Layer B joint primary moderation;
4. p95/p05 sensitivity;
5. three figures;
6. result documentation and human review.

Then STOP.

Do not automatically begin:
- Moran/LISA;
- 10–16 spatial interactions;
- additional thresholds;
- station significance mining;
- policy recommendations;
- final report drafting.

## 24. Success criteria

Stage 3C is successful when it provides a reproducible answer to Secondary 2 regardless of statistical significance:

- the citywide Stage 3B null/uncertain result is preserved honestly;
- station heterogeneity is described without significance hunting;
- the two pre-selected local-context variables are tested jointly;
- inference respects the dong- and date-level dependence structure;
- all four moderation tests and sensitivity results are reported;
- shelter limitations and passenger-residence limitations remain explicit;
- results can be compressed into the contest report without overstating causality or policy effects.
