# Stage 3A: Focused 2024 subway EDA

기록일: 2026-10-07. 기준 WIP commit: `2422ab46edf0c224249c1f70ee9c75280c4ff40e`.

## 1. 목적과 상태

Stage 2에서 승인된 2024 전처리 산출물만 사용해, 후속 극한기온 가설검정의 표본·분포·시간대·역 이질성을 기술적으로 진단한다. 이 단계는 **EDA only**다. 극한기온 cutoff, 통계모형, 가설검정, 인과·정책 결론은 채택하지 않는다.

현재 상태는 **기술 산출물 생성 완료 / 사람 검토 및 최종 local regression gate 대기**다. `eda_summary.json`도 `human_eda_review=PENDING`, `extreme_threshold_status=NOT ADOPTED`, `hypothesis_test=NOT PERFORMED`, `regression=NOT FITTED`, `policy_conclusion=NONE`을 기록한다.

## 2. 분석 표본

Stage2 full core는 수정하지 않는다. `station_master`와 `station_dong_map`의 현재 연구지역 상태를 사용해 서울 표본을 선택한다.

| 단계 | 행 | 역 identity | 처리 |
|---|---:|---:|---|
| Stage2 full core | 3,988,480 | 274 | 원본 분석 core 보존 |
| Current Seoul study area | 3,557,520 | 243 | 현재 실증 분석 표본 |
| Matched | 3,557,520 | 243 | unmatched 0 |
| Valid age comparison | 3,557,519 | 243 | senior>total 1셀만 연령비교 metric에서 제외 |

현재 범위에서 빠지는 430,960행은 full core에서 삭제되지 않는다. 219,600행/15 identity는 `OUTSIDE_CURRENT_STUDY_AREA`, 211,360행/16 identity는 `UNRESOLVED_STUDY_AREA_STATUS`다. 미확정 16역을 서울 밖으로 재분류하지 않는다.

서울 표본의 senior>total 1셀은 원값을 유지하고 `non_senior`, `senior_share` null 정책을 그대로 보존한다.

## 3. 시간·기상 결합 계약

기존 base grain은 `date × canonical_station_id × hour_bin × boarding_type`이다. 서울 ASOS108 일자료는 `date` unique를 검증한 뒤 many-to-one으로 결합한다. 현재 표본의 날짜 누락은 0이고, mean/max/min 기온은 366일 모두 관측된다.

사전 지정 daytime은 정확히 다음 6개 원래 interval이다.

`10_11, 11_12, 12_13, 13_14, 14_15, 15_16`

이는 `10:00 <= interval < 16:00`에 해당한다. WIP 중 그림의 시간순 표시 문제를 발견했으나 checkpoint에는 `hour_order`와 회귀 테스트가 반영되어 있다. 원격 versioned CSV와 PNG에서 `before_06`이 첫 구간, `after_24`가 마지막 구간임을 확인했다.

## 4. 기상 기술통계

기온 변수의 결측은 없다.

| 변수 | 평균 | 최소 | p05 | p50 | p95 | 최대 |
|---|---:|---:|---:|---:|---:|---:|
| 일평균기온 | 14.88°C | -11.7 | -0.775 | 16.3 | 29.4 | 31.8 |
| 일최고기온 | 19.54°C | -8.2 | 2.55 | 21.65 | 33.675 | 36.4 |
| 일최저기온 | 10.98°C | -14.0 | -4.8 | 11.9 | 26.875 | 28.2 |

p05/p95는 **후보 진단값일 뿐 극한기온 정의가 아니다**. 예를 들어 일최고기온은 p05 아래 19일, p95 위 19일이고, 일최저기온도 p05 아래 18일, p95 위 19일이다. 동률 때문에 분위수와 strict tail day 수는 정확히 5%와 다를 수 있다.

강수·적설·풍속의 Stage2 결측은 그대로 유지하며 0 대체하지 않는다.

## 5. 연령별 count 분포

공통 valid age-comparison 3,557,519셀 기준이다.

| 지표 | 65+ | Non-senior |
|---|---:|---:|
| 총 이용 count | 426,414,205 | 2,663,038,519 |
| 셀 평균 | 119.86 | 748.57 |
| zero rate | 2.47% | 0.50% |
| variance / mean | 147.87 | 1,977.24 |
| p95 | 368 | 2,478 |
| p99 | 630 | 5,715 |

두 집단 모두 count의 분산이 평균보다 훨씬 크다. 이는 후속 count-model에서 분산 가정과 robust inference를 검토해야 한다는 진단이지, 특정 Poisson/PPML/NB 모형의 자동 채택 또는 기각 근거는 아니다.

## 6. Calendar와 시간대 구조

요일 효과가 크다.

| 구분 | 일수 | 65+ 일평균 | Non-senior 일평균 | 전체 일평균 |
|---|---:|---:|---:|---:|
| 평일 | 262 | 1,260,632 | 8,109,699 | 9,370,331 |
| 주말 | 104 | 924,314 | 5,175,935 | 6,100,250 |

따라서 후속 기온 모형에서 calendar adjustment를 생략하면 기온·계절과 이용량의 관계를 혼동할 가능성이 크다.

시간대 profile에서는 10–16시가 고령층 이용 구조에서 상대적으로 더 큰 비중을 차지한다. 원자료 direction별 연간 count를 분모로 계산하면 10–16시는 65+의 약 48.7%(승차), 49.1%(하차), non-senior의 약 27.7%(승차), 29.1%(하차)다. **이는 baseline 시간대 구조이며 극한기온에서 차이가 더 커진다는 증거가 아니다.**

## 7. 기온-이용량 기술 프로파일

일최고/일최저기온을 이용량과 무관한 weather-only equal-frequency 10분위로 나누고, 각 연령집단의 연평균 일 이용량을 100으로 정규화했다.

두 프로파일 모두 단조 선형 형태가 아니다. 중간 기온 구간에서 높고 낮거나 높은 기온 극단에서 낮아지는 형태가 관찰된다. 특히 non-senior 변동폭이 일부 구간에서 더 크지만, weekend fraction 및 계절 구성이 bin마다 다르고 어떤 calendar/season control도 적용하지 않았으므로 **연령별 기온 효과로 해석할 수 없다**.

이 결과는 다음 단계에서 선형 단일 slope만 고정하기보다 비선형 함수형을 사전 검토할 근거다. 그러나 spline/GAM 또는 threshold를 결과가 강해지는 방향으로 고르지 않는다.

## 8. 역별 이질성

243개 역의 연간 valid-cell total count는 약 1.00M~58.86M으로 넓게 분포한다. 역별 senior share는 평균 15.76%, SD 약 6.25%p, 범위 약 3.09~46.14%다. station-level baseline 차이가 크므로 후속 패널 모형에서 station fixed effects 또는 동등한 통제가 중요한 후보가 된다.

이 수치는 역 이용자의 거주 고령인구 비율을 뜻하지 않으며, 역을 “좋은/나쁜 이동선택권”으로 순위화하지 않는다.

## 9. 산출물

Versioned tables:
- `eda_sample_accounting.csv`
- `eda_exclusions.csv`
- `eda_weather_summary.csv`
- `eda_temperature_quantiles.csv`
- `eda_count_diagnostics.csv`
- `eda_daily_age_weather.csv`
- `eda_calendar_profile.csv`
- `eda_hourly_profile.csv`
- `eda_station_summary.csv`
- `eda_station_distribution.csv`
- `eda_temperature_profiles.csv`
- `eda_summary.json`

Figures:
- `eda_temperature_distribution.png`
- `eda_temperature_max_age_profile.png`
- `eda_temperature_min_age_profile.png`
- `eda_hourly_age_profile.png`
- `eda_station_heterogeneity.png`

Local generated base:
- `subway/data/analysis/analysis_base_2024.parquet`

## 10. 가능한 해석과 불가능한 해석

현재 확인된 것은 표본 구성과 기술 패턴이다.

가능:
- 현재 서울 분석표본은 243역이며 기상 날짜 결합이 완전함
- 10–16시가 원래 hour-bin으로 정확히 정의 가능함
- 평일/주말, 역별, 연령별 count 구조 차이가 큼
- 기온 분위 기술 profile은 단순 선형 관계로 보이지 않음

불가능:
- “극한기온이 고령층 이용을 증가/감소시켰다”
- “고령자가 기후회피 목적으로 지하철을 탔다”
- “10–16시에 극한기온 고령효과가 더 강하다”
- 통계적 유의성·인과효과·정책 효과·지역 간 격차

## 11. 다음 의사결정 gate

Stage3A 사람 검토 후, 결과 크기를 보고 기준을 움직이지 않고 다음 분석 사양을 먼저 고정한다.

1. hot/cold exposure 정의: weather-only 원칙과 sensitivity 후보
2. nonlinear temperature control 또는 smooth specification
3. station/time/calendar fixed effects 구조
4. count model family 및 robust/cluster inference
5. Primary `Extreme × Senior`, Secondary1 `Extreme × Senior × Daytime`의 사전 명세
6. 그 뒤에만 실제 hypothesis model fit

Codex 중단 전 focused tests 9개 PASS가 보고되었다. ChatGPT는 checkpoint의 코드·CSV·summary·PNG를 원격 검토했으나 로컬 테스트를 독립 실행하지 않았다. Stage3A 최종 승인 전 로컬에서 focused test, `run_eda --year 2024`, full regression을 한 번 실행하고 Git clean을 확인한다.
