# Subway Stage 3C Spatial Heterogeneity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce Stage 3C Secondary 2 analysis: descriptive station-level hot/cold heterogeneity plus a pre-specified joint local-context moderation model using senior-population share and observed climate-shelter supply.

**Architecture:** Add one focused Stage 3C analysis module, one figure module, one runner, and one frozen config. The runner reads only accepted Stage 2/3A products, verifies Stage 3B threshold continuity, constructs 426-dong and 243-station context, builds a complete station-day log-ratio panel, runs Layer A descriptive station regressions and Layer B joint moderation with two-way clustered inference, then stages deterministic tables/models/figures. Existing preprocessing and Stage 3B outputs remain read-only.

**Tech Stack:** Python 3.11; pandas/numpy/pyarrow; GeoPandas/Shapely/pyproj already used by Stage 2; statsmodels 0.15.0; matplotlib 3.10.7; no new external data or network dependency.

**Spec:** `docs/superpowers/specs/2026-10-07-subway-spatial-heterogeneity-design.md`

## Global Constraints

- Current empirical scope: the already approved 243 mapped Seoul stations in 173 unique administrative dongs.
- Boarding only; common-valid age cells only; the current-Seoul senior>total cell is excluded from both age aggregates without changing raw values.
- Primary extremes remain exactly hot `temperature_max >= 32.75` and cold `temperature_min <= -3.05`; sensitivity only uses 33.675 / -4.8.
- No 10–16 spatial re-analysis, no new threshold, no Moran/LISA, no station significance mining, no policy recommendation.
- Primary contextual moderators are exactly `senior_population_share` and `shelters_per_10k`, fitted jointly.
- Moderator z-scores use 173 unique station-containing dongs once each, sample SD `ddof=1`.
- Shelter assignment is strict point-in-polygon after CRS validation; no buffer, snap, nearest-dong fallback, geometry repair, coordinate replacement, or manual assignment.
- `nearest_shelter_distance_m` is descriptive only and uses coordinate-valid observed shelter points in EPSG:5179 regardless of whether a point has a unique dong assignment; invalid-coordinate shelters are excluded from distance computation and remain explicit exceptions.
- Primary model: station/date fixed effects, four frozen extreme×moderator terms, moderator×month and moderator×DOW controls, OLS on station-day log ratio.
- Calendar interaction coding uses sorted categories with January (month=1) and Monday (DOW=0) as reference levels; this is frozen before results.
- Fixed effects are absorbed by balanced-panel two-way demeaning to avoid a dense 600+ column dummy matrix; equivalence to an explicit FE fit is pinned by fixture tests.
- Two-way clustered covariance uses `statsmodels.stats.sandwich_covariance.cov_cluster_2groups(..., use_correction=False)` on ADM_CD and date. Report normal-reference two-sided p-values and pointwise 95% CIs; Holm adjusts only the four primary p-values.
- No pseudocount, silent zero-day dropping, single-moderator fallback, or result-dependent model simplification.
- Stage 2, Stage 3A, and Stage 3B accepted artifacts are immutable; runner records and rechecks hashes before publication.
- All deterministic outputs are staged before replace; runtime failures write logs and return nonzero without publishing a partial successful result.

## File Structure

- Create `subway/config/spatial_heterogeneity_2024.yaml` — frozen Stage 3C scientific/configuration contract and Stage 3B threshold continuity.
- Create `subway/src/analysis/spatial_heterogeneity.py` — config validation, shelter/context construction, station-day panel, Layer A, Layer B design/inference, Holm family and summary helpers.
- Create `subway/src/analysis/spatial_figures.py` — exactly three Stage 3C report figures.
- Create `subway/run_spatial_heterogeneity.py` — prior-stage hash gates, actual-data orchestration, deterministic staging/publication and runtime logging.
- Create `subway/tests/test_spatial_heterogeneity.py` — pure scientific-contract tests and runner fixture tests.
- Create after successful execution: `subway/docs/analysis/11-spatial-heterogeneity.md`.
- Modify after successful execution: `subway/docs/analysis/00-report-map.md`, `subway/docs/analysis/methodology-log.md`, `subway/docs/analysis/ai-usage-log.md`.
- Produce tables/models/figures named in the approved spec, plus `subway/results/tables/shelter_mapping_exceptions.csv` as the explicit audit table for non-unique/invalid shelter mappings.

## Review Focus

1. **Shelter exceptions must not become false zero supply.** A ZERO_MATCH/BOUNDARY_POINT/MULTIPLE_MATCH/invalid shelter is excluded from a dong’s mapped count, preserved in `shelter_mapping_exceptions.csv`, and included in mapping QA totals; only a dong with zero uniquely mapped shelters receives count 0.
2. **Moderator standardization must not overweight multi-station dongs.** Tests must show z-scores are calculated from 173 unique ADM_CD rows and then repeated onto stations, with mean≈0 and sample SD≈1 at unique-dong level.
3. **Station-day zero counts must fail closed.** Any senior or non-senior station-day count of 0 raises before Layer A/Layer B fitting; no row drop or pseudocount is permitted.
4. **Fixed-effect and covariance implementation must match the approved model.** Fixture tests compare absorbed-FE coefficients to an explicit dummy-FE OLS on a small balanced panel and compare the returned two-way covariance to `cov_cluster_2groups` using ADM_CD/date.
5. **Accepted prior-stage bytes must not drift.** Runner tests alter one Stage 2/3A/3B dependency hash/status and require nonzero failure before result publication; successful fixture execution must leave those inputs byte-identical.

---

### Task 1: Freeze Stage 3C contract and build spatial context

**Files:**
- Create: `subway/config/spatial_heterogeneity_2024.yaml`
- Create: `subway/src/analysis/spatial_heterogeneity.py`
- Create: `subway/tests/test_spatial_heterogeneity.py`

**Interfaces:**
- Produces: `load_spatial_heterogeneity_config(repo_root: Path, year: int) -> dict[str, Any]`
- Produces: `validate_spatial_heterogeneity_config(profile: dict[str, Any], year: int) -> dict[str, Any]`
- Produces: `build_spatial_context(station_map: pd.DataFrame, population_boundary: gpd.GeoDataFrame, shelters: gpd.GeoDataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]`
- Returns from `build_spatial_context`: 426-row dong context, 243-row station context, shelter exception table, QA metadata.

- [ ] **Step 1: Write failing config-contract tests**

Test names/assertions:
- `test_stage3c_config_freezes_scope_thresholds_model_and_family`: exact 243/173/426 expectations, four threshold values, boarding event, two moderators, Holm alpha=.05, two cluster dimensions, sensitivity only p95/p05.
- `test_stage3c_config_drift_fails_closed`: changing any threshold, adding a moderator, changing cluster correction, enabling daytime/Moran must raise `ValueError`.
- `test_stage3b_threshold_continuity_is_exact`: values in the Stage 3C config must equal the existing confirmatory config.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:
`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: FAIL because Stage 3C config/module does not exist.

- [ ] **Step 3: Implement the frozen YAML and config validator**

The YAML must record:
- reference year/study area;
- Stage 3B approval date and spec path;
- exact primary/sensitivity thresholds and operators;
- boarding/common-valid contract;
- expected 243 stations / 173 station dongs / 426 Seoul dongs;
- two moderators and 173-dong z-score rule with `ddof=1`;
- OLS log-ratio, station/date FE, moderator×month/DOW controls;
- ADM_CD/date two-way clustering, `use_correction=false`;
- exact four-test family + Holm .05;
- Layer A descriptive-only and Moran/daytime/policy flags false.

- [ ] **Step 4: Write failing spatial-context tests**

Cover:
- exactly current-study-area `MAPPED` stations enter the 243-row context;
- same-dong multiple stations do not duplicate the z-score population;
- strict shelter within/touch/zero/multiple behavior;
- invalid shelter coordinate/CRS fails or remains explicit according to source contract;
- a dong with no uniquely mapped shelter gets mapped count 0;
- an unmapped shelter does not create a false mapped count;
- `shelters_per_10k = mapped_shelter_count / population_total * 10000`;
- nonpositive population blocks required context;
- z-score unique-dong mean≈0 / sample SD≈1 and zero-variance moderator blocks;
- nearest distance uses all coordinate-valid observed shelters in EPSG:5179 and is not affected by PIP status;
- input frames remain unchanged and reversed input order returns byte-equivalent sorted tables.

- [ ] **Step 5: Implement `build_spatial_context(...)` minimally**

Use the approved `station_dong_map` mapping, the 426-row population-boundary GeoDataFrame, and clean shelter GeoDataFrame. Do not call Stage 2 transforms to remap stations.

Output schemas must include:
- dong context: `ADM_CD, gu, dong, population_total, population_65_plus, senior_population_share, mapped_shelter_count, shelters_per_10k, has_analyzed_station, analyzed_station_count`;
- station context: station identity/name/line, ADM_CD, x_5179/y_5179, raw moderator values, `z_senior_population_share, z_shelters_per_10k, nearest_shelter_distance_m`;
- shelter exceptions: shelter identity/source row, mapping status/reason and projected coordinates when valid;
- QA metadata with total/mapped/zero/touch/multiple/invalid counts and mapping percentage.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:
`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: all Task 1 tests PASS.

- [ ] **Step 7: Commit Task 1**

`git add subway/config/spatial_heterogeneity_2024.yaml subway/src/analysis/spatial_heterogeneity.py subway/tests/test_spatial_heterogeneity.py`

`git commit -m "feat: build subway spatial context contract"`

---

### Task 2: Build the station-day panel and Layer A descriptive heterogeneity

**Files:**
- Modify: `subway/src/analysis/spatial_heterogeneity.py`
- Modify: `subway/tests/test_spatial_heterogeneity.py`

**Interfaces:**
- Consumes: Task 1 station context and frozen config.
- Produces: `build_station_day_panel(base: pd.DataFrame, station_context: pd.DataFrame, config: dict[str, Any], year: int) -> pd.DataFrame`
- Produces: `fit_station_heterogeneity(panel: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: Write failing station-day panel tests**

Assertions:
- boarding only;
- common-valid support excludes an invalid senior>total source cell from both age totals;
- expected balanced key `canonical_station_id × date`;
- synthetic expected row count equals stations×dates and every station has every date;
- aggregated senior/non-senior equal independent source sums;
- month/DOW and four frozen extreme indicators match weather/date inputs;
- station context joins many-to-one with no missing ADM_CD/moderator values;
- any zero senior/non-senior daily count raises;
- duplicate station/date/context key or missing day raises;
- no source frame mutation.

- [ ] **Step 2: Run the new panel tests and verify RED**

Run the exact new test class/methods with unittest; expected failure is missing `build_station_day_panel`.

- [ ] **Step 3: Implement `build_station_day_panel(...)`**

Aggregate valid boarding cells by station/date, retain `support_cells`, require strict positive paired counts, compute `log_ratio = log(senior/non_senior)`, attach context, and validate a balanced 243×366 actual-data contract without filling absent days.

- [ ] **Step 4: Write failing Layer A tests**

Use a deterministic multi-station annual fixture with known hot/cold coefficients. Assert:
- exactly one output row per station;
- columns contain hot/cold coefficient and valid-day count only for inference purposes;
- no station significance/reject field is emitted;
- month/DOW controls use sorted reference coding;
- design rank failure raises;
- coefficient estimates match direct explicit OLS on the fixture.

- [ ] **Step 5: Implement `fit_station_heterogeneity(...)`**

For each station fit:
`log_ratio ~ hot_primary + cold_primary + month FE + DOW FE`.

Use deterministic sorted month/DOW dummies and full-rank check. Return coefficient estimates and descriptive metadata; do not calculate or serialize station-level significance decisions.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:
`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: all Task 1–2 tests PASS.

- [ ] **Step 7: Commit Task 2**

`git add subway/src/analysis/spatial_heterogeneity.py subway/tests/test_spatial_heterogeneity.py`

`git commit -m "feat: add station extreme heterogeneity layer"`

---

### Task 3: Implement the joint moderation model, two-way clustered inference, and sensitivity

**Files:**
- Modify: `subway/src/analysis/spatial_heterogeneity.py`
- Modify: `subway/tests/test_spatial_heterogeneity.py`

**Interfaces:**
- Consumes: Task 2 balanced station-day panel.
- Produces: `design_spatial_moderation(panel: pd.DataFrame, *, hot: str, cold: str) -> pd.DataFrame`
- Produces: `absorb_station_date_fe(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame`
- Produces: `fit_spatial_moderation(panel: pd.DataFrame, *, hot: str, cold: str, threshold_label: str) -> tuple[pd.DataFrame, dict[str, Any]]`
- Produces: `fit_stage3c_models(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]` returning primary four-test table, p95/p05 sensitivity table, model metadata.

- [ ] **Step 1: Write failing design-matrix tests**

Assert exact primary terms:
- `hot_x_z_senior_population_share`;
- `cold_x_z_senior_population_share`;
- `hot_x_z_shelters_per_10k`;
- `cold_x_z_shelters_per_10k`.

Assert frozen controls:
- each moderator × months 2..12;
- each moderator × DOW 1..6;
- no standalone moderator, hot/cold, daytime, nearest-distance, or Moran term;
- full rank on fixture;
- deliberate moderator duplication/rank deficiency raises.

- [ ] **Step 2: Write failing fixed-effect equivalence test**

On a small balanced panel, compare `absorb_station_date_fe` + OLS coefficients against an explicit `C(station)+C(date)` dummy-FE OLS for all moderation/control slopes to tight numerical tolerance.

This pins the memory-efficient implementation to the approved station/date FE model.

- [ ] **Step 3: Implement design construction and balanced-panel FE absorption**

Use double demeaning:
`x_sd - mean_s(x) - mean_d(x) + grand_mean(x)`
for the outcome and each slope/control column. Require balanced station×date keys before absorption.

- [ ] **Step 4: Write failing two-way covariance and four-test-family tests**

Assertions:
- `cov_cluster_2groups(..., use_correction=False)` is called/equivalent for ADM_CD and date groups;
- ADM_CD/date unique cluster counts match fixture expectations;
- nonfinite or nonpositive primary variances block;
- estimate/SE/pointwise CI/two-sided normal p are finite;
- exactly four primary hypotheses are emitted;
- Holm-adjusted p-values are monotone and never smaller than raw p;
- primary family does not include sensitivity rows;
- reversing panel rows produces identical sorted results.

- [ ] **Step 5: Implement `fit_spatial_moderation(...)`**

Fit OLS on the FE-absorbed outcome/design. Obtain two-way cluster covariance with `cov_cluster_2groups(result, ADM_CD, date, use_correction=False)`. Compute SE from the combined covariance diagonal, pointwise 95% CI using 1.959963984540054, and two-sided normal p with `math.erfc(abs(z)/sqrt(2))`.

Report coefficients on the log-ratio scale; do not relabel them as count IRRs.

- [ ] **Step 6: Write failing p95/p05 sensitivity test**

The sensitivity run must change only the hot/cold indicator columns to the frozen severe definitions. Assert identical sample, moderators, controls, FE absorption, cluster groups and model row count. Assert no extra thresholds or time-window models exist.

- [ ] **Step 7: Implement `fit_stage3c_models(...)`**

Run primary p90/p10 and sensitivity p95/p05. Reuse the existing `holm_adjust` helper from `subway.src.analysis.confirmatory` for the four primary p-values only.

Metadata must include:
- nobs;
- 243 stations / 173 ADM_CD / 366 dates expected on actual data;
- slope design rank/columns;
- cluster counts;
- covariance method and `use_correction=false`;
- four-test family count;
- threshold-changed-after-results=false;
- daytime-spatial-analysis=false;
- Moran/LISA=false;
- station-significance-mining=false.

- [ ] **Step 8: Run focused tests and verify GREEN**

Run:
`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: all Task 1–3 tests PASS.

- [ ] **Step 9: Commit Task 3**

`git add subway/src/analysis/spatial_heterogeneity.py subway/tests/test_spatial_heterogeneity.py`

`git commit -m "feat: add subway spatial moderation inference"`

---

### Task 4: Add deterministic figures, runner, and actual Stage 3C artifacts

**Files:**
- Create: `subway/src/analysis/spatial_figures.py`
- Create: `subway/run_spatial_heterogeneity.py`
- Modify: `subway/tests/test_spatial_heterogeneity.py`
- Produce: `subway/results/tables/spatial_context_2024.csv`
- Produce: `subway/results/tables/station_spatial_context_2024.csv`
- Produce: `subway/results/tables/shelter_mapping_exceptions.csv`
- Produce: `subway/results/tables/station_extreme_heterogeneity.csv`
- Produce: `subway/results/models/spatial_moderation_primary.csv`
- Produce: `subway/results/models/spatial_moderation_sensitivity.csv`
- Produce: `subway/results/models/spatial_moderation_summary.json`
- Produce three figures from the approved spec.

**Interfaces:**
- Produces: `render_spatial_figures(dong_context: gpd.GeoDataFrame, station_context: pd.DataFrame, heterogeneity: pd.DataFrame, primary: pd.DataFrame, output_dir: Path) -> list[str]`
- Produces: `run_spatial_heterogeneity(repo_root: Path, year: int) -> int`
- Produces: CLI `python subway/run_spatial_heterogeneity.py --year 2024`.

- [ ] **Step 1: Write failing figure-contract tests**

Using small GeoDataFrames, assert exactly:
- `station_extreme_heterogeneity.png`;
- `spatial_context.png`;
- `spatial_moderation_effects.png`.

Inspect figure input contracts rather than pixel colors:
- station map receives both hot/cold coefficients and uses one common symmetric absolute limit;
- context figure receives all dongs plus `has_analyzed_station`;
- moderation plot contains exactly four primary rows and zero reference;
- no station significance flag is required or accepted.

- [ ] **Step 2: Implement `spatial_figures.py`**

Figure 1: paired hot/cold station panels, continuous scale centered at zero, no significance/rank labels.

Figure 2: all 426 dong polygons for raw senior share and shelters/10k, with analyzed-station dongs visibly distinguished without calling other dongs deficient.

Figure 3: four primary log-ratio moderation coefficients with pointwise 95% CI and caption describing FE, controls, two-way clustering and Holm-vs-CI distinction.

- [ ] **Step 3: Write failing runner fixture tests**

Use a temporary repo fixture and assert:
- missing analysis base may trigger the existing Stage 3A regeneration path, but network is never used;
- Stage 2 processed/clean inputs match `pipeline_summary.json` hashes;
- Stage 3A analysis base matches `eda_summary.json`;
- Stage 3B `confirmatory_summary.json` status is COMPLETE and its config thresholds match Stage 3C;
- deliberate drift in any accepted dependency blocks before publication;
- failed run does not replace existing Stage 3C success outputs;
- successful two-run fixture output is byte deterministic;
- no absolute repo path or runtime timestamp is serialized;
- accepted Stage 2/3A/3B input bytes are unchanged after success.

- [ ] **Step 4: Implement `run_spatial_heterogeneity(...)`**

Read:
- `subway/data/analysis/analysis_base_2024.parquet`;
- `subway/data/processed/station_dong_map.parquet`;
- `subway/data/processed/dong_population_2024q2.parquet`;
- `subway/data/clean/climate_shelters.parquet`;
- accepted Stage 2/3A/3B summaries/config.

Execution order:
1. validate config/prior-stage hashes and status;
2. build spatial context and expose shelter QA;
3. build station-day panel and execute zero-count gate;
4. fit Layer A;
5. fit primary and sensitivity Layer B;
6. render three figures;
7. recheck accepted input hashes;
8. serialize all outputs in a temporary staging directory;
9. atomically replace individual target files only after all gates pass;
10. print technical COMPLETE / human result review PENDING.

On failure, append traceback to `subway/logs/run_spatial_heterogeneity.log`, publish no partial success set, and return 1.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:
`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: all Stage 3C focused tests PASS.

- [ ] **Step 6: Execute the actual 2024 Stage 3C runner once**

Run:
`python subway/run_spatial_heterogeneity.py --year 2024`

Expected:
- exit 0;
- shelter mapping QA printed/serialized;
- 243×366 station-day panel passes strict-positive gate;
- primary/sensitivity models fit with finite two-way clustered covariance;
- exactly three figures and the specified CSV/JSON artifacts are produced.

If actual shelter exceptions or zero counts violate a scientific gate, STOP here and return to human review. Do not implement a workaround.

- [ ] **Step 7: Independently inspect actual artifact contracts before interpretation**

Verify:
- 243 station context rows, 173 unique station ADM_CD, 426 dong context rows;
- primary table exactly four rows;
- sensitivity contains only p95/p05 version of those four terms;
- Layer A contains 243 stations and no significance classification;
- z-score unique-dong mean/SD;
- figures visually show full uncertainty/zero references and no causal/vulnerability overstatement;
- summary hashes and prior-stage hashes match.

- [ ] **Step 8: Commit Task 4**

Stage only Stage 3C code/config/tests and deterministic results/figures. Do not include runtime logs or regenerated large Parquets.

`git commit -m "feat: run subway spatial heterogeneity analysis"`

---

### Task 5: Document results, run the final regression gate, and stop for human review

**Files:**
- Create: `subway/docs/analysis/11-spatial-heterogeneity.md`
- Modify: `subway/docs/analysis/00-report-map.md`
- Modify: `subway/docs/analysis/methodology-log.md`
- Modify: `subway/docs/analysis/ai-usage-log.md`

**Interfaces:**
- Consumes: Task 4 versioned Stage 3C outputs only.
- Produces: report-ready evidence trail; no new statistical analysis.

- [ ] **Step 1: Write the Stage 3C result record**

Separate sections explicitly:
- CONFIRMED FACT — sample/context/shelter mapping/accounting;
- DESCRIPTIVE RESULT — Layer A coefficient distribution/map;
- MODEL ESTIMATE — four primary moderation estimates;
- STATISTICAL UNCERTAINTY — pointwise CI/raw p/Holm p and sensitivity;
- INTERPRETATION — only one of the approved Case A/B/C formulations supported by actual results;
- LIMITATIONS — passenger residence, single ASOS citywide exposure, shelter snapshot completeness, straight-line distance, station-weighted estimand, unmeasured local factors.

State Stage 3B citywide H1/H2 remains NOT SUPPORTED and was not retuned.

- [ ] **Step 2: Update report-map/methodology/AI logs minimally**

Record:
- pre-fit approved Stage 3C design/spec SHA;
- exact implementation/result commit lineage;
- ChatGPT/Codex/human roles as actually performed;
- Secondary 2 technical completion and **human result review PENDING**;
- no policy conclusion.

Do not rewrite historical PENDING entries as if they had always been approved.

- [ ] **Step 3: Run the focused tests again**

`python -m unittest subway.tests.test_spatial_heterogeneity -v`

Expected: PASS.

- [ ] **Step 4: Run the full subway regression suite exactly once**

`python -m unittest discover -s subway/tests -v`

Expected: all tests PASS. Record the actual count; do not predict it in advance.

- [ ] **Step 5: Run the Stage 3C runner one final deterministic verification pass only if Task 4 artifacts or code changed after the actual run**

If no analytical code/result-producing change occurred after Task 4 actual execution, do not rerun merely for ceremony. If rerun is required, verify byte-identical Stage 3C outputs.

- [ ] **Step 6: Run repository hygiene checks**

`git diff --check`

`git status --short`

Inspect scoped diff and ensure no Stage 2/3A/3B accepted artifact changed.

- [ ] **Step 7: Perform one precision review**

Classify findings:
- Blocking — scientific contract, inference, accounting, reproducibility, or prior-stage integrity violation;
- fix-now — clear reporting/test defect with bounded correction;
- later-improvement — no impact on Stage 3C validity or contest report.

For any Blocking/fix-now code defect, reproduce with a failing test before fixing. Do not add new analyses during review.

- [ ] **Step 8: Commit/push the closeout record**

`git add subway/docs/analysis/11-spatial-heterogeneity.md subway/docs/analysis/00-report-map.md subway/docs/analysis/methodology-log.md subway/docs/analysis/ai-usage-log.md`

`git commit -m "docs: record subway spatial heterogeneity results"`

Push the current work branch only; verify remote SHA equals local HEAD and working tree is clean.

- [ ] **Step 9: STOP at the human result-review gate**

Report:
- branch and final SHA;
- focused/full test evidence;
- runner status;
- exact primary/sensitivity conclusions;
- any shelter mapping exceptions and limitations;
- no policy or final-report drafting started.

Do not begin Moran/LISA, daytime spatial interactions, threshold tuning, station significance mining, policy recommendations, or final report writing until the human approves Stage 3C results.
