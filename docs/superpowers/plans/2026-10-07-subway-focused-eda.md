# Focused 2024 subway EDA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Reproducible current-Seoul sample and descriptive evidence for later threshold/model review.
**Architecture:** Pure `build_eda(core,master,mapping,weather,year)` returns analysis base, deterministic tables and metadata. `run_eda(repo,year)` verifies accepted Stage2 hashes, writes local base plus versioned tables/five figures and a portable summary. Existing Stage2 code and products stay unchanged.
**Tech Stack:** Existing pandas/numpy/pyarrow plus pinned matplotlib3.10.7; offline execution.
**Spec:** User Mission attachment b111dd8f-886b-4ee8-baaf-9bb89b26000a; detailed requirements are binding and already authorize implementation.

## Global Constraints
Current branch and checkout; full transport core immutable. No inferential methods or adopted extreme threshold. Use current artifact membership and validate many-to-one joins. Base retains all current-area rows with explicit metric-valid flags; exclude unmatched/age anomalies only from age-comparison metrics, retaining their counts and original values. Daily paired-age totals use a common valid-cell denominator; also show full current-area raw totals. Weather-only deciles with duplicate edges collapsed; percentile tails use strict inequalities. No holiday/network data. Pre-specified six full intervals [10,16). Same recorded environment determinism only.

## Review Focus
Missing weather dates/duplicates, membership contradictions, nullable/zero denominators, tied weather bins, and daily unequal sample exposure must fail or be explicit. Covered by focused tests; final review checks actual artifacts/plot labels and scientific restraint.

### Task1: Pure sample and descriptive tables
Files: src/analysis/eda.py; tests/test_analysis_eda.py.
Interface: build_eda(DataFrame,DataFrame,DataFrame,DataFrame,int)->(DataFrame,dict[str,DataFrame],dict).
- [ ] Write fixture tests for current membership, immutable inputs, join uniqueness/missing dates, exact hours, preserved excess/null/zero, weather-only bins, reversals/no network/no paths.
- [ ] Run focused unittest RED for missing module.
- [ ] Implement keys/metric flags/accounting, weather summaries/tails, daily/calendar, hourly, temperature profiles and station summaries/distribution.
- [ ] Run focused unittest GREEN.

### Task2: Runner/artifacts/figures
Files: run_eda.py; requirements-analysis.txt; scoped ignore/EOL policy.
Interface: run_eda(Path,int)->int, main(list[str]|None)->int.
- [ ] Add runner tests for hash rejection, no mutation and deterministic real serialized fixtures.
- [ ] Verify RED; implement accepted hash checks, staging, CSV/Parquet writer, five deterministic PNGs, portable provenance summary.
- [ ] Focused tests GREEN; actual run_eda --year2024 once, verify hashes/core and view five figures.

### Task3: Evidence/documentation/final gate
Files: 08-focused-eda.md; report-map/methodology/AI log; results tables/figures.
- [ ] Document actual facts separately from descriptive patterns and later interpretation, all exclusions/denominators, next-review questions.
- [ ] Full regression once, git diff check, final independent review; one Important fix pass RED→GREEN if required.
- [ ] Commit/push current branch, remote equality and clean. Stop before thresholds/models/policy.
