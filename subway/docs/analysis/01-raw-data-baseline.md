# Stage 1 Raw 데이터 연구 기록

개인 subway 분석 기록 / 작성일 2026-10-06 / Stage 1 COMPLETE. 확인된 사실, 처리 판단, 아직 미확정을 구분한다.

## Stage 목적

**처리 판단:** 분석에 앞서 실제 로컬 Raw의 형식·스키마·출처·무결성·재현성을 고정한다. Stage 1에서는 분석용 전처리, 결합, 통계분석을 수행하지 않는다.

## 최종보고서 연결 항목

활용 데이터, 출처와 기준시점, 수집 및 전처리 과정, 재현 코드, AI 사용 범위에 연결한다. 분석 결과·정책 효과의 근거로 사용하지 않는다. [보고서 지도](00-report-map.md) 참조.

## 사용 Raw 7종

| 데이터 | 확인된 사실 | 기준시점·용도에 대한 처리 판단 |
|---|---|---|
| senior_ridership | CP949 CSV, 199,398행, 호선 없음, 2024 날짜 366개 | 노인 승하차 입력; 검증된 crosswalk 후 total과 결합 |
| total_ridership | CP949 CSV, 199,424행, 호선 있음, 2024 날짜 366개 | 전체 승하차 입력; 매칭·수량 검증 후 파생값 생성 |
| weather | CP949 CSV, 366행, 지점 108, 2024-01-01–12-31 | 일별 기상 공변량 준비. 극한기온 분류는 이후 Stage |
| station | CP949 CSV, 276행, 위도·경도, 작성기준일 값 `2025-08-14` | 역 좌표 후보. CRS와 2024 적용 가능성 확인 필요 |
| population | EUC-KR SpreadsheetML, 데이터 8,136행, Q2–Q4 | 2024 Q2 선택 계획; 계의 모집단 의미와 gu/dong 계층 검증 필요 |
| boundary | 426 Polygon, EPSG:5179, manifest 기준 2024-06-30 | Q2 행정동 공간 기준; validity·인구 consistency는 Stage 2 |
| shelter | CP949 CSV, 412행, 좌표 header EPSG:5186 | 시점 불확실성을 유지한 보조 공간 layer; 2024 당시 수로 해석 금지 |

파일명·source header·출처·제공기관·URL·SHA-256은 [기술 baseline](../../../docs/subway/2024-raw-schema-baseline.md), [manifest](../../data_manifest.csv), [source contracts](../../config/source_contracts_2024.yaml)에 있다. 이 기록에서는 중복된 긴 목록을 관리하지 않는다.

## 선정 이유

**처리 판단:** 승하차 두 source는 고령 이용과 전체 이용의 비교 가능한 입력을 준비하기 위해, 기상은 일별 환경조건을 연결하기 위해 선택했다. 역 좌표·행정동 경계·인구는 역과 행정동의 공간 연결 및 65세 이상 인구 기준을 준비하기 위한 입력이다. 쉼터는 후속 공간 분석의 보조 자료로 준비한다. 이는 자료 구성 목적이며 연구 가설이나 효과가 입증되었다는 주장은 아니다.

## 확인된 관측 사실

- Stage 1 검사: 7종 / inventory 11 files / primary 7, ERROR/WARNING/INFO 0.
- Unit test 16/16 PASS. 동일 Raw 검사 2회에서 생성 파일 SHA-256과 Raw 11개 SHA-256 불변; Git working tree clean.
- Population의 손상된 CSV export 대신 동일 조건 SpreadsheetML `데이터` sheet를 선택했고 해당 형식 regression test가 있다. Raw를 수선하지 않았다.
- 2026-10-06 읽기 전용 사전 진단: senior `(역번호, 역명)` 273개, total 274개. total의 이 조합에서 여러 호선으로 연결되는 조합은 0개였으나 senior 8개 조합은 정확히 일치하지 않았다. 따라서 전체 crosswalk가 성립했다고 볼 수 없다.
- Total의 호선은 `1호선`–`8호선`, station은 `1`–`8`. 호선 표기만 통일한 진단에서 호선+원본 역명은 205개 공통, total only 69개, station only 71개였다. 원본 exact 문자열의 단순 결합은 0개 공통이었다. 진단용 표기 통일은 alias 채택이나 전처리 구현이 아니다.
- Population에 452개 연속 지역 블록, 서로 다른 `동별` 이름 451개, `항목`은 `계`·`한국인`이 관측되었다. 첫 지역 순서는 합계→종로구→동들→중구였지만 일부 순서만으로 전체 계층을 확정하지 않았다.

## 데이터 품질/제약

**확인된 사실:** source별 역명·호선·시간대 label 차이와 연도/시점 차이가 존재한다. Stage 1 validator는 파일 존재·읽기 가능·Shapefile CRS 등을 검사하며 값의 정상성, crosswalk, geometry validity, 계의 의미를 검사하지 않는다.

**아직 미확정:** 역 좌표 CRS와 2024 적용 가능성, alias 동일역 근거, 인구 구-동 소속과 모집단 정의, 강수·적설 blank 의미, 쉼터 snapshot 기준시점, 라이선스 등 manifest 빈 메타데이터. Senior가 total보다 큰 셀의 존재·빈도와 unmatched 행 수는 아직 집계하지 않았다.

## 처리 결정

**처리 판단:** Raw는 불변·Git 제외. 확인되지 않은 metadata는 비워 둔다. source schema와 원본 식별자를 보존하고, 의심값·미매칭을 조용히 보정하거나 제외하지 않는다. Population은 Q2를 경계 Q2 기준과 연결할 계획이며 `gu + dong`을 사용한다. 시간대 차이는 명시적 mapping으로 처리한다. 역 코드 단독 join, CRS 추정, blank→0 자동 변환은 금지한다.

## 아직 미확정인 사항

Stage 2 계획의 사전 해결 목록을 따른다. 통계모형, EDA 결과, 정책 제안과 기대효과는 아직 없다. Alias 후보는 실제 Raw 진단 후 근거를 검토하며 지금 config에 넣지 않는다.

## Stage 2로 넘긴 요구사항

7 clean + 4 processed 산출물, Gate 0–3 validation, 전체 unmatched 보존, 안전한 non_senior·senior_share, 인구 65+ 8개 연령대와 계 의미 검증, 426 경계 consistency, 검증된 CRS에만 Point-in-Polygon, deterministic 출력과 provenance. [구현 계획](../../../docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md) 참조.

## 보고서 문장 후보

아래는 검증 범위가 한정된 초안이며 최종 연구 결과 문장이 아니다.

> 분석 전 지하철 승하차, 기상, 역사 좌표, 등록인구, 행정동 경계 및 쉼터 등 7종 Raw의 실제 스키마와 출처를 기록하였다. 구성 파일을 포함한 11개 파일의 SHA-256을 고정하고 반복 검사에서 원본과 검사 산출물의 무결성 및 재현성을 확인하였다.

> 인구 입력은 동일 조건의 SpreadsheetML 데이터 sheet를 사용하였다. 행정동 인구 집계와 역-행정동 결합은 별도 전처리 단계에서 검증하며, 역 좌표 CRS와 일부 자료의 기준시점은 미확정 사항으로 관리한다.
