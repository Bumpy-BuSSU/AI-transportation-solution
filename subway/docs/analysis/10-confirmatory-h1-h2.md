# Stage 3B: frozen H1/H2 confirmatory results

기록일: 2026-10-07. **기술 실행 COMPLETE / HUMAN APPROVED 2026-10-07**.
Stage2 COMPLETE/HUMAN APPROVED, Stage3A HUMAN APPROVED 2026-10-07를 기반으로 한다.
Primary 결과와 반대·불확실한 결과 및 모든 사전 지정 sensitivity를 함께 보고한다.

## CONFIRMED FACT — 사전 동결과 pre-fit 수정 이력

- SPEC_FREEZE_SHA: `f5433eb98d96d8098c265de0859282dcc53046f1`.
- 최초 implementation SHA: `e91af4e959eae4d1b8380c985370cf928b5368b9`.
- latest pre-fit YAML fix 및 이번 실제 실행의 implementation SHA: `596f0dbe00951a7444f30fc4fa41e88a529e6e8e`.
- 첫 인간 local focused 실행은 **11 tests / 11 ERROR**로 config validation에서 중단되었다. PyYAML이 따옴표 없는 `10_11`~`15_16`을 문자열이 아닌 scalar로 해석한 serialization defect였다.
- `596f0db…`는 여섯 bin에 문자열 따옴표만 추가한 **PRE-FIT IMPLEMENTATION correction**이다. Threshold, event, model, FE, clustering, Holm family, sensitivity는 변경하지 않았다. 그때 coefficient/p-value/model result가 생성되지 않아 contamination은 없었다.
- 이번 Codex 실행은 위 fix를 pull한 뒤 **focused11 OK → 실제 confirmatory exit0 → full178 OK(한 번)** 순서다. Production code와 frozen YAML을 수정하지 않았다. 결과 commit은 이 문서를 추가한 Git commit이며 실행 source SHA와 구분한다.

동결 계약은 [09 specification](09-confirmatory-specification.md), [frozen config](../../config/confirmatory_analysis_2024.yaml), [serialized model spec](../../results/models/confirmatory_model_spec.json)에 있다.

## CONFIRMED FACT — 표본·노출·극한일

현재 서울 고정243역, Stage3A base3,557,520cells 중1개 senior>total 셀은 원값을 보존하고 양쪽 연령집단의 confirmatory aggregate에서 모두 제외했다. Common-valid 총3,557,519cells이며 boarding1,778,759 / alighting1,778,760cells다.
ASOS108은 하루 하나의 citywide exposure이므로 station/hour 셀을 독립 기온 반복으로 취급하지 않는다.
H1은366dates×2age=**732rows**, H2는366dates×2age×2daytime=**1,464rows**이며 두 모델 모두366 date clusters다. H2 strata는 같은 날짜 cluster에 속한다.

| 정의 | 동결 규칙 | 실제 일 수 |
|---|---|---:|
| primary hot | temperature_max >=32.75°C, weather empirical p90 | 37 |
| primary cold | temperature_min <=-3.05°C, weather empirical p10 | 37 |
| sensitivity hot | temperature_max >=33.675°C, p95 | 19 |
| sensitivity cold | temperature_min <=-4.8°C, p05 | 20 |

이들은2024 서울 경험분포 기반 **연구용 상대적 극한일**이며 KMA 공식 특보 기준이 아니다. Daytime은 사전 고정 [10:00,16:00): `10_11,11_12,12_13,13_14,14_15,15_16` 문자열이다. Primary는boarding only, event sensitivity는alighting only다.

일별 실제 입력은 [daily age counts](../../results/tables/confirmatory_daily_age_counts.csv), [daily age/daytime counts](../../results/tables/confirmatory_daily_age_daytime_counts.csv), [extreme days](../../results/tables/extreme_temperature_days_2024.csv)에 있다. 양쪽 집단의 support_cells와 원량 합계를 원본 common-valid base에서 재계산해 exact 일치를 확인했다. 인구·쉼터 변수나 Secondary2 공간분석은 사용하지 않았다.

## MODEL ESTIMATE — frozen PPML 사양

H1:

`log E[count_dg] = date FE + senior + senior×month FE + senior×DOW FE + senior×hot + senior×cold`

H2:

`log E[count_dgt] = date FE + senior + daytime + senior×daytime + senior×month FE + daytime×month FE + senior×daytime×month FE + senior×DOW FE + daytime×DOW FE + senior×daytime×DOW FE + hot×daytime + cold×daytime + senior×hot + senior×cold + senior×hot×daytime + senior×cold×daytime`

둘 다 Poisson log-link GLM으로 PPML fit, SE는 **date-cluster robust**다. Date FE가 공통 date-level exposure main effects를 흡수하므로 별도 hot/cold main effect를 추정하지 않았다. 결과를 보고 control/FE/모형/관측을 변경하지 않았다.

Primary four-test family는 H1 hot/cold senior differential, H2 hot/cold daytime amplification이다. 아래 원 p는 양측이며 Holm alpha=.05를 네 개에만 적용했다. IRR=exp(beta), relative%=100×(exp(beta)−1)이다. H2 tau는 daytime과 나머지 시간 사이 age-differential association 차이이며 H1과 같은 estimand가 아니다.

| model/event/threshold | hypothesis | estimate | SE | 95% CI (beta) | IRR | relative % | raw p | Holm p |
|---|---|---|---|---|---|---|---|---|
| H1_PPML/boarding/p90_p10 | h1_cold_senior_differential | -0.007464 | 0.014898 | [-0.036663, 0.021735] | 0.992564 | -0.744% | 0.616357 | 1.000000 |
| H1_PPML/boarding/p90_p10 | h1_hot_senior_differential | -0.010800 | 0.010773 | [-0.031915, 0.010315] | 0.989258 | -1.074% | 0.316116 | 0.948348 |
| H2_PPML/boarding/p90_p10 | h2_cold_daytime_amplification | -0.010386 | 0.039158 | [-0.087134, 0.066362] | 0.989667 | -1.033% | 0.790824 | 1.000000 |
| H2_PPML/boarding/p90_p10 | h2_hot_daytime_amplification | -0.047685 | 0.035214 | [-0.116704, 0.021334] | 0.953434 | -4.657% | 0.175695 | 0.702781 |

## STATISTICAL UNCERTAINTY — primary 판단과 daytime contrast

네 primary 점추정은 모두 음수지만, **모든95% CI는0을 포함하고 Holm 기각은0/4**다.
H1 hot/cold 연령 차이와 H2 hot/cold 주간 증폭은 이 사전 사양에서 **NOT SUPPORTED**다. 이는 차이가 없다는 증명도 아니며, opposite 방향의 효과가 입증되었다는 뜻도 아니다.
위95% CI는 normal-reference **pointwise** CI이고 Holm-adjusted simultaneous CI가 아니다. 불확실성을 생략하지 않는다.

H2 daytime 내 senior differential은 해당 모델의 `senior×extreme + senior×extreme×daytime` 선형조합이며 **전체 covariance의 교차항**으로 SE를 계산한다. H1 coefficient를 H2 tau와 합산하지 않는다. 추가 contrast는 네 confirmatory family에 포함되지 않으며 아래 p는 보정하지 않은 사전 지정 추가 보고다.

| model/event/threshold | hypothesis | estimate | SE | 95% CI (beta) | IRR | relative % | raw p |
|---|---|---|---|---|---|---|---|
| H2_PPML/boarding/p90_p10 | h2_cold_senior_differential_during_daytime | -0.017107 | 0.027308 | [-0.070631, 0.036417] | 0.983039 | -1.696% | 0.531032 |
| H2_PPML/boarding/p90_p10 | h2_hot_senior_differential_during_daytime | -0.039654 | 0.026993 | [-0.092560, 0.013251] | 0.961122 | -3.888% | 0.141816 |

## MODEL ESTIMATE / STATISTICAL UNCERTAINTY — 모든 지정 sensitivity

아래는boarding p95/p05, alighting p90/p10 및 boarding HAC benchmarks 전체다. 민감도 p는raw이며 primary Holm family의 기각 판단으로 대체하지 않는다. 명칭은 [전체 sensitivity CSV](../../results/models/confirmatory_sensitivity_results.csv)와 같다.

| model/event/threshold | hypothesis | estimate | SE | 95% CI (beta) | IRR | relative % | raw p |
|---|---|---|---|---|---|---|---|
| H1_HAC_LOG_RATIO/boarding/p90_p10 | cold_primary | -0.008835 | 0.011839 | [-0.032039, 0.014370] | 0.991204 | -0.880% | 0.455542 |
| H1_HAC_LOG_RATIO/boarding/p90_p10 | hot_primary | -0.011947 | 0.009368 | [-0.030308, 0.006414] | 0.988124 | -1.188% | 0.202197 |
| H1_PPML/alighting/p90_p10 | h1_cold_senior_differential | -0.008033 | 0.015282 | [-0.037985, 0.021919] | 0.991999 | -0.800% | 0.599121 |
| H1_PPML/alighting/p90_p10 | h1_hot_senior_differential | -0.010954 | 0.010873 | [-0.032266, 0.010358] | 0.989106 | -1.089% | 0.313744 |
| H1_PPML/boarding/p95_p05 | h1_cold_senior_differential | -0.011188 | 0.019803 | [-0.050000, 0.027625] | 0.988875 | -1.113% | 0.572097 |
| H1_PPML/boarding/p95_p05 | h1_hot_senior_differential | -0.001095 | 0.015533 | [-0.031538, 0.029349] | 0.998906 | -0.109% | 0.943823 |
| H2_HAC_DELTA_LOG_RATIO/boarding/p90_p10 | cold_primary | 0.001789 | 0.042329 | [-0.081175, 0.084752] | 1.001790 | 0.179% | 0.966291 |
| H2_HAC_DELTA_LOG_RATIO/boarding/p90_p10 | hot_primary | -0.079896 | 0.060521 | [-0.198516, 0.038724] | 0.923212 | -7.679% | 0.186792 |
| H2_PPML/alighting/p90_p10 | h2_cold_daytime_amplification | -0.008248 | 0.038367 | [-0.083445, 0.066949] | 0.991786 | -0.821% | 0.829790 |
| H2_PPML/alighting/p90_p10 | h2_cold_senior_differential_during_daytime | -0.017483 | 0.026699 | [-0.069813, 0.034847] | 0.982669 | -1.733% | 0.512584 |
| H2_PPML/alighting/p90_p10 | h2_hot_daytime_amplification | -0.048649 | 0.035076 | [-0.117398, 0.020099] | 0.952515 | -4.749% | 0.165453 |
| H2_PPML/alighting/p90_p10 | h2_hot_senior_differential_during_daytime | -0.039797 | 0.026906 | [-0.092533, 0.012938] | 0.960984 | -3.902% | 0.139114 |
| H2_PPML/boarding/p95_p05 | h2_cold_daytime_amplification | -0.022478 | 0.043917 | [-0.108554, 0.063598] | 0.977772 | -2.223% | 0.608766 |
| H2_PPML/boarding/p95_p05 | h2_cold_senior_differential_during_daytime | -0.025348 | 0.029573 | [-0.083310, 0.032614] | 0.974971 | -2.503% | 0.391368 |
| H2_PPML/boarding/p95_p05 | h2_hot_daytime_amplification | -0.026464 | 0.035907 | [-0.096840, 0.043912] | 0.973883 | -2.612% | 0.461115 |
| H2_PPML/boarding/p95_p05 | h2_hot_senior_differential_during_daytime | -0.013900 | 0.022874 | [-0.058732, 0.030932] | 0.986196 | -1.380% | 0.543400 |

HAC H1은일별 `log(senior/non_senior)`, H2는 `log(senior_daytime/non_senior_daytime)−log(senior_other/non_senior_other)` outcome이다. 둘 다 `hot+cold+month FE+DOW FE` OLS, Newey-West **maxlags=7**이다. 일별 paired counts는 모두 양수여서 zero correction 없이 실행했다. HAC 행의 exp(beta)는 **log-ratio 변화의 승수**이며 PPML count IRR로 해석하지 않는다.

p95/p05와alighting primary estimands는 음의 점추정을 유지하지만 모두raw p>.05다. HAC H1 hot/cold 및H2 hot도음의 점추정, H2 cold는작은 양의 점추정으로 모두 CI가0을 포함한다. 민감도 결과도 명확한 가설 지지로 바꾸지 않는다.

## CONFIRMED FACT — 수치·회귀 검증과 artifacts

6개 PPML 모두converged=True. 각H1 design rank/columns=**386/386**, 각H2=**426/426**; nobs732/1,464, date clusters366이다. Frozen full design을 유지했다.
구현의 gate는 전체 fitted params/SE/p의finite 값을 검사하고, linear contrast variance의finite/nonnegative 조건을 검사한다. 모든 versioned 결과의 SE는양수이고 coefficient/CI/p/exp 변환도finite이며, 보고된 추론 수치에 covariance 오류는 발견되지 않았다. 전체 covariance 행렬의positive-definiteness를 추가 보증하는 진술은 하지 않는다.
Holm을statsmodels의 별도 routine과 비교하고 normal p/CI·IRR·relative%를 재계산해 일치를 확인했다. 기존12 Raw, Stage2 products, Stage3A artifacts/base hashes는 불변이며 이번 실행의 code/config hashes도pre-fit SHA와 일치한다.

```text
python -m unittest subway.tests.test_confirmatory -v    # 11 OK
python subway/run_confirmatory.py --year 2024          # exit0
python -m unittest discover -s subway/tests -v         # 178 OK, once
git diff --check                                      # PASS
```

생성된10개 result artifacts:

- models: [model spec](../../results/models/confirmatory_model_spec.json), [H1 results](../../results/models/h1_primary_results.csv), [H2 results](../../results/models/h2_primary_results.csv), [sensitivities](../../results/models/confirmatory_sensitivity_results.csv), [four-test family](../../results/models/confirmatory_test_family.csv), [summary](../../results/models/confirmatory_summary.json).
- tables: 위daily age / age-daytime / extreme days3개.
- figure: [effects PNG](../../results/figures/confirmatory_effects.png), relative%와pointwise95% CI를표시한다. 불확실성 구간 전체와0 reference가 보이도록 확인했다. 추가 figure는 만들지 않았다.

summary의 boarding/alighting_sample.model_status=NOT_FITTED는 **table-construction 단계에서 받은 nested metadata**다. 최종 fit 상태는top-level status와model_meta의6개converged 기록을 따른다. 역사·stage metadata를 지우기 위한 코드 변경은 하지 않았다.

## INTERPRETATION — 범위와 제한

추정량은 달·요일의 age/daytime 차이와 date 공통요인을 통제한 상대적 이용량 **association**이다. 절대적인 고령 이용량 변화나 기온의 인과효과가 아니다. 동일일 cluster는 날짜 내 상관을 다루며 날짜 간 serial dependence를 직접 보장하지 않는다. HAC(7) log-ratio benchmark는 별도의 민감도다. 한 도시·한 해, tail days37/37 및19/20의 자료 범위를 유지한다.
Station CRS/snapshot 가정·21개 code 경고·16개 공간 제외·15개 서울 밖 역의 한계는 [Stage2 baseline](../../../docs/subway/2024-clean-transform-baseline.md)을 따른다. 지금 자료로 trip purpose, individual behavior, rider residence, causal shelter-seeking, carbon reduction, inter-regional inequality를 추론하지 않는다.
현재 primary 결과로는 “고령자가 더위/추위를 피하기 위해 지하철을 탔다” 또는 명확한 연령별 차이가 관찰되었다고 결론내리지 않는다. 최대 해석 가능 범위와 현재 근거를 구분하며 정책권고는 작성하지 않았다.

**No scientific specification changed after results. No threshold tuned. No spatial Secondary2 started. No trip-purpose or causal policy conclusion.**

## HUMAN APPROVAL — 2026-10-07

사용자는 ChatGPT의 원격 코드·결과·문서 정밀검토 후 Stage 3B H1/H2 결과를 승인했다. 승인 범위는 사전 동결된 H1/H2 confirmatory 결과와 그 해석 한계까지이며, 정책결론·Secondary 2 공간분석·trip-purpose 또는 인과 해석을 승인한 것이 아니다. 현재 결론은 네 primary test 모두 Holm 보정 후 기각되지 않아 **H1/H2 NOT SUPPORTED under the frozen specification**이며, 이는 차이가 없다는 증명이 아니다.
