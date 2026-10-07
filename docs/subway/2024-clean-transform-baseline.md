# 2024 subway clean/transform 기술 baseline

## 1. 범위와 현재 상태

2026-10-07 기준 Stage 2 전처리 종료 기록이다. Stage 1 원래 baseline은 7 datasets / 11 physical Raw files였고, 승인된 `population_direct_65_plus` 확장 후 현재 입력은 8 datasets / 12 files다.
Task 9와 Task 10은 HUMAN APPROVED 2026-10-07이며, 이 승인 기록은 이번 Task 11 Mission을 근거로 한다. 인간이 Codex 자동 검증을 독립 실행했다는 뜻은 아니다.
Stage 2 / Task 11: **COMPLETE**. EDA·극한기온 분류·통계검정·회귀·공간 해석·정책 분석·시각화는 시작하지 않았다.

종료 기준 commit은 `b4785647ac2aec7e881062df5f3305307800d4c9`, 브랜치는 `subway/preprocessing-pipeline`이다. 이전 Task 9/10 문서의 PENDING은 당시 기록으로 보존한다. 재현된 pipeline summary의 `task10_human_review=PENDING`, `task11_status=NOT STARTED`도 Task 10 실행 계약의 기록이며, **최신 승인·종료 상태는 이 문서와 현재 report map**을 따른다. 이를 지우기 위한 production code/산출물 변경은 하지 않는다.

## 2. 입력 baseline

출처·기간·Raw 경로·라이선스 확인 상태는 [manifest](../../subway/data_manifest.csv), 정확한 12 Raw hashes 및 config/output hashes는 [canonical pipeline summary](../../subway/data/validation/pipeline_summary.json)를 참조한다. Raw는 수정하지 않는다.

| 입력 | 제공기관·기준 | 채택 역할 |
|---|---|---|
| senior ridership | 서울교통공사, 2024 일별·시간대별 노인 권종 | 65세 이상 이용량 core |
| total ridership | 서울교통공사, 2024 일별·시간대별 전체 | 전체 이용량 core |
| weather | 기상청, 서울 ASOS 108, 2024 일자료 | 별도 기상 제품; 현재 서울 exposure 자료 |
| station | 서울교통공사, 역 좌표 snapshot 276행 | 승인된 identity·좌표 eligibility에 한해 GIS 사용 |
| population_direct_65_plus | 서울특별시 공식 통계, 2024 Q2 | 직접 전체·65+ 집계 **PRIMARY** |
| population | 기존 연령대 SpreadsheetML, Q2–Q4 선택 | Q2의 독립 비교 **VALIDATION / SUPPLEMENTARY** |
| boundary | SGIS, 2024 Q2 / 2024-06-30, EPSG:5179 | 426개 서울 행정동 경계; SHP 및 sidecar 포함 |
| shelter | 서울 기후동행쉼터 snapshot 412행, EPSG:5186 | clean 보조 공간 layer; 2024 census 확정 아님 |

수집·schema 증거는 [Stage 1 baseline](2024-raw-schema-baseline.md), 직접 인구 채택 증거는 [승인된 authority adoption](../../subway/docs/analysis/03-approved-authority-adoption.md)에 있다. 보조 인구를 primary로 대체하거나 불완전한 26개 동을 보정·0 채움하지 않았다.

## 3. 실제 채택한 전처리

[한 명령 runner](../../subway/run_pipeline.py)는 기존 Tasks 1–9를 연결한다: Raw/schema/SHA·config 검사 → 실제 형식 ingest → wide-to-long 및 typed clean → 승인 alias/crosswalk → senior/total full outer integration → spatial eligibility → 경계·인구 계약 → strict Point-in-Polygon → 독립 study-area union 분류 → 회귀 gate → deterministic staging/publication.

20개 원래 hour_bin, 승차/하차, source row/file, 원본 code·name, alias/crosswalk evidence를 보존한다. 좌표·경계 repair, buffer, nearest fallback, 임의 역 매핑은 하지 않는다. 상세 구현과 Task 10 검증은 [orchestration 기록](../../subway/docs/analysis/07-pipeline-orchestration.md), 채택 방법 목록은 [methodology log](../../subway/docs/analysis/methodology-log.md)를 참조한다.

## 4. Core ridership accounting

grain/key는 `date × canonical_station_id × hour_bin × boarding_type`이며 양쪽 키 유일성을 검사한 one-to-one full outer join이다.

| 항목 | 승인된 값 |
|---|---:|
| integrated / matched | 3,988,480 / 3,987,960 |
| total-only / senior-only / ambiguous | 520 / 0 / 0 |
| senior > total 예외 | 3 |
| 전체 이용량 / 고령 이용량 | 3,302,748,460 / 462,981,953 |

total-only 520행의 전체 이용량 137도 보존한다. unmatched의 고령 값은 0으로 대체하지 않는다. 유효한 matched에서 `senior <= total`일 때만 `non_senior=total−senior`를 만들고, `senior_share`는 추가로 `total>0`일 때만 계산한다. 3개 초과 예외는 원값을 보존하고 두 파생값을 null로 둔다. 공간 필터로 `ridership_2024.parquet`를 줄이지 않았다.

## 5. 역 identity 및 공간 eligibility

[승인된 alias](../../subway/config/station_aliases.csv)·crosswalk와 [Task 5 계약](../../subway/config/spatial_eligibility_2024.yaml)을 따른다. 274개 원래 core identity는 모두 master에 남는다.

| Task 5 상태 | identity 수 |
|---|---:|
| ELIGIBLE / ELIGIBLE_CODE_WARNING | 237 / 21 |
| EXCLUDED_IDENTITY / EXCLUDED_COORDINATE / EXCLUDED_TEMPORAL | 12 / 4 / 0 |

16개 제외는 공간 subset에만 적용된다. 21개 외부 source-code 충돌은 warning을 유지하며 code를 화해·덮어쓰기하지 않았다. 원래 좌표 중복 등 source 진단은 summary/예외에 남기고, pinned evidence와 승인된 행별 제외 조건에 정확히 해당하는 경우만 처리한다. [Task 5 evidence](../../subway/data/validation/task5_spatial_eligibility.csv), [eligibility closure](../../subway/docs/analysis/05-station-spatial-eligibility.md)를 참조한다.

## 6. 현재 연구지역과 공간 coverage

세 층을 구분한다. **Source/core coverage**는 서울보다 넓고, 모든 승인된 Task 8 관측을 보존한다. **현재 contest 실증지역**은 서울특별시이며 [study_area_2024.yaml](../../subway/config/study_area_2024.yaml)에 명시한다. 서울 경계·인구·ASOS108·기후대응 공간자료와 따릉이 비교 맥락의 정합성을 기준으로 정했다. 따릉이는 이 subway pipeline의 8개 입력에 포함되지 않는다.

**향후 확장**은 경기·인천·수도권·다른 지역의 동등한 boundary/population/weather exposure/transport/climate-response 계약이 검증된 뒤 가능하다. 현재 해당 자료·adapter·지역 비교는 구현되지 않았고 지역 간 이동선택권 격차를 측정한 결과도 없다.

| 기준 | 결과 |
|---|---|
| Task 9 GIS input / MAPPED / ZERO_MATCH | 258 / 243 / 15 |
| BOUNDARY_POINT / MULTIPLE_MATCH | 0 / 0 |
| eligible study-area IN / OUT / UNRESOLVED | 243 / 15 / 0 |
| full master IN / OUT / UNRESOLVED | 243 / 15 / 16 |

전체 validated boundary union의 contains/touches를 좌표로 독립 검사했다. 15개는 기술적 `ZERO_MATCH`를 유지하며 **모두 union 밖**이다. 보고서에서는 “현재 서울 실증 연구범위 밖 역”으로 표현한다. bad coordinates·invalid ridership으로 간주하지 않는다. Task 5 제외 16개는 승인된 geometry 분류가 없어 unresolved이며 서울 밖으로 단정하지 않는다.

최종 243개 mapped subset은 원래 274개 identity의 **88.686131%**, 전체 이용량의 약 **93.541875%**, 고령 이용량의 약 **92.101731%**를 포괄한다. 분모는 full-core all-observations이며 [summary의 spatial_coverage](../../subway/data/validation/pipeline_summary.json)를 따른다. 누적 제외 비중은 authority/identity/coordinate 제외와 현재 지리적 범위 제외를 함께 포함하므로 전부 오류로 인한 데이터 손실이라고 표현하지 않는다. [Task 9 evidence](../../subway/docs/analysis/06-station-dong-mapping.md).

## 7. 인구·경계·쉼터 준비

공식 direct Q2 인구와 boundary의 `ADM_CD`는 **426/426 bijection PASS**다. 전체 인구 **9,619,861**, 65+ **1,785,286**이며, 구·동 명칭 및 상위 코드도 검사했다. 기존 연령대 자료의 유효한 400개 동은 **400/400 exact** 독립 비교를 통과했다. 불완전한 26개 동은 보조 진단으로 유지한다.

인구는 mapped 역에만 부착하고 unmapped 값은 null이다. 동 인구는 역 이용자의 모집단·거주지로 확정되지 않는다. 경계는 유효성·CRS·code·기준일 계약을 검사했고, 쉼터 412행은 clean layer만 준비했다. 쉼터 근접도·접근성·부족 여부는 계산하지 않았다.

## 8. Clean outputs

경로는 `subway/data/clean/` 기준이다. exact SHA-256은 canonical summary에만 참조한다.

| 파일 | 행 수 | 역할·사용 계약 |
|---|---:|---|
| senior_ridership_2024.parquet | 3,987,960 | 고령 long 관측; crosswalk/provenance 보존 |
| total_ridership_2024.parquet | 3,988,480 | 전체 long 관측; 원래 시간 구간 보존 |
| weather_2024.parquet | 366 | 서울 ASOS108 일자료; 결측 유지, 역별 exposure join 미수행 |
| stations.parquet | 276 | 좌표 원본 clean/audit; 모두 GIS 적격이라는 뜻 아님 |
| population_2024q2.parquet | 426 | direct 공식 PRIMARY 인구; 보조 source로 대체하지 않음 |
| dong_boundary_2024q2.parquet | 426 | validated 행정동 geometry |
| climate_shelters.parquet | 412 | snapshot 공간 layer; verified 2024 census 아님 |

## 9. Processed outputs

경로는 `subway/data/processed/` 기준이다. 자료는 아래 계약을 지키는 후속 분석 입력으로 준비되었으며 분석 결과는 아니다.

| 파일 | 행 수 | 역할·사용 계약 |
|---|---:|---|
| ridership_2024.parquet | 3,988,480 | 전체 transport core; join_status·예외·null 정책을 따라 연령 비교 |
| station_master.parquet | 274 | 모든 core identity·Task 5 eligibility·study_area_status 감사 |
| station_dong_map.parquet | 258 | 적격 역 strict GIS 결과; 243 mapped만 동 단위 분석에 사용 |
| dong_population_2024q2.parquet | 426 | 경계와 direct 인구 code 결합; 동 단위 reference |

## 10. Validation·warning·예외

현재 pipeline **ERROR 0 / WARNING 16 / INFO 2**, `PIPELINE PASSED WITH WARNINGS`다. 숫자는 중복 제거된 finding 행 수이며 영향받는 관측 수와 다르다. [quality report](../../subway/data/validation/data_quality_report.csv)의 모든 warning 의미는 다음과 같다.

| warning code / dataset | 의미·처리 |
|---|---|
| SUPPLEMENTARY_SOURCE_LIMITS / population | 기존 연령대 자료의 불완전 그룹 유지; primary direct 인구 사용 |
| SENIOR_EXCEEDS_TOTAL / ridership | 3 matched cells; 원값 보존, 파생값 null |
| TEMPORAL_UNCERTAINTY / shelter | snapshot이 2024 census임을 보증하지 않음 |
| APPROVED_ALIASES / station | 승인 alias 적용; evidence 보존 |
| APPROVED_COORDINATE_EXCLUSION / station | 승인된 중복 좌표 collision만 공간 제외; source 오류 진단 유지 |
| CRS_UNVERIFIED / station | source-specific CRS 미확인; 승인 EPSG:4326 분석 가정 |
| DOCUMENTED_IDENTITY_EXCLUSIONS / station | unmatched core identity 공간 제외; source-only row 감사 유지 |
| SOURCE_CODE_CONFLICT / station | 21개 code 충돌 미해결; 승인된 identity corroboration 및 warning 보존 |
| TASK5_SPATIAL_EXCLUSIONS / station | 16개 core identity 보존, 공간 제외 |
| TEMPORAL_UNCERTAINTY / station | snapshot의 연중 2024 적용은 증명되지 않음 |
| ZERO_MATCH / task9 | 15개 현재 연구지역 밖; 보정 없이 기술 상태 보존 |
| OBSERVATION_MISSING / weather (5 findings) | 일 최심신적설 350, 일 최심적설 338, 강수량 206, 최대 풍속 2, 평균 풍속 3 결측; 0 채움 없음 |

INFO 2개는 승인된 physical transfer coordinate 확인과 15개 독립 union 밖 판정이다. canonical QA는 [join report](../../subway/data/validation/join_report.csv)(520행), [ridership exceptions](../../subway/data/validation/exceptions_ridership.csv)(3행), [station exceptions](../../subway/data/validation/exceptions_station.csv)(69행), [spatial exceptions](../../subway/data/validation/exceptions_spatial.csv)(15행), quality report, pipeline summary 총 6개다. 기존 batch/task evidence는 보존한다. 실패는 nonzero 및 FAILED summary의 빈 output_hashes로 표시하며 이전 제품을 실패 실행의 결과로 간주하지 않는다.

## 11. 재현성과 최종 검증

저장소 root에서 실행한다.

```text
python -m unittest discover -s subway/tests -v
python subway/run_pipeline.py --year 2024
python subway/tools/inspect_raw_inputs.py --year 2024
git diff --check
```

Task 11 단일 최종 패스 결과: **158 tests OK**, pipeline exit **0** / ERROR **0** / WARNING **16** / INFO **2**, Raw inspection exit **0** / ERROR·WARNING·INFO 모두 **0**. 12 Raw hashes·config hashes·11 Parquet 행 수·16 output hashes·summary 바이트가 승인된 Task 10 baseline과 일치했고, manifest·역사 QA·기존 설정은 불변이다. `git diff --check` 및 문서 상대 링크 검사도 통과했다. Production code 변경은 없다. dependency 환경은 Python 3.11.9 / pandas 3.0.6 / numpy 2.4.6 / pyarrow 25.0.1 / GeoPandas 1.2.0 / Shapely 2.1.2 / pyproj 3.7.2 / PROJ 9.5.1이다. 환경별 정확한 값은 summary의 environment를 따른다.

같은 Raw/config/code/기록된 환경에서 Task 10 실제 두 실행의 byte determinism을 승인 baseline으로 유지한다. Task 11은 한 번 재실행하여 그 baseline과 비교하며 새 두 실행 실험을 반복하지 않는다. Windows `core.autocrlf=true`에서도 새 config/QA 8파일은 exact-file LF policy로 fresh checkout bytes가 검증되었다. 일반 code/docs의 기존 EOL 정책은 변경하지 않는다.

7 clean/4 processed Parquet는 로컬 생성물로 Git에서 제외되므로 fresh clone에서 한 명령으로 재생성한다. staging에서 모든 gate 통과 후, single-writer lock·기존 파일 backup·ordinary I/O rollback·summary-last publication을 적용한다. 다중 파일 전체가 동시에 바뀌는 filesystem transaction이나 power-loss/강제종료 보장은 아니다. 소비자는 lock이 없는 상태에서 success status와 hashes를 확인한다. 교차 버전 byte determinism은 보장하지 않는다.

## 12. 승인 가정과 한계

- 역 좌표 source-specific CRS는 명시적으로 검증되지 않았다. EPSG:4326은 승인된 **ANALYTICAL_ASSUMPTION**이다.
- 여러 동일 snapshot은 2024 내내 좌표가 연속적으로 같았다는 증명이 아니다. 정확한 historical 2024 KRIC station export는 확보하지 못했다.
- 21개 code 충돌은 미화해 warning이고, 16개 Task 5 identity는 공간 제외이며 15개 적격 역은 현재 연구범위 밖이다. core에서는 모두 보존한다.
- 쉼터 snapshot은 verified 2024 census가 아니다. ASOS108은 현재 서울 자료이며 연구지역 밖 역의 노출로 연결하지 않는다.
- aggregate 승하차는 trip purpose를 식별하지 못한다. 이후 결과도 최대 “기후회피형 이동과 일치하는 패턴”이며 “고령자가 더위/추위를 피하려고 지하철을 탔다”는 목적·인과 진술은 할 수 없다.
- 극한기온 효과와 지역 간 이동선택권 격차는 아직 분석하지 않았다. 탄소 감축은 정책 목적·맥락이며 emissions/mode-shift 증거 없는 측정 인과효과가 아니다.
- 기존 nonblocking minor: 계약 밖 plain pandas DataFrame boundary는 structured schema ERROR 전에 AttributeError를 낼 수 있다. 실제 GeoDataFrame pipeline에는 영향이 없어 이번 종료에서 수정하지 않는다.

## 13. Stage 2 Definition of Done와 보고서 근거 문장

**모든 gate PASS — Stage 2 COMPLETE / Task 11 COMPLETE.** Raw 불변·8/12 입력·7 clean/4 processed 재현·6 canonical QA·ERROR0·warning 의미·identity/crosswalk 감사·core accounting 보존·safe 파생값·direct 인구 authority·공간 eligibility 및 study-area 명시·core 관측 보존·한 명령 재현·승인 환경의 hashes·최신 report map/methodology/AI log·한계·downstream 계약의 모든 gate를 최종 패스로 확인했다.

아래는 전처리 근거용 초안이며 최종 5쪽 보고서나 분석 결론이 아니다.

| 보고서 항목 | 재사용 가능한 근거 문장 |
|---|---|
| 수집·source 선택 | 2024 승하차·기상과 Q2 경계·공식 direct 인구를 수집하고, 기존 연령대 자료는 보조 비교에 유지했다. |
| 전처리 | 원래 시간 구간과 provenance를 유지한 long 변환 후 승인 identity/crosswalk로 전체·고령 관측을 full outer 결합했다. |
| 품질 처리 | unmatched와 고령 초과 예외를 보존하고 파생값을 제한했으며, 미해결 역 문제는 core 삭제 없이 공간 eligibility로 분리했다. |
| 연구지역 | 서울을 현재 검증된 실증지역으로 설정하고, 서울 밖 역은 전체 core에 남긴 채 독립 경계 union 판정으로 구분했다. |
| 재현성 | 원본·설정·산출물 SHA-256과 QA를 기록하고 동일 환경의 한 명령 재현 및 안전한 publication을 검증했다. |
| 한계 | CRS·snapshot 시간 가정과 단일 서울 기상자료의 범위를 명시하며, 이후 서울 실증 결과를 다른 지역이나 이동 목적·인과효과로 일반화하지 않는다. |

## 14. Downstream analysis contract

원래 core는 유지한다. 현재 서울 동 단위 분석에서는 `MAPPED` 및 `IN_CURRENT_STUDY_AREA`에 해당하는 243 identity를 **명시적 분석 subset**으로 선택하고 사용 분모·coverage를 보고한다. 16 unresolved를 outside로 재분류하지 않는다. station-key join의 cardinality를 검사하여 many-to-many 증식을 막고, 520 unmatched 및 3 예외의 null 규칙을 따른다. 시간 구간은 기존 hour_bin을 사용하며 extreme/daytime 정의와 기상 exposure assignment는 이후 분석에서 검증한다. 현재 ASOS108을 밖 역에 붙이지 않는다.

동 인구는 동 reference이며 승객 개인의 거주지·성격이 아니다. 쉼터 공간자료는 준비된 입력일 뿐 접근성 지수·정책 효과가 아니다. 통계 방법은 모두 candidate다: Panel/Count Regression, PPML/Poisson, GAM/spline, Fixed Effects, interaction specifications, sensitivity analysis는 실제 fit·진단·승인 전 adopted로 기록하지 않는다.

합의된 질문은 그대로 이어간다.

- Primary: “극한기온에서 서울시 내 65세 이상 지하철 이용자의 이용 변화는 비고령층과 다르게 나타나는가?”
- Secondary 1: “이러한 연령별 차이는 10~16시 주간 비첨두 시간대에서 더 강하게 나타나는가?”
- Secondary 2: “이러한 차이는 서울 내 역·행정동별로 어떻게 다르며, 지역의 고령인구와 기후대응 공간 조건과 어떤 관계가 있는가?”

이후 현재 profile로 얻을 실증 결과의 적용 범위는 서울이다. 향후 비교 가능한 계약을 확보한 뒤 지역 이동선택권 격차로 확장할 수 있으나 현재 결과는 없다. [report map](../../subway/docs/analysis/00-report-map.md)과 [P-S2-T11 AI 사용 기록](../../subway/docs/analysis/ai-usage-log.md)에 근거를 연결한다. Task 11 이후 분석은 별도 지시 전 시작하지 않는다.
