# Task 9: strict eligible-station → Q2 administrative-dong mapping

Mission P-S2-T9, 2026-10-07. Starting HEAD `411374b88049bffaaaebf5d55ec51b231265f4d4`, branch `subway/preprocessing-pipeline`.
Task9 implementation COMPLETE under `strict_point_in_polygon_with_documented_exceptions`.
Human review of the Task9 result is **PENDING**, not approved. Task10/Task11 NOT STARTED.
This is preprocessing QA; no EDA, inference, accessibility/demand interpretation or production Parquet publication.

## Input and identity contract

`build_station_master(eligibility)` preserves all274 Task8 identities and all Task5 provenance columns.
Authoritative input remains [Task5 eligibility](../../data/validation/task5_spatial_eligibility.csv):
237 ELIGIBLE,21 ELIGIBLE_CODE_WARNING,12 EXCLUDED_IDENTITY,4 EXCLUDED_COORDINATE.
Only258 eligible identities enter GIS. Source-only station rows and16 excluded identities cannot enter it.
No new aliases/coordinates or changes to Raw, source codes, accepted transfer groups or Task5 reasons.
All21 source-code conflict flags and both source codes remain in the map CSV.

EPSG:4326 is an approved **ANALYTICAL_ASSUMPTION**, supported by the official national
station-data standard; source-specific datum verification remains unavailable.
Points use longitude=x and latitude=y, explicitly transformed into EPSG:5179 before containment.
Original geographic coordinates are retained; projected values are explicitly x_5179/y_5179.
The Task5 SNAPSHOT_STABILITY_ASSUMPTION remains an assumption, not proof of continuous2024 observation.
암사역사공원's known2024-08-10 opening remains explicit and excluded by Task5's missing accepted coordinate.

## Strict GIS results

Boundary:426 unique ADM_CD, EPSG:5179, BASE_DATE=20240630; valid nonnull nonempty polygons.
Each station is MAPPED only when strictly within exactly one polygon.
If no strict containment, polygon touches are checked explicitly. Boundary points receive candidates, never one arbitrary dong.
Multiple/zero/touch results are explicit exceptions. Bad coordinates/identity/CRS/boundary contracts ERROR and block completion.
No nearest join, buffer, snap, dissolve, polygon repair, coordinate replacement or manual ADM_CD assignment.

| Status | Identities | Integrated rows | Matched rows | Total ridership | Senior ridership |
|---|---:|---:|---:|---:|---:|
| MAPPED | 243 | 3,557,520 | 3,557,520 | 3,089,452,830 | 426,414,392 |
| ZERO_MATCH | 15 | 219,600 | 219,600 | 104,442,107 | 20,030,503 |
| BOUNDARY_POINT | 0 | 0 | 0 | 0 | 0 |
| MULTIPLE_MATCH | 0 | 0 | 0 | 0 | 0 |

All258 identities have one mapping_status; all15 failures have reasons/evidence.
[Map CSV](../../data/validation/task9_station_dong_map.csv) includes all258, including failures.
[Exceptions CSV](../../data/validation/task9_station_dong_exceptions.csv) includes all15 failures.
Their ADM_CD/gu/dong and population fields are null. Empty candidate sets mean no strict containment or boundary touch in this boundary layer.
These diagnostics do not establish a source-provider error or authorize point correction.

| Canonical ID | Line | Station | longitude, latitude | Status | Candidate ADM_CD | Reason |
|---|---|---|---|---|---|---|
| `station:["3","지축"]` | 3 | 지축 | 126.912551, 37.648281 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["5","미사"]` | 5 | 미사 | 127.192954, 37.56329 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["5","하남검단산"]` | 5 | 하남검단산 | 127.223427, 37.539729 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["5","하남시청(덕풍·신장)"]` | 5 | 하남시청(덕풍·신장) | 127.206901, 37.541723 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["5","하남풍산"]` | 5 | 하남풍산 | 127.203897, 37.552201 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["7","광명사거리"]` | 7 | 광명사거리 | 126.854854, 37.47927 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["7","장암"]` | 7 | 장암 | 127.053126, 37.70015 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["7","철산"]` | 7 | 철산 | 126.868217, 37.47616 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","남위례"]` | 8 | 남위례 | 127.139047, 37.462839 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","남한산성입구(성남법원.검찰청)"]` | 8 | 남한산성입구(성남법원.검찰청) | 127.159845, 37.451568 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","단대오거리"]` | 8 | 단대오거리 | 127.156735, 37.445057 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","모란"]` | 8 | 모란 | 127.129921, 37.433888 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","산성"]` | 8 | 산성 | 127.149927, 37.456886 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","수진"]` | 8 | 수진 | 127.140936, 37.437575 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |
| `station:["8","신흥"]` | 8 | 신흥 | 127.14759, 37.440952 | ZERO_MATCH | none | NO_STRICT_WITHIN_OR_TOUCH |

## Coverage and denominators

| Denominator | Identities | Total all observations | Total matched observations | Senior observations |
|---|---:|---:|---:|---:|
| A original core | 274 | 3,302,748,460 | 3,302,748,323 | 462,981,953 |
| B Task5 eligible | 258 | 3,193,894,937 | 3,193,894,937 | 446,444,895 |
| C Task9 MAPPED | 243 | 3,089,452,830 | 3,089,452,830 | 426,414,392 |

| Loss/coverage | Identity share | Total all share | Senior share |
|---|---:|---:|---:|
| Task5 exclusion / A | 5.839416% | 3.295847% | 3.571858% |
| Task9 additional exclusion / A | 5.474453% | 3.162279% | 4.326411% |
| Task9 additional exclusion / B | 5.813953% | 3.270055% | 4.486669% |
| Cumulative exclusion / A | 11.313869% | 6.458125% | 7.898269% |
| Cumulative coverage C / A | 88.686131% | 93.541875% | 92.101731% |

Core remains3,988,480 integrated /3,987,960 matched /520 total-only rows, with137 total-only riders;
all total-only observations remain in A even though excluded spatially. Senior>total exceptions remain3.
Cumulative matched-total loss=6.458121%; denominator3,302,748,323 distinct from all-total denominator3,302,748,460.
All exact per-status counts, incremental/cumulative losses and shares are in [summary JSON](../../data/validation/task9_spatial_summary.json).
No arbitrary coverage threshold was tuned. The spatial subset does not represent all274 original station identities.

## Population bijection and coverage QA

426/426 population/boundary ADM_CD exact unique set equality PASS. Population labels are checked by code;
same dong names in different gu never serve as a dong-name-only join key. Label disagreement is ERROR.
Original boundary geometry/date and direct-population provenance are preserved in the internal joined GeoDataFrame.
Direct totals unchanged:9,619,861 population_total,1,785,286 population_65_plus.
Old-source400/400 total/senior comparison remains exact,26 additional primary dongs retained.
Only safely MAPPED stations receive population fields and provenance.
Population values are dong attributes; repeated station rows must not be summed to infer city totals.
MAPPED stations represent173 distinct ADM_CD. Stations-per-ADM_CD distribution:
124 dongs with1 station,34 with2,10 with3,4 with4,1 with5; sums173 dongs/243 identities.
This is descriptive preprocessing coverage QA, not accessibility or demand analysis.

## Reproduction and validation

From repository root, using the recorded Python/library environment:

```powershell
python -m unittest subway.tests.test_transform_spatial -v
python -m unittest discover -s subway/tests -v
python subway/tools/generate_task9_audit.py --output-dir <audit-directory-1>
python subway/tools/generate_task9_audit.py --output-dir <audit-directory-2> --reverse-input-order
python subway/tools/inspect_raw_inputs.py --year 2024
git diff --check
```

Baseline122 PASS; new18 Task9 tests PASS; full140 PASS.
Actual Task8 reconstruction uses unchanged existing cleaners/identity/integration functions;
accounting, Task5 counts/shares and actual direct-population comparison are asserted against accepted evidence.
All12 Raw SHA-256 and existing manifest/config/validation files unchanged.
Normal and reversed-input generation produced identical bytes for all3 evidence files.
Raw inspection:8 datasets/12 files, ERROR/WARNING/INFO=0, exit0.
The3 new reports have exact-file LF policies to preserve committed hashes under core.autocrlf=true.
Environment: Python3.11.9, pandas3.0.6, GeoPandas1.2.0,
Shapely2.1.2, pyproj3.7.2, PROJ9.5.1.
Hashes:

- `task9_station_dong_map.csv`: `b6f037c1fcc3df0ba16dc65d38d366f2da4168f5b297977f835b0cec56c3d05e`
- `task9_station_dong_exceptions.csv`: `550d3623b7def2b3733b40834c9ae6e53b20e90367088de4671b10566aa15462`
- `task9_spatial_summary.json`: `6586d4cda7926058c28f281f71c7a18cb6902ccf84f67eb6403fb0d2dcc52edd`

## Scope of changed files

- `subway/src/transform/spatial.py`, `subway/tests/test_transform_spatial.py`
- `subway/tools/generate_task9_audit.py` (validation evidence only; does not orchestrate production publication)
- Task9 map/exception CSVs and summary JSON
- `subway/.gitattributes` (3 narrow LF report policies)
- This report, report-map, methodology-log, ai-usage-log and Task9 plan addendum

Task5 is HUMAN-APPROVED COMPLETE. Task9 technical completion awaits later human review.
Task10 NOT STARTED. Task11 NOT STARTED.
