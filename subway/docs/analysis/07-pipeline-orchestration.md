# Task 10: reproducible 2024 E2E pipeline with configurable study scope

P-S2-T10,2026-10-07. Branch `subway/preprocessing-pipeline`, starting HEAD `e4463288ce12f08ec87ec045f312d5dfde649801`.
Task9 **HUMAN APPROVED on2026-10-07**, as explicitly recorded in this Mission.
Historical Task9 reports retain their then-pending review status and bytes; this record updates current acceptance.
Task10 technical COMPLETE; Task10 human result review PENDING. **Task11 NOT STARTED**.

## Current command and publication

```powershell
python subway/run_pipeline.py --year 2024
python -m unittest subway.tests.test_run_pipeline subway.tests.test_study_area -v
python -m unittest discover -s subway/tests -v
python subway/tools/inspect_raw_inputs.py --year 2024
git diff --check
```

`run_pipeline(repo_root: Path,year: int) -> int` and `main(argv: list[str] | None=None) -> int` resolve the current profile from config.
Final production code ran twice on actual2024 inputs: exit0 both, **PIPELINE PASSED WITH WARNINGS**, identical summary bytes and all16 hashed output files.
Raw:8 datasets/12 files, all hashes unchanged; extended Raw inspection8/12 exit0, ERROR/WARNING/INFO=0.
Current pipeline quality counts: ERROR=0,WARNING=16,INFO=2.
Warnings remain explicit: weather missing observations, isolated senior>total, source metadata limitations,
approved aliases/code warnings/spatial exclusions, old supplementary age-band limitations and shelter temporal uncertainty.
OUTSIDE_CURRENT_STUDY_AREA is an analytical-scope INFO condition, not source corruption.

## Three scope layers

1. Source/core: all Seoul Metro1–8 observations, including stations outside Seoul, remain preserved.
2. Current empirical case: Seoul Special City, selected because Ttareungi, population, boundaries, climate-response spatial data and ASOS108 currently provide consistent inputs.
3. Future extension: wider capital-region/other comparable municipalities remain possible after equivalent data contracts and regional weather assignment are validated. No other region/data/analysis is implemented now.

[study_area_2024.yaml](../../config/study_area_2024.yaml) names the current area, boundary/population/weather/shelter source IDs,
reference year and boundary count/CRS/code/date contract. Generic mapping consumes that explicit contract;
426 dongs,243 mapped and the Seoul code prefix are current profile/baseline values, not universal transform invariants.
Legacy source-specific cleaners remain the approved2024 source adapters; adding an unvalidated region is not a config-only promise.
Minimal2-polygon synthetic-profile tests verify generic mapping/population join and union classification without Seoul names or426 rows.

Membership is independently computed against the union of the validated configured boundary.
An internal dong-boundary point may be inside the union even though its mapping_status is BOUNDARY_POINT.
Overlaps do not imply outside scope; outer study boundary touches remain UNRESOLVED.
ZERO_MATCH is not automatically outside. Every actual15 ZERO_MATCH was checked against the whole union and is outside.
No nearest fallback, buffer, snap, coordinate nudging or manual ADM_CD assignment.
Task5-excluded16 identities never enter geometry and retain UNRESOLVED scope in the274-row master.

| Product | IN_CURRENT_STUDY_AREA | OUTSIDE_CURRENT_STUDY_AREA | UNRESOLVED_STUDY_AREA_STATUS |
|---|---:|---:|---:|
| 258-row station_dong_map | 243 | 15 | 0 |
| 274-row station_master | 243 | 15 | 16 |

Technical Task9 result remains243 MAPPED/15 ZERO_MATCH/0 BOUNDARY_POINT/0 MULTIPLE_MATCH.
mapping_status and study_area_status are separate columns, never identity keys.
The15 outside rows remain in the full core; their ADM_CD/population fields remain null.
They are outside the current study area, not erroneous stations or invalid transport observations.
Names/coordinates/canonical IDs remain in [historical Task9 exceptions](../../data/validation/task9_station_dong_exceptions.csv)
and current [spatial exceptions](../../data/validation/exceptions_spatial.csv).
Weather remains a separate366-row source product; ASOS108 is not joined as exposure to out-of-area stations.
Future exposure assignment could use multiple stations, an approved nearest-valid rule, gridded climate or another validated method; none is implemented.

## Products and hashes

Parquet products are generated locally under data/clean and data/processed and excluded from Git by narrow generated-product rules.
The full core file is about217MB; code/config/canonical QA and exact hashes make these products reproducible without versioning large binaries.
Output hashes are SHA-256, verified against actual files. JSON excludes its own recursive hash;
two-run verification also compares the summary itself byte for byte.

| Clean output | Rows | SHA-256 |
|---|---:|---|
| `clean/climate_shelters.parquet` | 412 | `b0fbe6245fc0453f5b932ad7eb4ab9d3135f7a864ec4e4c7152de83dc78e361e` |
| `clean/dong_boundary_2024q2.parquet` | 426 | `f480ac7e77b181013e1ff66cae62a67f31ea0a8321d8a41ab659e39b033927e6` |
| `clean/population_2024q2.parquet` | 426 | `ca587dc2ce6bed0992caf1a5652e3af4888f8d1ce9a573a46e7b65d9a3656932` |
| `clean/senior_ridership_2024.parquet` | 3,987,960 | `27204fe04b646ae03b4a9eff0b506ae3b8ae7405b6dcf7589eb475830d2661d8` |
| `clean/stations.parquet` | 276 | `cf5fc107d1882c69f83fe97fb1183f71f4d68c1f17aee0de2758167b3b6ad589` |
| `clean/total_ridership_2024.parquet` | 3,988,480 | `574fcddda13937092523b13bcdcfa854eb43358d022b7298700db443afc4c5ae` |
| `clean/weather_2024.parquet` | 366 | `f28c83c551c8a5397bf1150aef0987ff83d6ada4eab98669c9fee61f36be91f2` |

| Processed output | Rows | SHA-256 |
|---|---:|---|
| `processed/dong_population_2024q2.parquet` | 426 | `b99e248e7362af7c5f145c3b174e9cabada6e0585c708f09e6c009cc2a01ac5c` |
| `processed/ridership_2024.parquet` | 3,988,480 | `b355e22f64500fd2eebbd57d50ec3e8d91be0a5c8abb0d79d8a3ec283c21b035` |
| `processed/station_dong_map.parquet` | 258 | `772fad38688a6db4a0b0c5f304b2b2445321a114caefd35d84a8a7340fd41516` |
| `processed/station_master.parquet` | 274 | `8bca3bf847126c3624048b9ffce4103b5aa0142f43c432b4b1610cd381ea289d` |

Canonical validation: data_quality_report.csv,join_report.csv,exceptions_ridership.csv,exceptions_station.csv,
exceptions_spatial.csv,pipeline_summary.json. All historical batch*/task5*/task9* reports stay byte-identical.
Exact validation hashes, Raw/config hashes, counts and environment are in [current summary](../../data/validation/pipeline_summary.json).
New configuration and CSV/JSON files have exact-file LF policies, preserving hashes under core.autocrlf=true.

## Gates and accepted source dispositions

Raw integrity/schema/config → ingest → existing clean functions → identity/age comparison → eligibility →
boundary/population contracts → strict mapping → independent union scope → baseline regression → staging/serialization → safe publication.
No network dependency. No absolute local path or current timestamp appears in deterministic artifacts.

Known source coordinate collisions are retained in source exceptions and original source findings.
Only the exact pinned Task5-approved collision rows receive an approved spatial-exclusion disposition.
Code conflicts are nonblocking only if the existing Task5 classifier separately corroborates ELIGIBLE_CODE_WARNING;
unmatched active identities must have an explicit Task5 exclusion. Other source/identity/geometry errors still block publication.
The current CRS warning records the approved analytical assumption, not source-specific verification.
Original source findings remain in source_station_diagnostics, with explicit current disposition.
Old age-band errors/rejected rows remain in supplementary_population_diagnostics, while the fully valid400 groups
are independently compared with direct population. Only the direct official426-dong source is the primary product.

Accepted2024 counts live separately in [pipeline_baseline_2024.yaml](../../config/pipeline_baseline_2024.yaml),
including SHA pins for existing authority and historical eligibility/mapping evidence. Generic transforms do not copy these constants into results.
Actual gates preserve:

- Task5:274 identities;237 eligible,21 warnings,12 identity/4 coordinate exclusions; shares unchanged.
- Task6:426/426 ADM_CD bijection;9,619,861 total/1,785,286 senior population;400/400 old-source comparison.
- Task8:3,988,480 integrated/3,987,960 matched/520 total-only/0 senior-only/0 ambiguous;3 explicit senior>total exceptions.
- Task9:258 inputs/243 mapped/15 zero/0 boundary/0 multiple; all21 warning flags preserved.

## Publication safety and tests

All11 Parquets and5 QA CSVs are serialized into same-filesystem staging after gates pass.
One writer lock prevents concurrent publication. Existing files are backed up; replacement failure restores changed files;
the complete success summary is published last. This is staged, rollback-safe multi-file publication, not a claim that multiple directory entries switch in one filesystem operation.
Consumers should verify the success status and hashes and avoid reading a generation while its writer lock exists.
A blocking/failed run returns nonzero, preserves diagnostic CSV/runtime logs, leaves prior product bytes in place,
and publishes a FAILED summary with empty output_hashes. Prior products are explicitly identified as last-successful files, not products of the failed run.
Unknown year, missing Raw, baseline drift, blocking findings, live lock, staging failure and mid-publication I/O failure are tested.
Reversed frame order yields identical hashes; fixture tests actually execute existing Tasks1–9 on two real transport identities and retain all reference sources.
New Task10 tests:11 orchestration/writer +6 study-area =17; full suite157 PASS. The CRS-column writer defect was reproduced RED and fixed using GeoDataFrame type detection.
Same recorded environment only: Python3.11.9,pandas3.0.6,numpy2.4.6,
pyarrow25.0.1,GeoPandas1.2.0,Shapely2.1.2,pyproj3.7.2,PROJ9.5.1.

## Current empirical questions and report-ready scope draft

Primary: “극한기온에서 서울시 내65세 이상 지하철 이용자의 이용 변화는 비고령층과 다르게 나타나는가?”
Secondary1: “이러한 연령별 차이는10~16시 주간 비첨두 시간대에서 더 강하게 나타나는가?”
Secondary2: “이러한 차이는 서울 내 역·행정동별로 어떻게 다르며, 지역의 고령인구와 기후대응 공간 조건과 어떤 관계가 있는가?”
No extreme-temperature classifications, statistical tests, EDA or scores are produced by Task10.
Aggregate ridership cannot establish trip purpose; later interpretation can at most be “기후회피형 이동과 일치하는 패턴”.
No claim that elderly passengers used the subway to escape heat is justified by this preprocessing.

Draft methodology wording (not an empirical finding):
“본 연구는 공공자전거·인구·행정경계·기상 및 기후대응 공간자료의 공간적 정합성을 확보할 수 있는 서울특별시를2024년 기준 실증 연구지역으로 설정하였다.
도시철도 원자료에 포함된 서울 외 역은 원본 및 통합 데이터에서 삭제하지 않고 현재 연구범위 밖 관측치로 구분하였다.
향후 분석 결과의 적용 범위는 검증된 서울 연구지역이며, 동일한 데이터 계약을 확보할 경우 수도권 및 지역 간 이동선택권 격차 분석으로 확장할 수 있다.”
No regional comparison has been performed; equivalent regional inputs and appropriate exposure assignment are prerequisites.

## Changed scope

run_pipeline.py; study_area transform; profile/baseline config; Task10/scope tests; configurable existing spatial mapper;
precise GeoDataFrame writer fix;6 canonical QA products; narrow.gitignore/.gitattributes; this execution record,
report-map/methodology/AI usage and plan addendum. No Raw, adopted aliases, historical evidence or statistical analysis changes.
Task10 COMPLETE / later human review PENDING. Task11 NOT STARTED.
