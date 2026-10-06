# 개인 subway 방법론 기록

작성일: 2026-10-06. `adopted`는 실제 수행·검증된 범위만 의미한다. Stage 2 전처리 기법은 구현·검증 후에만 adopted로 갱신한다.

| 방법명 | 목적 | 선택 이유 | 상태 | 검증 근거 | 주의사항 |
|---|---|---|---|---|---|
| Raw schema inspection | 형식·컬럼·인코딩·행 수·CRS 입력 계약 확인 | 추측 기반 전처리 방지 | adopted | schema snapshot, source contracts, 16 tests, 실제 inspection exit 0 | loadability는 값·join·geometry 품질 보증이 아님 |
| SHA-256 provenance/integrity validation | 원본 snapshot 식별·불변 확인 | 파일명만으로 동일 입력 보장 불가 | adopted | inventory 11개, manifest primary 7개, Raw 전후 SHA-256 불변 | 출처의 신뢰성·모집단 적합성을 hash로 증명하지 못함 |
| Deterministic reproduction validation | 동일 입력의 검사 산출물 반복 재현 | 변경 추적·검토 가능성 확보 | adopted | 검사 2회 생성 파일 hash 불변, diff/staged diff 없음, Git clean | Stage 1 출력만 검증; Stage 2 Parquet는 미검증 |
| Panel / Count Regression with Interaction Effects | 극한기온에서 senior와 non-senior 이용량 반응 차이 검정 후보 | Primary question의 연령별 차이를 같은 패널 단위에서 비교 | candidate | 아직 fit·진단·검정 없음 | 모형·극한기온 정의·식별 조건은 분석 Stage에서 결정 |
| PPML / Poisson count regression | Count outcome에 적합한 모형 후보 검토 | 승하차 count의 분포에 맞는 사양 검토 | candidate | 실제 분포·overdispersion·diagnostic 미수행 | 진단 후 결정; 현재 실행·채택 아님 |
| GAM / spline | Temperature-response의 비선형성 탐색 후보 | 선형 함수로 충분한지 진단 후 필요할 때 검토 | candidate | 비선형 진단·fit 없음 | 필요할 때만 사용, 복잡도·해석·과적합 검토 |
| Fixed Effects | Station/date/time 등의 관측되지 않은 이질성 통제 후보 | 패널의 station-level heterogeneity와 시간 차이 통제 검토 | candidate | 식별·fit·비교 없음 | FE 조합의 공선성·식별 가능성은 분석 Stage에서 검토 |
| Sensitivity Analysis | Extreme-temperature 정의와 주요 가정 변화에 대한 견고성 검토 | 연구결과의 정의·사양 의존성을 평가 | candidate | 실제 분석·대안 비교 없음 | 분석과 기준 사양 확정 이후 수행 |

Interaction specification 후보는 `Extreme × Senior`, three-way specification 후보는 `Extreme × Senior × Daytime`이다. 이는 위 모형 안의 항 사양이며 독립적인 분석 알고리즘이 아니다. Daytime은 현재 10~16시 가설이고 최종 정의·검증은 분석 Stage에서 수행한다. Stage 2에서는 해당 indicator나 극한기온 분류·검정·모형 fit을 만들지 않고 원래 20개 hour_bin과 age comparison 정보를 보존한다.

Stage 2 계획의 wide→long, alias mapping, crosswalk, 인구 집계 및 Point-in-Polygon은 모두 **계획 상태**다. 이번 문서 작성으로 adopted가 되지 않는다. 분석 후보의 선택 이유는 검토 목적이며 특정 방법의 적합성이 검증되었다는 진술이 아니다.


## P-S2-2RB implemented-method update — 2026-10-06

The earlier “planned” preprocessing entries are historical. Explicit reviewed
station aliases/transfer validation and direct Q2 population aggregates are
now adopted within the approved scope: 55 station aliases, three transfer
groups, strict official code-parent/boundary attribute-set corroboration,
426 direct clean rows and independent 400-dong source comparison. The old
26 incomplete age-band dongs stay unchanged. Source SHA and reversed-row
deterministic CSV checks pass, with 102 unit tests and actual Task 8/4/7
regression. These are data-preparation checks, not statistical inference.
Point-in-Polygon remains unimplemented; Task 9 NOT STARTED. Detailed gates and
method limits: [Batch 2R-B record](03-approved-authority-adoption.md).


## P-S2-2RD implemented-method update — 2026-10-07

Station spatial eligibility is now adopted as a separate data-preparation
contract. All274 Task8 identities receive one status; core observations remain
intact. Only ELIGIBLE /ELIGIBLE_CODE_WARNING can enter the future spatial
subset. Exclusions are deterministic, with all/matched total and senior
denominators and observed loss reported separately. Source codes are preserved
and21 conflicts remain provenance warnings, not reconciled identifiers.

EPSG4326 is an approved analytical assumption; source-specific datum remains
unverified. SNAPSHOT_STABILITY_ASSUMPTION expresses multiple equal snapshots,
not continuous2024 observation. Known Amsa opening2024-08-10 is explicit;
Amsa has no accepted coordinate and is excluded. The three approved physical
transfer groups remain accepted; unresolved Magok/Balsan collision remains
excluded. These checks are not statistical inference or source repair.
Task5 COMPLETE means eligibility contract finalized with exclusions, not all
source problems fixed. Task9 Point-in-Polygon, CRS transformation and shelter
proximity remain NOT STARTED. Detailed evidence: [Task5 closure](05-station-spatial-eligibility.md).

## P-S2-T9 — 2026-10-07 strict spatial preprocessing adopted

Task5의 승인된274 identity master를 보존하며258 eligible에만 longitude=x/latitude=y,
EPSG:4326 ANALYTICAL_ASSUMPTION → EPSG:5179 변환 및 strict Point-in-Polygon 적용.
243 MAPPED/15 ZERO_MATCH/0 BOUNDARY_POINT/0 MULTIPLE_MATCH. 좌표·경계 보정과 nearest fallback 없음.
ADM_CD로426/426 population-boundary bijection 및 gu/dong 진단 후 mapped 역에만 직접 인구 부착.
원본 Task8 accounting/total-only/3 senior>total 예외 및12 Raw hashes 보존.
Core274 대비 누적 제외31 identities, total-all6.458125%, senior7.898269%; 분모 분리는
[Task9 증거](06-station-dong-mapping.md) 및 summary 참조. 173개 동 coverage는 전처리 QA뿐이다.
Task9 기술 구현 COMPLETE / 인간 결과 검토 PENDING. Task10/11 NOT STARTED.
EDA·회귀·가설검정·공간적 수요/접근성 해석은 수행하지 않았다.
