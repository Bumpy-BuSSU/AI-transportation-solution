# Stage 3C: controlled reconstruction and Secondary 2 evidence ledger

기록일: 2026-10-07. **실제 데이터 기술 실행 완료 / 인간 과학적 결과 검토 PENDING**.
Stage 3C의 과학적 완료를 선언하지 않는다. 정책·최종보고서 작성은 시작하지 않았다.

## Provenance and approved decisions

신뢰 가능한 재구축 baseline: `d24830a7a4de3a41753fe53f8ccfa8ba6a8f2186`.
이는 승인된 Stage 3B 완료 `d7fe7aadaa80de3831b1cfde6d566ba87d516bc7`의 후손이며 차이는 설계·계획·승인 기록뿐이다.
누락된 `f002cc1`은 제한된 복구 검색에서 찾지 못했다. 이번 코드는 **controlled reconstruction after loss of an unrecoverable local checkpoint**이며 이전 구현의 복구가 아니다.
이전 “29 PASS”는 검증하지 못한 역사적 보고로, 이번 테스트 근거에 포함하지 않는다. 이전 실제 수치는 독립 acceptance checkpoints로만 비교했으며 production 추정기에 넣지 않았다.

승인된 [design](../../../docs/superpowers/specs/2026-10-07-subway-spatial-heterogeneity-design.md)과 [plan](../../../docs/superpowers/plans/2026-10-07-subway-spatial-heterogeneity.md)은 보존했다.
민감도 실패 처리는 **과학적 gate 이후 인간이 승인한 failure-handling protocol amendment**이다. 원래 사전 지정된 규칙이라고 기술하지 않는다.
최신 재구축 Mission이 계획의 중간 커밋·push 절차를 대체한다: 최종 로컬 재구축 커밋 하나 후 STOP, push/PR/merge 없음.
결과 커밋은 이 문서를 도입한 Git 커밋(`git log -1 --format=%H -- subway/docs/analysis/11-spatial-heterogeneity.md`)으로 식별한다. 생성 산출물에는 baseline 및 실행 코드 SHA-256을 기록했다.

## A–B. Purpose and data

Secondary 2: 서울 내 역·행정동별 연령 상대반응의 이질성이 고령인구와 관측된 기후대응 공간 조건에 어떻게 관련되는가?
Layer A는 역별 기술적 점추정 분포, Primary Layer B는 사전 선택한 두 문맥 변수의 공동 조절 연관, p95/p05는 같은 사양의 유일한 극한 threshold sensitivity다.

출처·URL·Raw SHA-256은 기존 [manifest](../../data_manifest.csv), [source contracts](../../config/source_contracts_2024.yaml), [전처리 baseline](../../../docs/subway/2024-clean-transform-baseline.md)을 재사용한다.

| 승인 데이터 | 제공기관 | 기간/시점 | 변수 | 공간·시간 단위 |
|---|---|---|---|---|
| 노인 및 전체 승하차 | 서울교통공사 | 2024-01-01–12-31 | senior, total, non_senior | 역×날짜×시간구간×승하차; 이번은 boarding |
| ASOS108 일기상 | 기상청 | 2024 전년 | temperature_max/min | 서울 한 관측소×날짜 |
| 직접 65+ 주민등록인구 | 서울특별시 기본통계 DT_201004_O020003 | 2024 Q2/06-30 | 총인구, 65+, 고령인구비중 | 행정동; 외국인 포함 승인 집계 |
| 행정동 경계 | SGIS | 2024 Q2/06-30 | ADM_CD, geometry | 426행정동; EPSG:5179 |
| 역 좌표·승인 station-dong map | 서울교통공사 및 Stage 2 | 승인 snapshot-stability 가정 | 역 정체성, 좌표, ADM_CD | 역; source-specific CRS 미확인 한계 유지 |
| 기후동행쉼터 | 서울특별시 | Raw snapshot; 2024 완전성·시점 미확정 | 412 point, 좌표 | 쉼터; source EPSG:5186 |

## C. Preprocessing and QA — CONFIRMED FACT

현재 분석대상 **243개 지하철역이 위치한 173개 행정동**. 서울 전체 문맥은426동이며173동을 전체의 대표표본으로 해석하지 않는다.
Station-days **88,938 =243×366**, common-valid boarding cells **1,778,759**.
Senior/non-senior zero station-days **0/0**. 영일 제외나 pseudocount 없이 balanced panel을 사용했다.

`2024-04-20 / 올림픽공원(한국체대) / 21–22 / senior187 > total106` 한 셀은 원값과 Stage 3A invalid flag를 보존하고 양쪽 연령집단 집계에서 공통 제외했다.
15 outside/16 unresolved 역의 Stage 2 결정을 다시 열지 않았다. Raw·Stage 2·3A·3B 산출물은 변경하지 않았다.

쉼터 raw412 / strict unique PIP412(100%), ZERO/BOUNDARY/MULTIPLE/invalid-coordinate **0/0/0/0**.
EPSG:5186→5179 strict within만 사용; buffer/snap/repair/nearest assignment 없음. Exception 표는 header만 있는 빈 표로 명시적으로 발행했다.
역별 최단 쉼터 직선거리는 유효 좌표의 모든 관측 point로 계산한 기술적 문맥이며 regression moderator가 아니다.

| 노출 | threshold °C | 일 수 |
|---|---:|---:|
| Hot p90 | max≥32.75 |37|
| Cold p10 | min≤-3.05 |37|
| Hot p95 | max≥33.675 |19|
| Cold p05 | min≤-4.8 |20|

173개 고유 station-containing 동을 한 번씩 사용해 각 moderator를 sample SD(`ddof=1`)로 표준화했다.
고령비중 mean0.184023212933219/SD0.042332227716294; shelters/10k mean0.8519821601482883/SD1.737471263639569.
Moderator correlation **-0.03725136330283785**. 두 slope design 모두38열/full rank38.

## D. Frozen statistical method

분석단위는 station-day, outcome `log(senior/non_senior)`다.
Layer A: 역별 OLS, hot/cold + month FE + DOW FE + intercept; 역별 추론·유의성 분류 없음.
Primary Layer B: station/date FE + hot/cold×두 z-moderator 네 target + 각 moderator×month(2..12) 및×DOW(1..6); January/Monday reference.
Balanced-panel double demeaning으로 FE를 흡수하며 fixture에서 explicit dummy-FE OLS와 일치를 검증했다.
OLS covariance는 `statsmodels.stats.sandwich_covariance.cov_cluster_2groups(..., use_correction=False)`.
Cluster는 정확히 ADM_CD173/date366. Normal-reference 양측 p와 pointwise95% CI; Holm alpha.05는 **primary 네 검정에만** 적용한다.
동일 표본·moderator·control·FE·covariance를 유지한 p95/p05 sensitivity 하나만 실행했다.

## E. Results — distinguish descriptive estimates and inference

### Layer A: descriptive point estimates only

| Descriptive coefficient | median | Q25 | Q75 | min | max | negative point estimates |
|---|---:|---:|---:|---:|---:|---:|
| Hot p90 | -0.004783410957461168 | -0.01820754218427782 | 0.01021221909245738 | -0.1017069289571636 | 0.08327108400753636 | 61.72839506% |
| Cold p10 | -0.009610326051229764 | -0.01791199820054042 | 0.00107323471807897 | -0.08570598396028896 | 0.1803501790804397 | 71.60493827% |

음수 비중은 음의 점추정 비중이며 유의한 역 비중이나 위험 역 분류가 아니다.
[역별 표](../../results/tables/station_extreme_heterogeneity.csv), [paired map](../../results/figures/station_extreme_heterogeneity.png).

### Primary Layer B: valid frozen inference

| Moderation (per one SD) | β | SE | pointwise 95% CI | raw p | Holm p | Holm reject |
|---|---:|---:|---|---:|---:|---|
| Hot × senior population share | 0.0011721125506326 | 0.0010416207869425 | [-0.0008694266773229, 0.0032136517785883] | 0.2604714140950214 | 0.7190417895179239 | False |
| Cold × senior population share | -0.0072203866339546 | 0.0011405787888051 | [-0.009455879981543, -0.0049848932863662] | 2.444338330777708e-10 | 9.777353323110831e-10 | True |
| Hot × shelters/10k | -0.0021656691548385 | 0.0024055169618598 | [-0.006880395764284, 0.002549057454607] | 0.367964550389231 | 0.7190417895179239 | False |
| Cold × shelters/10k | 0.0030755862375073 | 0.0026157714999733 | [-0.0020512316942267, 0.0082024041692413] | 0.2396805965059746 | 0.7190417895179239 | False |

Holm 기각은1/4: Cold×senior-population-share. 이는 station-weighted local-context association이다.
[정밀 CSV](../../results/models/spatial_moderation_primary.csv), [pointwise CI figure](../../results/figures/spatial_moderation_effects.png).

### p95/p05: retained point estimates, inference NOT ESTIMABLE

| Moderation (per one SD) | β | raw target variance | inference status |
|---|---:|---:|---|
| Hot × senior population share | 0.0035541025540569 | -5.168962841020486e-06 | NOT ESTIMABLE |
| Cold × senior population share | -0.0041228391879592 | -4.699743265250515e-06 | NOT ESTIMABLE |
| Hot × shelters/10k | -0.0004598578599467 | -1.2479116573284e-06 | NOT ESTIMABLE |
| Cold × shelters/10k | 0.0005516948515419 | 3.466442195916638e-06 | NOT ESTIMABLE |

고정된 two-way covariance가 자연스럽게 target variance **3/4 음수**를 산출했다. 4번째 양의 분산 계수도 포함해 **전체 sensitivity inferential layer를 NOT ESTIMABLE**로 처리했다.
모든 SE/CI/raw p/adjusted p/significance classification은 CSV에서 빈 값(NA), 실패 사유는 `NOT_ESTIMABLE_INVALID_TWOWAY_COVARIANCE`다.
분산 abs, sqrt(abs), clipping, eigenvalue/PSD correction, ADM/date-only 또는 HC/HAC fallback은 사용하지 않았다.
원래 covariance38×38, 모든 design-column 이름, raw target diagonals, negative/invalid counts, cluster counts, correction flag를 [summary](../../results/models/spatial_moderation_summary.json)에 그대로 보존했다.
[민감도 CSV](../../results/models/spatial_moderation_sensitivity.csv). **NOT ESTIMABLE은 “not significant”가 아니다.**

## F. Supported interpretation and boundaries

Supported: 이 고정 사양에서 Cold×고령인구비중의 음의 조절 연관이 Holm을 통과했다. 한 SD 높은 고령인구비중의 동에 위치한 역에서 cold day의 senior/non-senior boarding log-ratio 상대변화가 더 음의 방향이었다.
다른 세 Primary target은 Holm 비기각이며 영효과의 증명이 아니다. Layer A 이질성은 기술적 분포다. 기존 Stage 3B citywide H1/H2 NOT SUPPORTED 결과는 변경하지 않았다.

Not supported: 인과효과, 승객 거주지, 직접적인 “고령자가 지하철을 쉼터로 사용”, 위험 역 분류, 쉼터 부족·정책 사각지대·탄소감축·지역 간 격차.
Sensitivity inference failure를 비유의성이나 Primary 강건성의 증명으로 쓰지 않는다.
한계: 단일 ASOS citywide exposure, 단일 연도, 역별 가중 estimand, 미측정 지역 요인, 쉼터 snapshot 시점·완전성, 직선거리와 실제 접근성의 차이, 역 좌표의 승인된 분석 가정, 집계자료의 거주·이동목적 미식별.

## G–H. AI disclosure and reproducibility

Human: 설계·Stage 3B 결과 승인, 공분산 실패의 scientific gate 및 전체 민감도 추론 억제 amendment 승인, 재구축 Mission 승인. 이번 자동 테스트·실데이터 결과를 인간이 독립 재실행했다고 주장하지 않는다. **이번 결과의 인간 검토는 PENDING**.
ChatGPT/Codex: 승인된 계획을 해석하고 코드·TDD·실데이터 실행·독립 수치 비교·결과 요약 및 disclosure 근거를 작성했다. 대화 전체를 최종보고서에 복제하지 않는다. 상세 역할은 [AI log](ai-usage-log.md).

실행 환경: Python3.11.9 / pandas3.0.6 / numpy2.4.6 / pyarrow25.0.1 / statsmodels0.15.0; 정확한 GeoPandas/matplotlib 버전은 summary에 있다.
현재 환경의 기존 pyarrow로 **production Parquet runner를 실제 실행**했다. 종전 환경의 pyarrow 부재는 역사적 한계이며 dependency를 추가·변경하지 않았다.

명령:
```text
python -m unittest subway.tests.test_spatial_heterogeneity -v
python subway/run_spatial_heterogeneity.py --year 2024
python -m unittest discover -s subway/tests -v
git diff --check
git status --short
```
실제 executable은 `C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe`.
새 focused17 tests PASS(모델·문맥14 + runner/그림3). 최초 RED13→GREEN13, runner RED3→GREEN16, 정밀 검토 회귀 RED1→최종GREEN17을 이번 세션에서 확인했다. 전체 회귀 결과는 아래 검증 기록에 기입한다.
입력은 승인된 analysis_base, station_dong_map, dong_population_2024q2, climate_shelters Parquet 및 기존 summary/config다.
코드는 [runner](../../run_spatial_heterogeneity.py), [analysis](../../src/analysis/spatial_heterogeneity.py), [figures](../../src/analysis/spatial_figures.py), [config](../../config/spatial_heterogeneity_2024.yaml), [tests](../../tests/test_spatial_heterogeneity.py).
네 tables, 두 model CSV, 한 summary JSON, 세 PNG를 gate 통과 후 staging에서 발행한다. Runtime log와 large Parquet는 커밋하지 않는다.
문서 갱신 전에 기존173 tracked baseline 파일 모두의 SHA-256 불변을 확인했다. 갱신 후에는 허용된 report-map/methodology/AI 문서 세 개만 달라졌으며, 나머지 기존 파일·accepted inputs·Stage3C output/code hashes를 다시 확인했다.
Fixture runner는 두 번 byte-identical. 실제 runner 재실행 여부·전체 test 결과·최종 검토 근거는 아래에 별도 기록해 추론 실행과 문서 수정을 구분한다.

## Final precision review and post-review verification

Fresh-context read-only reviewer가 common-valid filtering 뒤 한 역의 모든 셀이 제외될 때 표본에서 그 역이 사라질 수 있는 fail-closed gap을 지적했다.
실제 데이터는 이미243역/88938일을 유지하여 수치 영향은 없었지만, 이를 fix-now로 분류했다.
새 회귀 `test_panel_entire_invalid_station_cannot_disappear_from_required_population`을 실제 함수에서 RED(ValueError not raised)로 확인한 뒤, 집계 후 required station identity set을 비교하는 최소 gate를 추가했다. Focused17 PASS.
동일 reviewer가 이 finding의 해결을 읽기 전용으로 확인했다. 나머지 분석/시각화 리팩터링은 하지 않았다.

코드 변경 때문에 필요한 실제 production runner 최종 재실행은 exit0이었다. 네 tables·두 model CSV·세 PNG(9개)는 첫 실행과 SHA-256 byte-identical; summary는 수정된 code_hashes만 달라졌다.
모든 데이터·수치 acceptance checkpoints와 원시 covariance diagnostics는 재일치했다. Primary의 beta/SE/CI/raw p/Holm 및 sensitivity beta가 모두 불변이다.
그림3개를 직접 열어 전체 지리 범위·공통0중심 척도·pointwise CI와0기준·읽을 수 있는 caption·역별 유의성/위험 분류 부재를 시각 검토했다.


최종 전체 회귀: `python -m unittest discover -s subway/tests -v` → **195 tests, OK, exit0** (51.960s). 기존178개 + 새17개이며 이전 미복구29개를 포함했다는 뜻은 아니다.
최초 전체 회귀194 tests도 통과했고, 정밀 검토 후 gate/회귀 테스트 변경 때문에 최종195개를 재실행했다. 이미 통과한 검증의 불필요한 반복이 아니다.
최종 focused: `python -m unittest subway.tests.test_spatial_heterogeneity -v` →17 tests OK/exit0.
실제 실행: `python subway/run_spatial_heterogeneity.py --year 2024` →최초/필요한 최종 재실행 모두 exit0, 동일 승인 Parquet 경로 사용.
독립 acceptance 검증은 현재 실제 산출물을 이전 보고의 근사값과 비교했고 모든 sample/point estimate/primary inference/covariance failure checkpoints가 허용 반올림 범위 안에서 재현됐다.
최종 Git hygiene는 로컬 커밋 전에 `git diff --check` 및 `git diff --cached --check`로 검사하고, 커밋 후 `git status --short`로 clean을 확인한다. 정확한 commit SHA/status는 종료 보고에 제공한다.
기술 검증을 마쳤으나 **인간 과학적 결과 검토 PENDING**이며 Stage3C 과학적 완료를 선언하지 않는다.
