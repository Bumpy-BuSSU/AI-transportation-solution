# Subway Clean / Transform Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 7종 Raw를 7개 clean·4개 processed 데이터셋으로 변환하고 validation, provenance 및 재현성을 확보한다.

**Architecture:** Stage 1 ingest·hash·경로 검사를 재사용하고 source별 pure clean 함수, 명시적 station/crosswalk transform, Gate 0–3 검증과 CLI orchestration을 분리한다. ERROR가 있으면 정상 processed 결과를 발행하지 않고 diagnostics와 실패 summary를 남긴다. Stage 1 산출물은 보존한다.

**Tech Stack:** Windows + Python, Colab 호환; pandas, pyarrow, openpyxl, geopandas, shapely, pyyaml, 표준 unittest. 의존성은 기존 `subway/requirements.txt`에서 관리한다.

**Spec:** [승인 설계](../specs/2026-10-03-subway-data-preprocessing-design.md). Source 권위: [source contracts](../../../subway/config/source_contracts_2024.yaml), [Raw baseline](../../subway/2024-raw-schema-baseline.md), [manifest](../../../subway/data_manifest.csv).

문서 파일명 날짜는 사용자 지정 `2026-10-05`를 유지한다. 실제 작성·읽기 전용 진단일은 2026-10-06이다. **계획만 작성, 구현 미착수.** 아래 인터페이스·tests·config는 미래 구현 계약이며 지금 존재하는 기능이 아니다.

## Global Constraints

- Primary: local Windows + Python / Secondary: Google Colab compatible / No absolute local paths.
- Raw data remains local and is excluded from Git. Keep downloaded filenames unchanged. Never overwrite or manually edit raw files.
- Target command: `python subway/run_pipeline.py --year 2024`. Same structure must support later 2023 and 2025 expansion; 다른 연도는 별도 source contract 없이는 실패시킨다.
- Every manual mapping, exclusion, or correction must be explicit and auditable. Unknown metadata must remain blank or marked unverified; never guessed.
- 초기 runtime config는 `datasets.yaml`, `station_aliases.csv`, `validation_rules.yaml`. Stage 1의 `source_contracts_2024.yaml`은 이미 존재하는 관측 source 계약으로 추가 재사용한다. 임의의 새 설정 파일은 만들지 않는다.
- No EDA, charts, correlation analysis, heatwave/cold-wave classification, statistical tests, regression, machine learning, policy scoring, or final report writing in this phase.
- PPML, GAM/spline, fixed effects, interaction/three-way interaction, Random Forest/SHAP, 최종 해석은 별도 분석 Stage다.
- bike/, common/, top-level README·협업 규칙을 변경하지 않는다. 이번 Mission의 변경은 문서뿐이다.
- Raw identifiers·source column·source row를 보존한다. Negative/null/duplicate/unmatched를 silently repair/drop하지 않는다. 역 코드 단독 공통 PK를 가정하지 않는다.
- 강수·적설 blank는 의미 확인 전 NaN 유지. Station CRS는 공식 metadata 또는 충분한 source evidence 확인 전 설정하지 않는다.
- 모든 구현 Task는 RED → minimal implementation → GREEN → 관련 regression → 해당 파일만 commit 순서로 진행한다.

## Research Context와 해석 범위

전체 팀 주제는 **“탄소중립 교통 전환 속 고령자의 이동 선택권 격차 분석 — 공공자전거와 도시철도를 중심으로”**이며, 이 계획은 subway 분석만 다룬다.

현재 subway working question은 **“극한기온은 서울 고령층의 지하철 이용 패턴을 어떻게 변화시키며, 이러한 변화는 기존 교통 혼잡 및 기후대응 공간의 부족과 어떤 관계가 있는가?”**이다.

- Primary testable question: “극한기온에서 65세 이상 고령층의 지하철 이용 변화가 비고령층과 다르게 나타나는가?”
- Secondary hypothesis question: “연령별 차이가 존재한다면 그 차이가 10~16시 daytime/off-peak에서 더 강하게 나타나는가?” Daytime의 최종 정의와 검증은 분석 Stage에서 수행한다.

연구질문은 현재 working question으로 확정되어 있다. 최종보고서 문장은 분석결과 후 조정할 수 있으며 분석결과·정책결론은 아직 없다. Aggregate ridership으로 trip purpose를 직접 증명할 수 없으므로 향후 해석은 최대 **“기후회피형 이동과 일치하는 패턴”** 수준으로 제한한다. Stage 2는 이 가설을 검정하지 않는다.

현재 7개 Raw에는 일별 실제 혼잡을 검증할 core congestion dataset이 없다. **혼잡과의 관계는 Stage 2 증거 범위 밖**이다. 적합한 congestion dataset 확보 후 secondary analysis로 추가하거나 분석 단계에서 최종 연구질문의 범위를 조정한다. 현재 자료로 혼잡 결과를 예고하거나 추론하지 않는다. Shelter는 clean auxiliary spatial layer로 유지하며 기후대응 공간 부족에 대한 결과도 아직 확정하지 않는다.

## Stage 2 information-preservation contract

후속 분석 단위 **date × station × hour_bin × boarding/alighting × age comparison**을 손실 없이 보존한다. Age comparison은 별도 연령 long table을 지금 강제 생성한다는 뜻이 아니라 senior/non_senior를 동일 key에서 비교할 수 있도록 유지한다는 계약이다.

- 20개 time bin을 임의 집계하지 않는다. 10~16시 indicator는 Stage 2에서 만들 필요가 없으며 이후 원래 hour_bin으로부터 생성 가능해야 한다.
- Station-level heterogeneity 분석을 위해 canonical_station_id를 보존한다. Boarding/alighting을 합치거나 station/date/hour 단위를 축약하지 않는다.
- Senior, total, non_senior, senior_share 각각의 source row·hour column·양쪽 join provenance와 파생식·유효성 조건을 보존한다. 미매칭·rejected·파생 null의 이유도 추적 가능해야 한다.
- Weather는 core panel에 강제 join하지 않지만 서울 ASOS 108의 unique daily date key와 2024 coverage를 보존해 이후 date 기준으로 행 손실·증식 없는 join이 가능해야 한다. Population/shelter도 core panel에 강제 결합하지 않는다.

## Review Focus

1. 역명 변경·문장부호·괄호와 호선 표기 차이: alias 없이는 임의 동치화 금지, before/after count 기록 (Task 3·5).
2. Duplicate 또는 다대다 join: 행 폭증 금지, source row 보존과 blocking diagnostics (Task 2·3·8).
3. 인구의 동명 중복·구 subtotal·연령대 누락: gu+dong, 모집단·8개 band 검증 (Task 6·9).
4. CRS 미확정·polygon 경계점·0/multiple match: 성공 주장 금지, spatial exception 보존 (Task 7·9).
5. 실패 후 남은 이전 출력·환경 차이·빈 exception 파일: 실패를 성공으로 오인하지 않고 고정 header·sort·serialization 사용 (Task 1·10).

## Preflight와 실제 미확정 사항

Stage 1 technical baseline commit은 `2fa30e7`, Stage 1 closeout / Stage 2 planning commit은 `7ec5c84`다. 이는 기준선의 이력이며 현재 branch HEAD를 과거 commit으로 지칭하지 않는다. Stage 1에서 16 tests, inspection 0, 7종/11 files/primary 7, finding 0, deterministic·Raw 불변·clean이 확인됐다. `run_pipeline.py`, clean/transform 모듈, aliases/rules config는 아직 없다. Stage 1 validator는 source 계약과 행 값의 의미까지 검사하지 않으므로 Stage 2 Gate 0에서 추가 확인한다.

읽기 전용 진단 결과(2026-10-06, 원본 수정·clean 생성 없음):

- Senior `(역번호, 역명)` 273개, total 274개. Total 내부 이 조합의 multiple line은 0이나 senior 8개는 exact unmatched다: 223 교대(법원·검찰청), 319 종로3가(탑골공원), 330 교대(법원·검찰청), 409 불암산, 428 삼각지(전쟁기념관), 2535 종로3가(탑골공원), 2629 삼각지(전쟁기념관), 2823 남한산성입구(성남법원·검찰청). 숫자는 unique 조합 수이며 unmatched 행 수가 아니다. 충분한 식별 조합의 uniqueness를 검증하기 전 호선을 부여하지 않는다.
- Total 호선 label `1호선`–`8호선`, station `1`–`8`. 원본 호선+역명의 exact match는 0개. 호선만 통일한 진단은 공통 205개 / total only 69개 / station only 71개다. 예: 서울역↔서울, 청량리(서울시립대입구)↔청량리. 모두 후보일 뿐 alias 채택 근거가 아니다. 전체 mismatch·duplicate를 다시 출력하고 개별 증거를 확인한다.
- Population `동별`은 452개 연속 지역 블록·451개 distinct label이며 `항목`은 계·한국인이다. 합계→종로구→동들→중구 순서가 관측됐지만 전체 소속 계층·동명 중복·계 의미는 아직 검증되지 않았다. 8,136 = 452×18이라는 산술만으로 426동 consistency를 입증하지 않는다.
- Station `작성기준일` 값은 2025-08-14. CRS와 2024 역 운영·좌표 적합성은 추가 source evidence가 필요하다. `작성일자`의 의미도 추정하지 않는다.
- Weather 지점 108, 2024 날짜 366개는 관측했으나 blank의 의미는 미확정이다. Shelter 412행의 시점도 미확정이다.
- Boundary ADM_NM에서 gu/dong 분리 방법, ADM_CD 체계, 인구와의 구-동 bijection, polygon validity는 Task 6·7·9에서 진단한다.

CRS, hierarchy, 모집단, alias 미확정은 해당 작업의 blocking condition이다. Weather blank와 shelter temporal uncertainty는 명시적 warning/metadata를 유지하고 계속할 수 있다. 모든 ambiguity를 미리 해결했다고 주장하지 않는다.

## 기존 설계와의 관계

승인 설계의 출력명·계층·Gate·의존성을 유지한다. 설계의 `implementation not started`는 승인 당시 상태이며 Stage 1은 이미 완료되었다. 원문을 다시 쓰지 않는다. 초기 config 3개 제한은 Stage 1에서 확정된 source contract를 재사용하는 현실과 차이가 있으므로 runtime config 3개 + 관측 source 계약이라는 역할 구분을 명시한다. Root requirements 예시보다 Stage 1 계획의 `subway/requirements.txt` 위치를 따른다.

설계의 clean senior `line`은 source에 없으므로 Task 2에서 nullable, Task 3 uniqueness 검증 후 완성한다. 최종 산출물의 핵심 필드는 유지하고 provenance/join_status를 추가한다. 설계의 '쉼터 보조 공간 결합'은 보조 clean layer 준비로 충족하며 core ridership panel과 강제 결합하지 않는다. Stage 2 완료 주장에는 station CRS와 공간 mapping 해결이 필요하다. WARNING 상태를 모든 definition-of-done 완료로 오인하지 않는다.

## 파일 구조와 공통 인터페이스

미래 생성 파일: `subway/src/clean/{__init__,contracts,ridership,weather,station,population,spatial}.py`, `subway/src/transform/{__init__,station_keys,ridership,spatial}.py`, `subway/src/validate/pipeline_validation.py`, `subway/src/utils/artifacts.py`, `subway/src/ingest/spreadsheetml.py`, `subway/run_pipeline.py`, Task별 tests. 기존 `schema_inspector.py`는 SpreadsheetML reader 추출 시에만 수정하고 기존 fixture regression을 유지한다. 무관한 구조 refactor는 하지 않는다.

`contracts.py`: `StageResult(frame: pd.DataFrame, findings: list[Finding], exceptions: pd.DataFrame)` dataclass. Spatial frame은 GeoDataFrame이며 같은 타입 계약을 따른다. 모든 source result의 provenance 열: `source_dataset_id`, `source_file`(repo relative), `source_row_id`(안정적인 원본 row), 원본 identifiers; long ridership에는 `source_hour_column`. Join 결과는 양쪽 row provenance를 각각 보존한다.

`pipeline_validation.py`: 기존 `Finding` 재사용. `validate_frame(frame: pd.DataFrame, dataset_id: str, rules: dict) -> list[Finding]`, `pipeline_status(findings: list[Finding]) -> tuple[str, int]`. ERROR 존재→PIPELINE FAILED/1, WARNING만→PIPELINE PASSED WITH WARNINGS/0, 모두 없음→PIPELINE PASSED/0.

`artifacts.py`: `write_artifacts(output_dir: Path, frames: dict[str, pd.DataFrame], summary: dict) -> dict[str, str]`는 안정적인 sort/schema/nullable dtype·UTF-8 LF CSV·sorted JSON·고정 Parquet writer options로 쓰고 SHA-256을 반환한다. 빈 exception도 header를 쓴다. GeoParquet는 CRS metadata 유지. 동일 Raw뿐 아니라 manifest·contract·alias·rules와 동일 library 환경에서 byte reproducibility를 검증한다. 환경 버전은 summary에 기록하되 실행시각·절대경로는 제외한다. 다른 writer/library 환경 간 byte 동일성은 주장하지 않는다.

## 산출물 계약

| 영역 | 파일 | 핵심 schema / 주의 |
|---|---|---|
| clean | senior_ridership_2024.parquet, total_ridership_2024.parquet | date, line, station_code_raw, station_name_raw, station_name, boarding_type, hour_start, hour_end, ridership + hour_bin·provenance |
| clean | weather_2024.parquet | date, station_id, station_name, temperature_mean/min/max, precipitation, wind_max/mean, humidity_mean, snow_new_max, snow_depth_max + provenance |
| clean | stations.parquet | line, source_station_code, station_name_raw, station_name, latitude, longitude + source dates·provenance·CRS evidence metadata |
| clean | population_2024q2.parquet | gu, dong, population_total, population_65_plus, senior_population_share, 8 age-band counts + provenance |
| clean | dong_boundary_2024q2.parquet | base_date, adm_cd, admin_name_raw, gu, dong, geometry; EPSG:5179 |
| clean | climate_shelters.parquet | shelter_id, type, name, gu, address, x_raw, y_raw, operating_hours, geometry; EPSG:5186 + temporal uncertainty |
| processed | ridership_2024.parquet | date, line, station, hour, boarding_type, senior, total, non_senior, senior_share + canonical_station_id, join_status, provenance |
| processed | station_master.parquet | canonical_station_id, line, station_name, latitude, longitude, source_station_code + CRS provenance |
| processed | station_dong_map.parquet | canonical_station_id, adm_cd, gu, dong + match diagnostics |
| processed | dong_population_2024q2.parquet | adm_cd, gu, dong, population_total, population_65_plus, senior_population_share |

Validation directory: `data_quality_report.csv`는 기존 Finding 5열, `join_report.csv`는 join_name,status,count,input_left_rows,input_right_rows,output_rows를 사용한다. `exceptions_ridership.csv`, `exceptions_station.csv`, `exceptions_spatial.csv`는 exception_code, 관련 key, source provenance, candidate details를 고정 schema로 갖는다. `pipeline_summary.json`은 year,status,finding_counts,counts,input_hashes,config_hashes,output_hashes,environment,blocking_reasons를 갖고 자신의 hash는 넣지 않는다. Crosswalk·alias 후보는 station exceptions의 diagnostic record로 출력하고 채택 mapping과 구분한다. Stage 1 report 4개는 덮어쓰지 않는다.

Clean은 `subway/data/clean/`, processed는 `subway/data/processed/`에 쓴다. Core panel에 weather/population/shelter를 강제 결합하지 않는다. Binary의 Git 관리 범위는 구현 시 기존 데이터 정책과 크기에 따라 결정한다. Runtime log는 기존 ignore 대상 `subway/logs/pipeline_2024_YYYYMMDD_HHMMSS.log`에 쓴다.

## Task 1: Preflight·clean contracts·validation infrastructure

**Files:** Create `subway/src/clean/__init__.py`, `subway/src/clean/contracts.py`, `subway/src/transform/__init__.py`, `subway/src/validate/pipeline_validation.py`, `subway/src/utils/artifacts.py`, `subway/config/validation_rules.yaml`, `subway/tests/test_pipeline_contracts.py`. Modify `subway/config/datasets.yaml` (outputs·108·station CRS/evidence 필드; 미확인은 null).

**Interfaces:** `preflight(repo_root: Path, year: int) -> list[Finding]` in pipeline_validation. Stage 1 discover/hash/inspect와 manifest를 소비한다. StageResult, validate_frame, pipeline_status, write_artifacts는 위 공통 정의대로 만든다.

- [ ] RED: `test_preflight_rejects_hash_header_year_drift`는 hash·필수 header·contract year 변조 각각 ERROR, Raw 불변을 assert한다. `test_status_and_empty_reports`는 3 status/exit와 빈 CSV header, `test_contracts_preserve_unknown_metadata`는 CRS null, `test_artifacts_are_stable`은 2회 bytes 동일을 확인한다.
- [ ] `python -m unittest subway.tests.test_pipeline_contracts -v` → missing API 또는 새 assertion FAIL 확인.
- [ ] Validation rules에는 senior>total count/rate threshold와 station/time/date 구조적 집중의 판정 기준·집계 분모·근거를 기록할 계약을 둔다. 실제 값은 지금 정하지 않으며 Task 1 또는 Task 8 구현 시 2024 진단 결과로 확정한다. 정책이 미확정인 상태를 임의 기본값으로 WARNING-only 처리하지 않는다.
- [ ] Minimal: observed contract·manifest와 입력을 비교한다. Manifest 재생성으로 hash mismatch를 숨기지 않는다. Unknown year와 Gate 0 ERROR는 중단한다. Snapshot row count는 검사하되 값 품질은 후속 Gate에서 다룬다.
- [ ] GREEN: 동일 명령 PASS. Regression `python -m unittest discover -s subway/tests -v` 전체 PASS.
- [ ] Files만 commit: `feat: add subway clean contracts and validation gates`.

핵심 test assertion:

```python
self.assertEqual(pipeline_status([]), ("PIPELINE PASSED", 0))
self.assertEqual(pipeline_status([Finding("ERROR", "station", "UNKNOWN_CRS", "unverified")]), ("PIPELINE FAILED", 1))
```

## Task 2: Total/senior ridership clean·wide→long

**Files:** Create `subway/src/clean/ridership.py`, `subway/tests/test_clean_ridership.py`; Modify `subway/config/validation_rules.yaml` (time bins·boarding/line 명시 map).

**Interfaces:** `clean_ridership(frame: pd.DataFrame, dataset_id: str, year: int, rules: dict, source_file: str) -> StageResult`.

- [ ] RED: `test_explicit_hour_mapping`은 `06시간대이전`/`06시이전`→before_06, `24시간대이후`/`24시이후`→after_24, 중간 18열 `06-07시간대`–`23-24시간대`→06_07–23_24를 assert한다. 20 bins, source_hour_column 유지, sum 불변, unknown header ERROR. Before bin end=6/start=null, after bin start=24/end=null로 실제 미확정 시간 끝을 만들지 않는다.
- [ ] RED: `test_dates_boarding_and_identifiers`는 2024 날짜, 관측 label 승차/하차→boarding/alighting, 코드 문자열·row provenance 유지. `test_invalid_null_negative_duplicate`는 불정 날짜·필수 null·음수·logical key duplicate ERROR+exceptions, 입력 불변, dedup 없음. Senior line은 이 단계에서 null.
- [ ] `python -m unittest subway.tests.test_clean_ridership -v` → FAIL 확인.
- [ ] Minimal: source contract 20열만 melt, strict date/numeric parse, nullable 정수. Date coverage는 366일을 rules로 검사하되 station별 운영일을 추측하지 않는다. Senior line은 Task 3에서 완성한다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_ridership subway.tests.test_pipeline_contracts -v` PASS.
- [ ] Commit `feat: clean subway hourly ridership with explicit bins`.

```python
self.assertEqual(set(result.frame["hour_bin"]), {"before_06", "after_24"} | {f"{h:02d}_{h+1:02d}" for h in range(6, 24)})
self.assertIn("source_hour_column", result.frame)
```

## Task 3: Senior line crosswalk diagnostics·canonical identifiers

**Files:** Create `subway/src/transform/station_keys.py`, `subway/tests/test_station_keys.py`, `subway/config/station_aliases.csv` (header만; 지금 후보를 채택하지 않음).

**Interfaces:** `normalize_station_name(name: str) -> str` (NFC·앞뒤 공백만), `build_senior_crosswalk(senior: pd.DataFrame, total: pd.DataFrame, aliases: pd.DataFrame) -> StageResult`, `assign_station_ids(frame: pd.DataFrame) -> StageResult`.

- [ ] RED: `test_crosswalk_requires_unique_code_and_canonical_name`은 code 단독 후보 불가, 검증된 code+canonical name의 unique line만 부여, multiple lines ERROR, unmatched blocking diagnostic, 원본 identifiers 유지. `test_no_implicit_alias`는 괄호/문장부호 제거 금지. `test_ids_are_stable_and_line_sensitive`는 같은 이름 다른 호선의 ID 분리와 순서 불변.
- [ ] `python -m unittest subway.tests.test_station_keys -v` → FAIL.
- [ ] Minimal: alias 열 dataset_id,line,station_name_raw,station_name,evidence,verified. Verified만 적용, alias ambiguity ERROR. Senior line 미확정 후보는 진단만 하고 충분한 crosswalk 없이 부여하지 않는다. ID는 canonical line+name의 충돌 없는 안정 encoding으로 만든다. Alias로 code/line 모순을 숨기지 않는다.
- [ ] 실 Raw에서 8 exact unmatched를 포함한 모든 후보를 station exceptions에 출력. 개별 증거를 확인한 alias만 config에 추가. 해결 불가면 중단하며 COMPLETE로 표시하지 않는다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_ridership subway.tests.test_station_keys -v` PASS.
- [ ] Commit `feat: validate senior line crosswalk and station identities`.

```python
self.assertEqual(normalize_station_name(" 교대(법원·검찰청) "), "교대(법원·검찰청)")
self.assertTrue(any(f.severity == "ERROR" for f in ambiguous_result.findings))
```

## Task 4: Weather clean

**Files:** Create `subway/src/clean/weather.py`, `subway/tests/test_clean_weather.py`; Modify rules (108·2024 coverage).

**Interfaces:** `clean_weather(frame: pd.DataFrame, year: int, rules: dict, source_file: str) -> StageResult`.

- [ ] RED: `test_asos_108_leap_year_coverage`는 108/366 unique dates, 중복일·누락일·다른 지점 ERROR. `test_blank_precipitation_snow_remain_missing`은 blank NaN과 실제 0 구분, warning/metadata, 기온3·강수·풍속2·습도·신적설·적설 9개 변수 보존, 극한기온 분류 열 없음.
- [ ] `python -m unittest subway.tests.test_clean_weather -v` → FAIL.
- [ ] Minimal: source contract의 모든 변수를 명시 rename, 단위 metadata 보존. 공식 의미 검증 없으면 blank NaN. 비수치·날짜 오류는 보고하고 보간/보충하지 않는다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_weather subway.tests.test_pipeline_contracts -v` PASS.
- [ ] Commit `feat: clean ASOS weather without implicit zero filling`.

```python
self.assertEqual(result.frame["date"].nunique(), 366)
self.assertTrue(pd.isna(blank_result.frame.loc[0, "precipitation"]))
```

## Task 5: Station clean·alias diagnostics

**Files:** Create `subway/src/clean/station.py`, `subway/tests/test_clean_station.py`; Modify station_keys (match API), aliases (증거 확인 후만).

**Interfaces:** `clean_stations(frame: pd.DataFrame, rules: dict, source_file: str) -> StageResult`, `match_stations(ridership: pd.DataFrame, stations: pd.DataFrame, aliases: pd.DataFrame) -> StageResult` in station_keys; Task 3 ID와 aliases 소비.

- [ ] RED: `test_station_codes_not_shared_primary_key`는 code만 같고 line/name 다르면 자동join 금지. `test_alias_counts_and_unmatched_preserved`는 canonical/alias 구별, before/after count, 양쪽 unmatched 유지, duplicate coordinates ERROR. `test_crs_and_reference_dates_not_inferred`는 CRS 미확정 유지·source dates 보존·2025를2024로 변경 금지.
- [ ] `python -m unittest subway.tests.test_clean_station subway.tests.test_station_keys -v` → 새 tests FAIL.
- [ ] Minimal: 명시 line map, coordinate type/range 검증. 실제 alias 후보를 전부 진단하고 유사 문자열만으로 채택하지 않는다. 2024 운영 적합성·이름 변경은 source evidence로 검증한다. 276을 2024 기대 역 수에 강제하지 않는다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_ridership subway.tests.test_station_keys subway.tests.test_clean_station -v` PASS.
- [ ] Commit `feat: clean station sources and audit name matches`.

```python
self.assertEqual(result.frame.loc[0, "reference_date_raw"], "2025-08-14")
self.assertIn("station_name_raw", result.frame)
```

## Task 6: Population SpreadsheetML·gu/dong hierarchy

**Files:** Create `subway/src/ingest/spreadsheetml.py`, `subway/src/clean/population.py`, `subway/tests/test_clean_population.py`; Modify schema_inspector.py (필요 reader만 공유 추출), rules (Q2·bands).

**Interfaces:** `read_spreadsheetml(path: Path, sheet_name: str, encoding: str, title_row_count: int) -> pd.DataFrame`, `clean_population(frame: pd.DataFrame, hierarchy: pd.DataFrame, rules: dict, source_file: str) -> StageResult`. Hierarchy 열 source_block_id,level,gu,dong,evidence. 전체 source evidence로 구현 시 구성하며 순서만 추측해 fill하지 않는다.

- [ ] RED: `test_data_sheet_with_invalid_metadata_sheet`는 EUC-KR, 데이터sheet, title1, ss:Index sparse cells, source row 유지. `test_gu_dong_hierarchy_requires_evidence`는 subtotal 제외·동명중복 별gu 유지·고아동/미검증gu ERROR. `test_q2_total_and_all_eight_senior_bands`는 동일 모집단 `계`/Q2, Q3·Q4 혼입 없음·8band sum·band 누락/중복/음수 ERROR.
- [ ] `python -m unittest subway.tests.test_clean_population subway.tests.test_schema_inspector -v` → 새 tests FAIL.
- [ ] Minimal: 452 block 전체의 순서·subtotal·boundary 행정명/code 구조를 조사해 hierarchy를 검증. 계의 의미는 공식 metadata 또는 충분한 source evidence로 확인·문서화. 동명 중복·25구/426동 consistency를 전체 확인한 mapping만 사용한다. 손상 metadata sheet를 임의 수선하지 않는다.
- [ ] Total과 65+는 같은 `계`의 Q2를 사용. Bands는 `65~69세`, `70~74세`, `75~79세`, `80~84세`, `85~89세`, `90~94세`, `95~99세`, `100세 이상`. Total>0이면 share, total=0이면 null+report, 65+>total ERROR. 8band counts 유지.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest discover -s subway/tests -v` 전체 PASS.
- [ ] Commit `feat: clean Q2 population with verified district hierarchy`.

```python
self.assertEqual(result.frame.loc[0, "population_65_plus"], sum(range(1, 9)))  # fixture bands 1..8
self.assertFalse(result.frame.duplicated(["gu", "dong"]).any())
```

## Task 7: Boundary·shelter clean / CRS validation

**Files:** Create `subway/src/clean/spatial.py`, `subway/tests/test_clean_spatial.py`; Modify datasets/rules (확인한 source evidence만).

**Interfaces:** `clean_boundary(frame: gpd.GeoDataFrame, rules: dict, source_file: str) -> StageResult`, `clean_shelters(frame: pd.DataFrame, rules: dict, source_file: str) -> StageResult`.

- [ ] RED: `test_boundary_426_5179_validity`는 실제 기준426·5179·unique ADM_CD·valid nonempty polygon, invalid/unknown CRS ERROR·silent buffer repair 금지. Small fixture에는 별도 expected count rule 사용. `test_shelter_5186_and_uncertain_time`는 header5186·temporal warning·coordinate invalid exception·stable ID. 412는 관측 row 수만 의미.
- [ ] `python -m unittest subway.tests.test_clean_spatial -v` → FAIL.
- [ ] Minimal: gu/dong은 확인한 source 구조에서만 추출하고 Raw명/code 보존. Shelter 순번이 unique면 dataset prefix ID, 아니면 source row provenance로 충돌 방지. 5186 GeoParquet로 준비하고 core panel에 결합하지 않는다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_population subway.tests.test_clean_spatial subway.tests.test_schema_inspector -v` PASS.
- [ ] Commit `feat: validate boundary and shelter spatial layers`.

```python
self.assertEqual(boundary_result.frame.crs.to_epsg(), 5179)
self.assertTrue(boundary_result.frame.geometry.is_valid.all())
```

## Task 8: Senior-total integration·safe non_senior

**Files:** Create `subway/src/transform/ridership.py`, `subway/tests/test_transform_ridership.py`.

**Interfaces:** `integrate_ridership(senior: pd.DataFrame, total: pd.DataFrame) -> StageResult`. Task 3·5 IDs/line/name/match provenance와 Task 2 date/hour_bin/boarding_type 소비.

- [ ] RED: `test_full_outer_join_and_status`는 (date,canonical_station_id,hour_bin,boarding_type) key와 exact/canonical matched, alias matched, total only, senior only, ambiguous/rejected 상태, 양쪽 provenance 유지. `test_duplicates_block_many_to_many`는 duplicate ERROR+exception·행폭증 금지. `test_safe_difference_and_share`는 정상matched에서 senior<=total만 파생, 고립된 소수 senior>total은 WARNING+exception·두 파생null, unmatched 두 파생null, total0이면 share null. `test_senior_excess_escalation`은 설정된 count/rate threshold 초과 또는 station/time/date의 구조적 집중으로 join/schema 문제 가능성이 있으면 ERROR+pipeline blocking을 assert한다. 모든 초과 행의 exception·두 파생null·원본 불변은 severity와 무관하게 유지한다.
- [ ] `python -m unittest subway.tests.test_transform_ridership -v` → FAIL.
- [ ] Minimal: cardinality 검사 후 full outer. Rejected rows는 exceptions로 보존. Non_senior는 matched·양쪽 비음수/비결측·senior<=total 때만, share는 추가로 total>0 때만 생성. 0/0을0으로 처리하지 않는다. Date overlap/hour compatibility를 report한다. Senior>total의 전체 count/rate 및 station/time/date별 집중 진단을 기록하고, 근거 기반으로 확정한 validation_rules 정책에 따라 WARNING 또는 ERROR로 분류한다. Threshold 값과 구조적 집중 기준은 실제 2024 진단 후 Task 1 또는 이 Task 구현 시 확정하며 지금 임의로 정하지 않는다. Silent correction은 계속 금지한다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_ridership subway.tests.test_station_keys subway.tests.test_clean_station subway.tests.test_transform_ridership -v` PASS.
- [ ] Commit `feat: integrate ridership with auditable exceptions`.

```python
self.assertEqual(normal_result.frame.loc[0, "non_senior"], 7)  # fixture total=10, senior=3
self.assertTrue(pd.isna(excess_result.frame.loc[0, "non_senior"]))  # fixture total=10, senior=11
self.assertTrue(pd.isna(excess_result.frame.loc[0, "senior_share"]))
```

## Task 9: Station master·Point-in-Polygon·population mapping

**Files:** Create `subway/src/transform/spatial.py`, `subway/tests/test_transform_spatial.py`.

**Interfaces:** `build_station_master(stations: pd.DataFrame, ridership: pd.DataFrame) -> StageResult`, `map_stations_to_dongs(stations: pd.DataFrame, boundary: gpd.GeoDataFrame, station_crs: str | None) -> StageResult`, `map_population_to_boundary(population: pd.DataFrame, boundary: gpd.GeoDataFrame) -> StageResult`.

- [ ] RED: `test_unknown_station_crs_blocks_spatial_success`는 unknown CRS ERROR·성공map 없음. `test_zero_multiple_and_boundary_points_are_exceptions`는 5179로 transform 후 within, 0/multiple/경계point 예외·nearest 보정 금지. `test_population_gu_dong_bijection`는426 target code 전체unique 대응, 동명 별gu 구별, unmatched/duplicate ERROR+exception.
- [ ] `python -m unittest subway.tests.test_transform_spatial -v` → FAIL.
- [ ] Minimal: CRS·2024 적합성 evidence 기록 후 point/reproject. Source station unmatched는 pending으로 남기고 active ridership coverage와 구분한다. 0match가 서울 경계 밖이어도 exception을 보존. 제외/역외 정책은 근거 확인 전 미해결이며 COMPLETE 주장 금지. 인구 gu+dong 검증 후adm_cd, 426 consistency와 합계를 검증한다.
- [ ] GREEN 동일 명령 PASS; regression `python -m unittest subway.tests.test_clean_station subway.tests.test_clean_population subway.tests.test_clean_spatial subway.tests.test_transform_spatial -v` PASS.
- [ ] Commit `feat: map verified station coordinates and Q2 population`.

```python
self.assertTrue(any(f.severity == "ERROR" for f in unknown_crs_result.findings))
self.assertTrue(unknown_crs_result.frame.empty)
self.assertEqual(len(population_result.frame), 426)  # full reference fixture
```

## Task 10: E2E run_pipeline·deterministic validation

**Files:** Create `subway/run_pipeline.py`, `subway/tests/test_run_pipeline.py`; Modify artifacts/validation의 필요한 부분만.

**Interfaces:** `run_pipeline(repo_root: Path, year: int) -> int`, `main(argv: list[str] | None = None) -> int`. Task 1–9를 Gate0→clean→Gate1→transform→Gate2/3→발행 순서로 호출한다.

- [ ] RED: Temporary repo fixture `test_pipeline_all_outputs`는 7clean/4processed/6validation, 3status·exit mapping·Raw불변. `test_error_does_not_publish_stale_success`는 성공 후 ERROR run의 failed summary·이번 정상 산출물 미발행·이전 산출물 성공 오인 방지. `test_same_inputs_two_runs`는 모든 Parquet/reports hash 동일·빈CSV header·JSON sort·manifest 수동값과 Stage1산출물 불변·logs 외 timestamp 없음. 실패에도 diagnostics를 쓴다.
- [ ] `python -m unittest subway.tests.test_run_pipeline -v` → FAIL.
- [ ] Minimal: staging directory에 생성·검증 후 발행. Failed summary의 output_hashes에 이전 성공 산출물을 새run 결과처럼 싣지 않는다. 검증한 evidence는 config로 소비하고 매번 네트워크에 의존하지 않는다. Blocking을 warning으로 낮추지 않는다.
- [ ] GREEN 동일 명령 PASS; `python -m unittest discover -s subway/tests -v` 전체 PASS.
- [ ] 실제 입력 blocking 해소 후 `python subway/run_pipeline.py --year 2024` 2회 → exit0, ERROR0, warning 이유 기록, Raw11hash·manifest 불변, 전체 산출물hash 동일. `python subway/tools/inspect_raw_inputs.py --year 2024`→0, Stage1생성파일 diff 없음. 실제test 수와 library 환경을 기록한다.
- [ ] 새 versioned CSV/JSON은 LF를 확인. Baseline commit 후 재실행에서 `git diff --exit-code`, `git diff --cached --exit-code`→0, `git status --short`→빈 출력. Git add로 실제 변경을 숨기지 않는다.
- [ ] Commit `feat: orchestrate reproducible subway preprocessing` (코드/tests·검토한 산출물만; Raw staging 금지).

```python
self.assertEqual(run_pipeline(fixture_root, 2024), 0)
self.assertEqual(first_output_hashes, second_output_hashes)
self.assertEqual(raw_before_hashes, raw_after_hashes)
```

## Task 11: Stage 2 technical closeout documentation

**Files:** Create `docs/subway/2024-clean-transform-baseline.md`; Modify 개인 `subway/docs/analysis/00-report-map.md`, `methodology-log.md`, `ai-usage-log.md`. `02-clean-transform-baseline.md`는 실제 기록할 실적이 있을 때만 생성한다.

- [ ] 문서 Task에 RED/GREEN 구현 실적을 만들지 않는다. Task10의 검증 결과, alias/CRS/hierarchy evidence, report counts, unmatched/exception 처리, input/config/output hashes, 재현 명령을 모은다.
- [ ] Blocking·spatial coverage 미달·모집단 미확인이 있으면 Stage2 INCOMPLETE. ERROR0만으로 DoD 완료 처리하지 않는다.
- [ ] 실제 구현·검증된 전처리만 methodology adopted로 갱신한다. 통계모형은 candidate 유지. AI 자동 검사와 인간 검증을 분리한다.
- [ ] Link·명령·실적을 검토하고 전체 tests·2회pipeline/hash/Git clean·모든DoD 근거가 있을 때만 COMPLETE를 기록한다.
- [ ] Commit `docs: close subway clean transform stage`.

## Self-review·실행 시작 조건

추천 순서의 11 tasks를 유지했다. Task3 crosswalk와 Task5 alias evidence는 공유 API를 쓰되 독립 검증 가능해 분리했다. Task6에 SpreadsheetML reader의 최소 추출을 포함해 중복 reader·무관한 refactor를 피한다. Setup/config는 Task1, 전체 발행은 Task10에 모았다.

Coverage: 7clean은Task2/4/5/6/7, 4processed는Task8/9, Gate0–3/reports는Task1/8/9/10, CLI/provenance/reproducibility는Task10, closeout은Task11. 미확정 source evidence는Task3/5/6/9에 blocking으로 배치했다. Review Focus 5항목은 owner test에 대응하며 공통 StageResult/signature는 동일하다. 코드 예시의 result·fixture 변수는 해당 RED 단계에서 구성한다.

이번 Mission은 여기서 종료한다. 계획 리뷰와 별도 구현 시작 지시 전에는 Stage2 코드·alias값·CRS확정값·clean/processed 산출물을 만들지 않는다.


## P-S2-2RB authority addendum — 2026-10-06

The approved baseline now extends the original 7 datasets/11 files with the
exact DT_201004_O020003 Raw source: **8 datasets/12 files**. Task 6's approved
primary population contract is `population_direct_65_plus`: direct Q2 계 and
65세이상고령자, not summing incomplete old age bands. `population` remains
validation/supplementary and its historical 400 complete/26 incomplete dongs
remain evidence. Task 6 COMPLETE after exact 426 boundary keys, 400 equality,
26 direct coverage, deterministic outputs and full regression. The old plan's
age-band primary calculation is superseded only by this approved contract.
Exactly 55 station aliases and three transfer groups are adopted; Task 5 still
BLOCKED for unmatched/code/coordinate/CRS/temporal reasons. Task 9, Task 10 and
Task 11 remain NOT STARTED and are not authorized by this addendum.
See [authority adoption evidence](../../../subway/docs/analysis/03-approved-authority-adoption.md).


## Human-approved P-S2-2RD Task5 completion-definition addendum — 2026-10-07

This addendum supersedes the earlier Task5 requirement for resolving all source
identities/CRS/temporal uncertainty before completion. Task5 now closes when
every actual Task8 identity has one defensible eligibility/exclusion status,
core rows are preserved, and losses/assumptions/source limits are quantified.
The human approves EPSG4326 only as an analytical assumption and snapshot
coordinate equality only as a stability assumption. Source metadata, codes,
approved aliases and Raw remain unchanged. Current evidence:274 statuses,
237 ELIGIBLE,21 ELIGIBLE_CODE_WARNING,16 excluded; full122 tests PASS and actual
Task8/4/7 regression. Task5 COMPLETE under
eligibility_based_with_documented_exclusions. Task9/10/11 NOT STARTED; no
geometry/transformation/Point-in-Polygon/proximity work is performed.
See [Task5 contract evidence](../../../subway/docs/analysis/05-station-spatial-eligibility.md).

## Human-issued P-S2-T9 contract addendum — 2026-10-07

The Task9 Mission supersedes the older Task9 interfaces and universal spatial-success gate.
`build_station_master(eligibility: pd.DataFrame) -> StageResult` consumes the approved Task5 table,
preserves274 identities, and only258 eligible identities enter `map_stations_to_dongs(stations,boundary)`.
`map_population_to_boundary(population,boundary)` uses verified ADM_CD bijection with gu/dong diagnostics;
mapped-only enrichment preserves core rows. Strict within/touches exceptions are auditable, never repaired.
Task9 technical COMPLETE under strict_point_in_polygon_with_documented_exceptions after coverage/regression gates;
human review PENDING. Actual243 MAPPED/15 ZERO_MATCH. New18/full140 tests PASS, reversed output hashes equal,
12 Raw hashes unchanged. Task10/11 NOT STARTED. No production publication or final Stage2 closeout.
See [Task9 evidence](../../../subway/docs/analysis/06-station-dong-mapping.md).

## Human-issued P-S2-T10 latest-Mission addendum — 2026-10-07

The latest Task10 Mission supersedes earlier Task10 prompts. Task9 is HUMAN APPROVED2026-10-07.
Keep the full transport core and separate source coverage/current configurable study area/future regional extension.
Implement run_pipeline(repo_root,year) and main(argv), seven clean/four processed/six QA outputs, staging/rollback,
failed-summary stale-success protection, same-environment determinism and separate accepted2024 regression assertions.
Task9 technical ZERO_MATCH remains unchanged; study_area_status is independently derived from the whole validated union.
Current243 IN/15 OUT, all15 zero matches verified outside union; Task5-excluded16 remain outside geometry and unresolved in the274 master.
Future data sources/exposure strategies are not implemented. No analysis and no Task11 closeout.
Actual2024 two runs exit0, no blockingERROR, full158 tests,12Raw/historical evidence unchanged.
Task10 technical COMPLETE / human result review PENDING. Task11 NOT STARTED.
See [Task10 execution](../../../subway/docs/analysis/07-pipeline-orchestration.md).
