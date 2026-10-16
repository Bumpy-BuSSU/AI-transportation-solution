# Stage 2 Batch 2R-B: approved authority adoption

Mission **P-S2-2RB**, approved 2026-10-06, attachment
`75d55a8f-96a3-449c-98e1-7466a584e49b`.
Starting HEAD `e70601fa1917316296e1c59ae01e70672b285dd2`, branch
`subway/preprocessing-pipeline`. Final Git SHAs are in the closeout response.

## Approved scope and source history

The human explicitly authorized exactly the 55 Batch 2R-A station aliases,
three complete transfer-coordinate groups and the exact audited direct-65+
population source. This supersedes the earlier automatic approval rejection.
[Batch 2R-A](02-spatial-input-blocker-review.md) and its five diagnostic files
remain unchanged historical proposal evidence. No additional alias, external
coordinate, station CRS or temporal assumption is adopted.

The proposal CSV's recorded resolution is `explicit alias gates passed;
authoritative adoption blocked by automatic approval review`, rather than the
shorter wording in the Mission. Selecting that exact recorded value and its
station-only audit side gives exactly 55 distinct line/raw/canonical tuples;
the 110 two-sided audit records are not 110 aliases. All adopted aliases are
explicitly line scoped. The original five senior rows remain byte-identical.
Only the line-7 뚝섬유원지 → 자양(뚝섬한강공원) official-rename evidence
has its contradictory “not an official rename claim” clause removed; other
reviewed source/display evidence and every mapping retain their meaning.

## Station authority and remaining blockers

Actual source recomputation gives 205 exact, 55 alias, 14 ridership-only and
16 station-only identities: **260/274 = 94.8905109489%** name/line coverage.
This is an identity audit, not verified spatial eligibility. The new
`batch2rb_station_identity_audit.csv` preserves both codes and an explicit
`source_code_conflict` flag. Twenty-one line-6 exact name/line matches have
different external codes and now produce a blocking `SOURCE_CODE_CONFLICT`
finding/exception. Neither source code is rewritten or offset-corrected.

| Complete reviewed coordinate group | Members | Result |
| --- | --- | --- |
| 까치산 | 2/200; 5/2519 | 2 INFO rows |
| 충무로 | 3/321; 4/423 | 2 INFO rows |
| 태릉입구 | 6/2647; 7/2719 | 2 INFO rows |
| 마곡 / 발산 | 5/2515; 5/2516 | 2 ERROR rows |

Nonblank string evidence and the exact complete distinct-line member set
remain required. Extra members, duplicate canonical identities, unrelated
collisions, null/NaN/false/zero/blank evidence cannot clear errors. A partially
present approved group is now explicitly ERROR even if its sole remaining
coordinate is unique; completely absent review groups do not apply.

**Task 5 BLOCKED**, separately for identity, coordinate coverage, temporal
applicability and CRS. Remaining reasons: unmatched identities, 21 code
disagreements, absent current-source 까치울/암사역사공원 coordinates,
마곡/발산 collision, unverified CRS and unresolved 2025 snapshot applicability.
KRIC stays supporting evidence; no coordinates are injected.

## Original baseline and approved extension

The original Stage 1 **7 datasets / 11 Raw files** remain immutable. The
approved extension adds `population_direct_65_plus` / one Raw file, so the
current baseline is **8 datasets / 12 files / 8 primary files**. Every original
Raw hash, manifest entry, schema snapshot entry and inventory row is unchanged.
The dataset registry, inspection schema and read-only preflight now require
the extended baseline. Inspection preserves both the quarter row and the
measure-header row of the new CSV, allowing explicit period-drift validation.

Approved Raw:
`subway/data/raw/2024/population_direct_65_plus/201_DT_201004_O020003_2024Q2_20261006.csv`.
SHA-256:
`e48f83ca75f7f92a5a83e39834440c0f3149ace1113c3533102797e4d0338d76`.
The audited local candidate was copied byte-for-byte. The Git index blob also
has that exact SHA. The export has a UTF-8 BOM and 454 LF-terminated rows;
the specific Raw path is `-text` in `subway/.gitattributes` to prevent
`core.autocrlf=true` from changing checkout bytes. Existing five LF artifact
attributes remain necessary and unchanged. Original Raw files remain excluded;
only this explicitly approved new export is force-added to Git for exact
source reproducibility.

[Official table DT_201004_O020003](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_O020003&conn_path=I2):
서울특별시 / 서울특별시기본통계, 주민등록인구(동별), official export
`등록인구_20261006115823.csv`, downloaded 2026-10-06, 2024 Q2/reference
2024-06-30. The public official export needs no login; separate license text
was not identified in export/table metadata, and provider/source attribution
is retained. This is not asserted to carry a specific open-data license.

## Task 6 primary output and independent validation

`population_direct_65_plus` is now **PRIMARY**; the original age-band
`population` stays **VALIDATION / SUPPLEMENTARY**. Exact source fields,
quarter, unit and approved SHA are checked. Codes of length 3/6/9 establish
Seoul/gu/dong parents; they are not equated to SGIS codes. Complete source
gu member-name sets are independently matched to complete Q2 boundary parent
sets. The seven existing explicit typography relationships are reused; no
generic punctuation normalization or spatial geometry join is involved.

`batch2rb_population_clean.csv` is the actual verified 426-row clean output
with gu, dong, adm_cd, total, direct 65+, share, reference period/date and raw
provenance. It is placed with acceptance evidence in `data/validation`;
the Task 10 full clean/processed publication runner is not implemented.
It uses the official **계** and **65세이상고령자**, both 명; the official
metadata includes foreigners in the 65+ aggregate. Missing/statistical
symbols stay nonnumeric. No zero fill, age-band manufacture, reconciliation
or quarter substitution occurs. Share is calculated only for total>0 and
senior<=total; zero total and invalid excess have null shares.

Measured result: **25 gu / 426 unique dong keys / 426 exact boundary keys**,
both 신사동 separated by gu, zero missing required cells out of 852,
nonnegative counts and no senior>total. Totals are **9,619,861 / 1,785,286**.

| Independent old complete 400-dong comparison | Exact | Mismatch | Max absolute difference |
| --- | ---: | ---: | ---: |
| direct total vs old 계 total | 400 | 0 | 0 |
| direct 65+ vs old eight-band sum | 400 | 0 | 0 |

All 26 previously blocked dongs have direct numeric total/65+ and valid share.
The old source's 32 missing elderly age-band cells across those 26 dongs remain
missing; those age-band values are not described as fixed. The historical
400/26 diagnostic stays unchanged. New comparison and recovered-dong evidence
are recorded in the Batch 2R-B CSV/JSON.

**Task 6 COMPLETE**: exact Raw SHA, source contract, hierarchy, required values,
boundary-key equality, independent 400 comparison, 26 coverage, deterministic
artifacts, full regression and original Raw integrity all passed.

## Validation and reproduction scope

Executed commands use Python 3.11.9, pandas 3.0.6, numpy 2.4.6, pyarrow 25.0.1,
GeoPandas 1.2.0 and Shapely 2.1.2:

- `python -m unittest discover -s subway/tests -v`: 83 baseline, **102 PASS**
  after implementation. Station additions: five RED failures before adoption;
  baseline extension: two RED failures; direct reader/clean/comparison: nine
  RED failures. Negative behavior and historical source tests pass together.
- `python subway/tools/inspect_raw_inputs.py --year 2024`: extended baseline
  exit 0, ERROR/WARNING/INFO all 0. Read-only `preflight(repo_root, 2024)`: [].
- Actual Task 8 regression recomputed **3,988,480 integrated / 3,987,960 matched /
  520 total-only / 0 senior-only / 0 ambiguous**; three excess cells,
  3,987,957 valid non_senior, 3,968,169 valid senior_share, 19,788 matched 0/0.
  Accounting and two diagnostic CSV byte hashes match Batch 3. Its historical
  summary remains unchanged; a new regenerated local summary naturally has
  different adopted-config provenance and is not substituted for history.
- Actual Task 4 weather and Task 7 boundary/shelter summaries equal Batch 2.
  Senior aliases, senior identity assignment and adopted QA policy are frozen.
- Two independently generated writes with reversed row order have identical
  acceptance CSV/JSON hashes; repeated actual-source diagnostic generation
  also matches. Original 11 Raw hashes and all five Batch 2R-A reports are
  individually compared with the starting commit's recorded evidence.
- `git diff --check`: 0. Inspection regeneration against the committed baseline
  produces `git diff --exit-code` 0 for the five Stage 1 artifacts. Final commit,
  clean working tree, push and remote SHA are reported in the closeout response.

Acceptance drivers are retained in this chat workspace `_batch2rb`: `regression.py`
recomputes the existing Task 8/4/7 diagnostics; `evidence.py` calls the checked-in
station and direct population cleaners, old-source cleaner and comparison,
enforces all gates, and writes only the six Batch 2R-B acceptance artifacts.
They are local audit drivers, not the forbidden Task 10 pipeline runner.
The checked-in unit tests reproduce the actual 426/400/26 and deterministic
clean-output checks using the repository's recorded source contract.

**Task 9 NOT STARTED. Tasks 10 and 11 NOT STARTED.** No station Point-in-Polygon,
population-to-station join, shelter proximity or station CRS conversion.
No analysis results, causal interpretation or policy conclusions are claimed.


## Final review hardening and Windows checkout proof

A read-only whole-change review independently re-derived the station and
population CSVs and their exact committed bytes. Final checks identified two
confirmed defects, both reproduced RED before their scoped fixes:

- With `core.autocrlf=true`, temporary `git checkout-index` converted the six
  new acceptance files and four published-hash config files to CRLF. For
  example population_clean changed from SHA `9d7e0115d7da96711d54a9cca009d52428cb2c3b0b80978b535724f9e78d96cd`
  to `c4abd22a5d420bd239f9f82bb997dd65ca35141e70807d9b78a9820ee0bf3f34`.
  Exact per-file `text eol=lf` attributes now preserve index bytes on checkout;
  the original five artifact LF attributes remain unchanged. All ten files,
  plus exact new Raw bytes, pass the temporary-checkout byte comparison.
- Nullable `BASE_DATE` equality could be skipped by pandas `.all()` and pass
  the direct cleaner's Q2 boundary contract. Explicit null-to-false validation
  now rejects null and wrong dates; actual valid Raw and population outputs
  remain unchanged.

Both new regression tests pass and the final full suite is **102/102 PASS**.
The six acceptance artifacts were regenerated and checked again; only final
verification test-count metadata changed. No structural refactor or new
functionality was added. Remaining Task 5 resolutions, future Tasks 9/10/11,
and re-adjudication of already approved evidence stay outside this approval;
source mappings and access wording were checked against the binding Mission.


## Scoped changed files

36 files changed from the Mission starting HEAD; the empty Raw inspection report is unchanged.

```text
docs/subway/2024-raw-schema-baseline.md
docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md
subway/.gitattributes
subway/config/datasets.yaml
subway/config/source_contracts_2024.yaml
subway/config/station_aliases.csv
subway/config/validation_rules.yaml
subway/data/raw/2024/population_direct_65_plus/201_DT_201004_O020003_2024Q2_20261006.csv
subway/data/validation/batch2rb_baseline_extension_summary.json
subway/data/validation/batch2rb_population_authority_summary.json
subway/data/validation/batch2rb_population_clean.csv
subway/data/validation/batch2rb_population_cross_validation.csv
subway/data/validation/batch2rb_station_authority_summary.json
subway/data/validation/batch2rb_station_identity_audit.csv
subway/data/validation/raw_inspection_summary.json
subway/data/validation/raw_inventory.csv
subway/data/validation/raw_schema_snapshot.json
subway/data_manifest.csv
subway/docs/analysis/00-report-map.md
subway/docs/analysis/01-raw-data-baseline.md
subway/docs/analysis/03-approved-authority-adoption.md
subway/docs/analysis/ai-usage-log.md
subway/docs/analysis/methodology-log.md
subway/src/clean/population_direct.py
subway/src/clean/station.py
subway/src/ingest/population_direct.py
subway/src/ingest/schema_inspector.py
subway/src/transform/station_keys.py
subway/src/utils/paths.py
subway/src/validate/pipeline_validation.py
subway/tests/test_baseline_extension.py
subway/tests/test_inspect_raw_inputs.py
subway/tests/test_paths.py
subway/tests/test_population_direct.py
subway/tests/test_station_authority.py
subway/tests/test_station_keys.py
```
