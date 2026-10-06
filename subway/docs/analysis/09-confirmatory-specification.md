# Stage 3B confirmatory specification freeze

기록일: 2026-10-07.

이 문서는 Stage 3A 기술 EDA의 사람 승인 후, H1/H2 결과를 보기 **전에** 고정한 confirmatory analysis 계약이다.
이 커밋 자체가 `SPEC_FREEZE_SHA`이며, 이후 실제 모델 결과 문서에서 SHA를 명시한다.

## 1. 사람 승인과 분석 질문

Stage 3A는 2026-10-07 사람 검토를 통과했다. focused test 9개와 전체 회귀 167개가 로컬에서 OK였고,
실제 EDA runner도 정상 종료했다. 이 승인은 극한기온 효과나 가설을 승인했다는 뜻이 아니다.

H1: 극한기온에서 서울시 내 65세 이상 지하철 이용 변화가 비고령층과 다른가?

H2: 그 연령별 차이가 사전 정의한 10–16시에 더 강한가?

Secondary 2의 역·행정동 공간 이질성은 이 Stage에서 시작하지 않는다.

## 2. 추론 단위

서울 ASOS108 기온은 날짜별 하나의 citywide exposure다.
따라서 약 355만 station-hour-direction cell을 독립적인 기온 노출 반복으로 취급하지 않는다.

H1은 `date × age_group`, H2는 `date × age_group × daytime`로 집계한 뒤 추론한다.
243개 역의 고정된 서울 연구범위는 동일하게 유지한다. 역 이질성은 후속 Secondary 2에서 별도로 다룬다.

## 3. 공통 유효 셀

Stage3A의 `age_comparison_valid=True` 셀만 사용한다.
서울 표본의 `senior>total` 1셀은 원값을 고치지 않고, senior와 non-senior 양쪽 aggregate에서 모두 제외한다.
따라서 두 연령집단은 같은 underlying station/hour support를 사용한다.

## 4. 사건과 시간창

Primary event는 **boarding only**다. 승차와 하차를 독립 여행처럼 합산하지 않는다.
Alighting only는 사전 지정 sensitivity다.

Daytime은 결과를 보기 전에 정한 `10:00 <= interval < 16:00`이며 정확한 source bins는
`10_11, 11_12, 12_13, 13_14, 14_15, 15_16`이다. 이 시간창은 결과에 따라 변경하지 않는다.

## 5. 극한기온 정의

이 정의는 KMA 공식 폭염/한파 특보 기준이 아니라 **2024 서울 ASOS108 경험분포 기반 연구용 상대적 극한일**이다.

Primary:
- hot: `temperature_max >= 32.75°C` (2024 empirical p90)
- cold: `temperature_min <= -3.05°C` (2024 empirical p10)

Sensitivity:
- severe hot: `temperature_max >= 33.675°C` (p95)
- severe cold: `temperature_min <= -4.8°C` (p05)

모든 threshold는 ridership outcome을 사용하지 않고 Stage3A weather distribution에서 고정했다.
실제 realized day count는 모델 실행 시 계산하며 예상 일수를 hard-code하지 않는다.

## 6. H1 primary specification

Primary family는 PPML이다.

개념식:

`log E[count_dg] = date FE + senior + senior×month FE + senior×DOW FE + senior×hot + senior×cold`

Date FE는 hot/cold의 공통 main effect와 날짜 공통 충격을 흡수한다.
따라서 관심 추정량은 `senior×hot`, `senior×cold`의 age-differential effect다.

표준오차는 **date cluster-robust**로 고정한다.

## 7. H2 primary specification

H2는 `date × age_group × daytime` PPML이다.

Date FE와 함께 age/daytime baseline 및 필요한 lower-order interaction을 포함하고,
month와 day-of-week의 age×daytime 구조를 통제한다.

주 관심 추정량:
- `senior×hot×daytime`
- `senior×cold×daytime`

추가로 daytime 내 senior differential인
`senior×hot + senior×hot×daytime`,
`senior×cold + senior×cold×daytime` linear combination을 보고한다.

표준오차는 H1과 동일하게 date cluster-robust다.

## 8. 다중검정

하나의 confirmatory family를 네 개로 고정한다.

1. H1 hot senior differential
2. H1 cold senior differential
3. H2 hot daytime amplification
4. H2 cold daytime amplification

모두 양측 검정이며 raw p-value와 Holm-adjusted p-value를 함께 보고한다. alpha=0.05다.
효과크기와 95% CI를 p-value보다 우선해 해석한다.

## 9. 사전 지정 sensitivity

추가 탐색을 늘리지 않고 다음만 수행한다.

1. boarding PPML에서 p95 hot / p05 cold threshold sensitivity
2. p90/p10 사양을 alighting only로 반복
3. boarding daily log senior/non-senior ratio의 OLS + Newey-West HAC(maxlags=7) benchmark
4. H2는 daytime log ratio와 non-daytime log ratio의 차이 `DeltaR`를 같은 HAC benchmark로 사용

도시 전체 일별 age count에 0이 있으면 임의 zero correction 없이 benchmark를 BLOCK한다.

## 10. 해석 제한

Aggregate ridership은 이동 목적, 개인행동, 승객 거주지를 식별하지 않는다.
이 분석만으로 shelter-seeking 인과, 탄소감축, 지역 간 이동선택권 격차를 입증하지 않는다.
가설이 반대 또는 불확실하게 나오더라도 threshold/model을 바꾸지 않는다.

## 11. 구현 gate

이 specification/config/test commit을 먼저 만든 후에만 실제 모델 fitting 코드를 실행한다.
실제 fit 이전에는 coefficient, p-value, hypothesis result artifact를 생성하지 않는다.
통계 사양 변경이 필요하면 구현자가 임의 수정하지 않고 사람 검토로 되돌린다.
