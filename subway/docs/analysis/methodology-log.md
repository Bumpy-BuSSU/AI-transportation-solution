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


## P-S3A-EDA — focused descriptive methods implemented / 2026-10-07

Stage 3A에서 아래 기술적 방법만 구현·산출물 수준에서 채택한다. 이는 통계모형 채택이나 가설검정이 아니다.

| 방법 | 상태 | 실제 범위·근거 |
|---|---|---|
| Current-study-area sample construction | adopted for EDA | `IN_CURRENT_STUDY_AREA` + 유효 mapped identity로 243역/3,557,520행; full Stage2 core는 불변 |
| Deterministic ASOS108 date join | adopted for EDA | 2024-01-01~12-31 366일 unique date, many-to-one join; 현재 서울 표본에만 사용 |
| Exact 10–16 daytime indicator | adopted as pre-specified definition | 기존 `10_11`~`15_16` 6개 구간; 결과를 본 뒤 창구 변경하지 않음 |
| Distribution/count diagnostics | adopted for EDA | senior/non-senior zero rate, mean/variance, quantiles, variance/mean ratio |
| Weather-only percentile diagnostics | adopted for EDA | mean/max/min 기온 분위수와 strict tail day 수; extreme cutoff로 채택하지 않음 |
| Weather-only equal-frequency temperature bins | adopted for descriptive EDA | 이용량과 무관하게 기상값만으로 10분위 bin; 동률 edge collapse |
| Hour/station descriptive aggregation | adopted for EDA | 시간대 연령 구조 및 243역 이질성; station-specific temperature effect는 미추정 |

실제 count diagnostics는 senior 평균 119.86, variance/mean 147.87, zero 2.47%; non-senior 평균 748.57, variance/mean 1,977.24, zero 0.50%다. 이는 단순 Poisson 등분산 가정이 자료의 기술적 분산 구조와 맞지 않음을 보여주지만, PPML의 채택/기각 자체를 뜻하지 않는다. 역별 senior share는 평균 15.76%, SD 약 6.25%p, 범위 약 3.09~46.14%로 이질성이 크다.

평일/주말 일평균 차이가 커서 calendar control이 후속 사양에서 필요하다. 기온-이용량 분위 프로파일은 선형 단조 관계로 보이지 않으므로 spline/GAM 또는 비선형 기온 사양을 후보로 유지한다. 다만 이는 season/calendar 미조정 EDA이므로 함수형 선택은 다음 사전 명세 단계에서 고정한다.

**계속 candidate:** extreme cutoff, PPML/Poisson, Negative Binomial, GAM/spline, Fixed Effects 조합, cluster-robust SE, `Extreme × Senior`, `Extreme × Senior × Daytime`, sensitivity thresholds. Stage3A에서는 어떠한 모형도 fit하지 않았다.


## P-S3B — confirmatory specification frozen pre-fit / 2026-10-07

Stage3A HUMAN APPROVED 후 결과를 보기 전에 다음 사양을 **adopted for confirmatory testing**으로 동결한다.

- 추론 단위: citywide daily weather exposure와 맞춘 H1 `date×age`, H2 `date×age×daytime`
- primary event: boarding only; alighting only는 sensitivity
- primary extreme: max-temp p90 32.75°C 이상, min-temp p10 -3.05°C 이하
- severe sensitivity: max-temp p95 33.675°C 이상, min-temp p05 -4.8°C 이하
- daytime: 원래 10_11~15_16 6개 bin
- primary family: PPML
- H1: date FE + age-specific month/DOW structure + `senior×hot/cold`
- H2: date FE + age/daytime lower-order 및 month/DOW differential structure + `senior×extreme×daytime`
- covariance: cluster by date
- multiple testing: four two-sided primary tests, Holm, alpha=0.05
- robustness: p95/p05, alighting, OLS log-ratio HAC(7)

Stage3A의 과산포는 PPML을 자동 기각하는 근거로 사용하지 않는다. 역별 고정 이질성은 고정된 243역을 daily citywide aggregate로 쓰는 H1/H2 primary에서 station FE로 재확장하지 않고, 후속 Secondary2에서 별도 분석한다.
실제 model fit/result는 아직 없음. 상세 계약: [09-confirmatory-specification.md](09-confirmatory-specification.md).


## P-S3B-RESULT — frozen confirmatory methods executed / 2026-10-07

사전 동결SPEC f5433eb… 및pre-fit serialization fix596f0db…로 실제 H1/H2를 실행했다. Scientific specification 변경 없음.
PPML/date FE·동결age/month/DOW/daytime 구조·date-cluster SE·4-test Holm·boarding primary·p95/p05/alighting sensitivity·OLS log-ratio HAC(7)는 **실제 수행됨**으로 기록한다.
H1 citywide date×age732rows, H2 date×age×daytime1,464rows; common-valid underlying cells,366date clusters다.6PPML full-rank/converged이며 네 primary Holm 기각0/4다.
앞선candidate/no-fit 문구는 당시단계의기록이다. 이번결과로 alternate NB/GAM/spline/새 FE/추가threshold를채택하지않았다. 사람결과검토는 PENDING이다.
수치·pointwise CI·raw/Holm p·모든 sensitivity와 해석한계는 [H1/H2 record](10-confirmatory-h1-h2.md)를 따른다. 정책인과·trip purpose·Secondary2 공간분석은실행하지않았다.
