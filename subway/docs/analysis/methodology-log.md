# 개인 subway 방법론 기록

초기 작성일: 2026-10-06. `adopted`는 실제 수행·검증된 범위만 의미한다. 첫 표와 이전 Tasks 섹션은 당시 기록이다. **최신 상태는 아래 P-S2-T11**을 따른다: Tasks9/10 HUMAN APPROVED 2026-10-07, Stage2 preprocessing COMPLETE. 통계 기법은 여전히 candidate다.

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

## P-S2-T10 — configurable current study scope and reproducible publication adopted

Task9 HUMAN APPROVED2026-10-07. Task10 technical COMPLETE / 인간 결과 검토 PENDING.
서울은 현재 실증 profile이며 source/core coverage는 더 넓다. Raw/config integrity와 기존 Tasks1–9를 연결하여
full Task8 core를 유지한7 clean/4 processed/6 validation 제품을 생성한다.
mapping_status와 독립 boundary-union study_area_status를 분리하고, 실제15 ZERO_MATCH 모두 현재 union 밖임을 확인했다.
ASOS108은 연구지역 밖 역의 노출로 붙이지 않았다. staged publication/rollback/failed-summary와 같은 환경에서의 두 실행 결정성을 검증했다.
CRS/snapshot 분석 가정, source exclusions 및 보조 인구 한계를 유지한다. 현재 primary/secondary 질문과 지역 확장 조건은
[Task10 record](07-pipeline-orchestration.md) 참조. 이후 비교 지역의 동등한 데이터·기상 전략이 필요하며 현재 지역 간 결과는 없다.
EDA·극한기온 분류·통계검정·접근성/이동선택권 지수는 수행하지 않았다. Task11 NOT STARTED.


## P-S2-T11 — adopted preprocessing baseline / 2026-10-07

Stage2 preprocessing COMPLETE; Task9/10 HUMAN APPROVED 2026-10-07.
현재 근거: [canonical technical closeout](../../../docs/subway/2024-clean-transform-baseline.md),
[pipeline summary](../../data/validation/pipeline_summary.json), [quality report](../../data/validation/data_quality_report.csv).
Codex 최종 단일 검증은158 tests OK, pipeline/Raw inspection exit0이다. 인간의 독립 실행으로 기록하지 않는다.

| 실제 채택 방법 | 상태 | 검증·사용 범위 |
|---|---|---|
| Raw schema inspection | adopted | 현재8datasets/12files 및 계약 검사; Raw inspection findings0 |
| SHA-256 provenance/integrity | adopted | 12Raw·config·제품 hashes 및 원본 불변; 출처 타당성의 증명은 아님 |
| Same-environment deterministic reproduction | adopted | Task10 두 실제 실행, Task11 승인 baseline과16output hashes/summary byte 일치; 교차 버전 보장 아님 |
| Wide-to-long ridership | adopted | 원래20hour bins·승차/하차·source provenance 보존 |
| Explicit station alias/crosswalk | adopted | 승인 alias·identity·transfer evidence 및 cardinality 검증 |
| Full outer senior/total integration | adopted | 3,988,480core/3,987,960matched/520total-only; 원량 보존 |
| Safe non_senior/senior_share | adopted | 유효 matched와senior<=total에만 차이; total>0에만 share;3예외 원값 보존·파생값null |
| Direct official65+ population authority | adopted | 426direct PRIMARY; 기존400exact 보조 비교/26불완전 미보정 |
| Explicit spatial eligibility | adopted | 274master 보존;258eligible/16공간 제외;21code 충돌warning |
| Strict Point-in-Polygon / CRS transformation | adopted | 승인EPSG4326가정→5179;243mapped/15zero;repair/nearest 없음 |
| ADM_CD population-boundary bijection | adopted | 426/426PASS;인구9,619,861/65+1,785,286; mapped 역에만 부착 |
| Configurable study-area union classification | adopted | independent union243IN/15OUT;16excluded unresolved; source/core와서울 실증범위 분리 |
| Staged deterministic publication | adopted | single writer/ordinary I/O rollback/summary-last;실패nonzero·빈output hashes;전원중단transaction 보장 아님 |

Panel/Count Regression, PPML/Poisson, GAM/spline, Fixed Effects, interaction specifications 및
sensitivity analysis는 **CANDIDATE**다. fit·분포진단·극한기온 분류·검정·추정은 수행하지 않았고
이번 closeout으로 adopted가 되지 않는다. 현재 질문·10~16시 가설·trip purpose 해석 한계는 유지한다.
Shelter proximity/accessibility와 지역 비교도 미구현이다. Task11 COMPLETE; EDA/statistical analysis NOT STARTED.
