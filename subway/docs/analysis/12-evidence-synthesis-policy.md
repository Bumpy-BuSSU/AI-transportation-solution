# Stage 4: Subway evidence synthesis and policy translation

## 1. 목적과 상태

작성일: 2026-10-07. 기준 `origin/dev`: `8ed2a52a450d7cb459b3c23ca7c3d36bcf17b9a2` (Stage 3C PR #3 merge). Stage 3A/B/C는 **HUMAN APPROVED**인 동결 근거다. 이 문서는 5쪽 내외 팀 보고서에 사용할 subway 근거 종합·정책 번역의 canonical 기록이다. **Stage 4 문서 작성 완료 / HUMAN REVIEW PENDING**이며, 정책 문구와 최종 그림 채택은 이번 인간 검토 대상이다.

새 통계분석·모형 변경·결과 또는 그림 재생성은 수행하지 않는다. 기존 방법론을 재채택하거나 새 변수·threshold·sensitivity를 도입하는 단계가 아니다. Subway 결과만으로 팀 전체의 이동선택권 격차를 확정하지 않는다.

## 2. 동결 근거 입력

| 입력 | 승인 근거와 사용 범위 |
|---|---|
| [Stage 3A focused EDA](08-focused-eda.md) | 시간대·calendar·과산포·역 이질성의 기술적 근거. 승인 기록은 [report map](00-report-map.md)의 P-S3B specification freeze 및 [AI log](ai-usage-log.md)의 P-S3B-SPEC에 있음 |
| [Stage 3B H1/H2](10-confirmatory-h1-h2.md), [primary CSV](../../results/models/confirmatory_test_family.csv) | Seoul-wide 연령별 상대 승차반응과 주간 추가 증폭; four-test Holm, 사전 동결 사양에서 NOT SUPPORTED |
| [Stage 3C evidence](11-spatial-heterogeneity.md), [primary CSV](../../results/models/spatial_moderation_primary.csv) | 역별 기술적 점추정과 station-weighted local-context moderation; 후속 인간 승인 기록이 현재 상태 |
| [Stage 3C sensitivity CSV](../../results/models/spatial_moderation_sensitivity.csv), [summary](../../results/models/spatial_moderation_summary.json) | 네 점추정과 raw covariance 실패 근거 보존; 전체 추론 NOT ESTIMABLE |

분석은 2024 서울 243역·366일에 한정된다. Stage 3C는 역이 위치한 173동의 문맥을 사용하며 서울 전체 426동의 대표표본으로 해석하지 않는다. Common-valid boarding cells는 1,778,759, station-days는 88,938이다. `2024-04-20 / 올림픽공원(한국체대) / 21–22 / senior 187 > total 106` 셀은 원값을 보존하고 양쪽 연령 비교 집계에서 공통 제외했다.

Primary hot은 일최고기온 ≥32.75°C(p90), cold는 일최저기온 ≤−3.05°C(p10)로 각각 37일이다. 이는 경험분포 기반 연구용 극한일이며 공식 기상특보 기준이 아니다. Daytime은 사전 지정 `10:00 ≤ time < 16:00`, `10_11`~`15_16` 여섯 bin이다. Primary event는 boarding이다. 출처·전처리·공간 가정·시점 한계는 [manifest](../../data_manifest.csv), [Stage 2 baseline](../../../docs/subway/2024-clean-transform-baseline.md), 각 Stage 근거를 따른다.

Stage 3C는 `d24830a…`에서 재구축한 `f5e0328…`의 결과이며, `5520e8e…`에서 인간 승인을 기록하고 현재 dev에 merge됐다. `f002cc1`을 복구한 것이 아니고 역사적 29 PASS를 검증 근거로 사용하지 않는다. 기존 문서·generated summary의 PENDING은 실행 당시 이력이며 후속 인간 승인과 구분한다.

## 3. 근거 종합 matrix

| 질문/근거 | 확인된 결과 | 판단과 해석 범위 |
|---|---|---|
| Stage 3A: 고령층의 baseline 시간대 구조 | 10–16 이용 비중은 고령층 약 48.7%(승차)/49.1%(하차), 비고령층 약 27.7%/29.1% | 기술적 시간대 차이. 극한기온 효과나 이동목적의 증거가 아님 |
| Stage 3B H1: hot/cold senior differential | H1 두 검정 모두 Holm 비기각 | 동결 사양에서 NOT SUPPORTED. 차이 없음의 증명이 아님 |
| Stage 3B H2: hot/cold daytime amplification | H2 두 검정 모두 Holm 비기각; H1/H2 family 기각 0/4 | 사전 지정 주간 추가 증폭 NOT SUPPORTED. Baseline 주간 집중과 구분 |
| Stage 3C Layer A | Hot median ≈−0.00478341, cold median ≈−0.00961033; 음의 점추정 비중 약 61.7%/71.6% | 역별 기술적 점추정 분포만. 유의한 역 비율·위험/취약 역 분류가 아님 |
| Stage 3C Primary: 고령인구비중 | Cold만 Holm 기각, hot 비기각 | 한파일의 연령 상대반응과 지역 인구 문맥 사이 음의 조절 연관 |
| Stage 3C Primary: shelters/10k | Hot/cold 모두 Holm 비기각 | 현재 지표·사양에서 NOT SUPPORTED. 쉼터 무효과·부족 원인 또는 증설 효과의 증명이 아님 |
| Stage 3C p95/p05 | Target variance 3/4 음수; 네 점추정 보존, 전체 SE/CI/raw p/adjusted p/significance NA | NOT ESTIMABLE. 비유의성 또는 강건성 근거로 사용 불가 |

Stage 3B는 daily citywide PPML/date-cluster 추론이고 Stage 3C Primary는 station-day `log(senior/non_senior)` outcome의 station/date FE·ADM_CD/date two-way covariance다. 두 분석은 추정 대상이 다르므로 citywide 비지지와 공간 조절 연관을 모순이나 같은 효과의 재검정으로 표현하지 않는다. 각각의 primary 네 검정에 Holm을 적용했으며 두 family를 합친 새 보정을 수행하지 않았다.

아래 수치는 [Stage 3C primary CSV](../../results/models/spatial_moderation_primary.csv)의 값을 소수점 여섯 자리로 반올림한 보고용 표다. Moderator는 역이 위치한 173개 고유 동의 sample SD로 표준화했다. CI는 **pointwise 95%**이며 Holm-adjusted simultaneous CI가 아니다.

| Moderation (문맥 변수 1 SD당) | β | Pointwise 95% CI | Holm 판단 |
|---|---:|---|---|
| Hot × 고령인구비중 | +0.001172 | [−0.000869, +0.003214] | 비기각 |
| Cold × 고령인구비중 | −0.007220 | [−0.009456, −0.004985] | 기각 |
| Hot × shelters/10k | −0.002166 | [−0.006880, +0.002549] | 비기각 |
| Cold × shelters/10k | +0.003076 | [−0.002051, +0.008202] | 비기각 |

Cold × 고령인구비중의 canonical β는 `-0.007220386633954651`, Holm p는 `9.777353323110831e-10`이다. 이는 고령인구비중이 한 SD 높은 동에 위치한 역에서 한파일의 고령/비고령 승차 log-ratio 상대반응이 더 음의 방향이라는 station-weighted 문맥적 연관이다. 고령자 절대 이용량 감소나 거주자 개인의 반응을 직접 추정한 값이 아니다.

**민감도 범위:** NOT ESTIMABLE은 Stage 3C p95/p05의 전체 four-target inferential layer를 뜻한다. Stage 3B의 별도 p95/p05 결과에 이 상태를 적용하지 않는다. 실패 사유는 `NOT_ESTIMABLE_INVALID_TWOWAY_COVARIANCE`; 네 번째 양의 target variance도 전체 추론 억제에 포함한다. 전체 억제는 scientific gate 이후 인간이 승인한 protocol amendment이며 원래 사전 지정 규칙으로 표현하지 않는다. 분산 abs/clipping/PSD repair 또는 대체 covariance는 사용하지 않았다.

## 4. 보고서용 통합 결론과 이동선택권 framing

> 서울 전체 평균에서는 폭염·한파에 따른 고령자와 비고령자의 지하철 이용반응 차이와 10~16시 추가 증폭이 뚜렷하게 지지되지 않았다. 그러나 공간적으로는 고령인구 비중이 높은 지역일수록 한파일의 고령/비고령 상대 승차반응이 더 음의 방향으로 나타나는 문맥적 연관이 확인됐다. 따라서 극한기후 속 고령자의 지하철 이동을 하나의 평균적 행동패턴으로 설명하기보다 지역 맥락에 따른 이동반응의 이질성을 고려할 필요가 있다.

고령층의 baseline 주간 이용 비중이 높다는 EDA 관찰은 H2 지지로 이어지지 않았다. Citywide 평균의 비지지는 모든 지역의 반응이 같다는 뜻도 아니다. 공간 결과는 지역별 차이에 주목할 근거를 제공하지만, 동일한 개인이나 절대 이동량의 변화를 식별하지 않는다.

> 동일한 도시철도 네트워크가 존재하더라도 극한기후 상황의 실제 이용반응은 지역의 인구구조와 함께 달라질 가능성이 있으며, 이는 기후회복력 있는 이동선택권을 설계할 때 평균값만으로는 충분하지 않을 수 있음을 시사한다.

현재 subway 자료는 **이동선택권 격차를 직접 증명하지 않는다**. 팀 전체 격차 결론은 추후 bike 근거와 통합한 뒤 인간이 판단한다.

## 5. 근거 강도별 정책 번역

### Tier 1 — 근거가 뒷받침하는 시사점

| 시사점 | 실행 방향 | 근거 범위 |
|---|---|---|
| 서울 전체에 동일한 대응만 적용하면 지역별 차이를 놓칠 수 있음 | 지역 문맥을 고려하는 대응과 모니터링 | Citywide H1/H2 비지지와 Cold × 고령인구비중 조절 연관을 함께 반영 |
| 한파 이동 모니터링에서 지역 연령구조를 고려할 필요 | 고령인구비중을 함께 보는 우선 모니터링 | 지역 인구 문맥과 연령 상대 승차반응의 연관까지 |
| 고령인구비중이 높은 동의 역 주변은 추가 평가의 우선 대상 후보 | 접근성·이동 여건의 추가 평가 | 역별 위험 순위나 검증된 취약지역 지정이 아님; 새로운 cut-off를 설정하지 않음 |

이는 정책 검토 방향이며 정책 효과를 검증한 결과가 아니다. 기대 기여는 평균 중심 진단을 보완하는 데 있고, 이용 증가·격차 감소·탄소감축의 크기는 추정하지 않았다.

### Tier 2 — 추가 근거가 필요한 정책 설계 가설

후속 평가 항목은 역까지의 보행 접근, 무장애·수직 이동 접근, 버스 환승 및 first/last-mile 접근, 기상으로부터 보호되는 대기·접근 공간, 기후대응 시설의 실제 접근성·운영 조건이다. 각각이 관측된 한파 조절 연관의 원인 또는 완충 요인인지 확인할 필요가 있다는 **평가 제안**이며, 현재 원인으로 관측됐다는 진술이 아니다. 개선 사업의 효과나 우선 사업 순서를 현 결과로 확정하지 않는다.

**쉼터:** 현재 분석의 단순 shelters/10k 조절 연관은 hot/cold 모두 지지되지 않았다. 따라서 쉼터 수 증가를 입증된 해결책으로 제안하지 않는다. 후속 연구에서는 접근성·거리·질·운영시간 등 세부 지표의 필요성을 검토할 수 있지만 현재 모형에 추가하지 않는다. 이는 쉼터 효과가 없다는 결론이 아니다.

## 6. 지지되지 않은 주장과 해석 한계

- H1/H2 비지지를 “연령 차이가 없다” 또는 반대 효과가 입증됐다는 주장으로 바꾸지 않는다.
- 지역 문맥 조절 연관을 기온·인구구조·보행/교통 인프라의 인과효과로 해석하지 않는다.
- 역 이용자의 거주지·개인 행동·절대 이동 위축·이동목적·쉼터 이용 또는 피난 기능을 확인했다고 주장하지 않는다.
- 역별 기술적 점추정으로 유의한 역, 위험 역, 취약 역 또는 교통소외지역을 지정하지 않는다.
- 쉼터 부족이 결과를 초래했다거나 증설이 입증된 해법이라는 주장, 쉼터 무효과 주장 모두 근거 밖이다.
- Stage 3C p95/p05 NOT ESTIMABLE을 비유의성·primary 강건성의 증거와 혼동하지 않는다.
- Subway 단독으로 이동선택권 격차·정책 효과·탄소감축·지역 간 격차를 입증하거나 다른 연도·도시로 일반화하지 않는다.

한계는 단일 연도·단일 ASOS 서울 노출, station-weighted estimand, 미측정 지역 요인, 역 좌표의 승인된 CRS/snapshot 가정, 공간 제외, 쉼터 snapshot 시점·완전성, 직선거리와 실제 접근성의 차이, 집계자료의 거주지·목적 미식별이다. 상세 기술 한계는 Stage 2/3 근거에 남기고 본문에는 결과 해석에 필요한 범위만 선택한다.

## 7. 최종 5쪽 보고서의 최소 근거 package

다음 요약표 하나와 기존 primary 그림 두 개를 최소 subway 후보로 선택한다. 이는 팀 보고서 전체 5쪽 안에서 사용할 후보이며 최종 배치·크기는 인간 검토 및 bike 통합 후 결정한다. 전체 technical log와 모든 수치표를 본문에 복제하지 않는다.

| Research question | Evidence | Decision |
|---|---|---|
| 극한기온에서 고령층은 비고령층과 다르게 반응하는가? | Stage 3B H1, Holm-adjusted primary result | NOT SUPPORTED under the frozen specification |
| 연령 차이는 사전 지정 10–16시에 더 증폭되는가? | Stage 3B H2, Holm-adjusted primary result | NOT SUPPORTED under the frozen specification |
| 반응은 지역 문맥에 따라 달라지는가? | Stage 3C primary moderation | Cold × senior population share supported; 문맥적 연관 |
| Shelters/10k가 반응을 조절하는가? | Stage 3C hot/cold shelter moderators | NOT SUPPORTED under the frozen specification |
| Stage 3C p95/p05 sensitivity는 유효한 추론을 제공하는가? | Frozen ADM_CD/date two-way covariance | NOT ESTIMABLE |

NOT SUPPORTED는 현재 사양의 지지 부족이며 영효과 입증이 아니다. NOT ESTIMABLE은 추론 불가다.

| 우선순위 | 기존 그림 | 목적 및 보고서 caption 핵심 |
|---|---|---|
| Primary 1 | [confirmatory_effects.png](../../results/figures/confirmatory_effects.png) | Seoul-wide H1/H2 상대 추정치와 pointwise 95% CI. Primary 네 검정의 Holm 기각 0/4; 차이 없음의 증명이 아님 |
| Primary 2 | [spatial_moderation_effects.png](../../results/figures/spatial_moderation_effects.png) | Stage 3C 네 조절 추정치와 pointwise 95% CI. Cold × 고령인구비중만 four-test Holm 통과; station-weighted 문맥적 연관 |
| Supplementary | [station_extreme_heterogeneity.png](../../results/figures/station_extreme_heterogeneity.png) | 역별 기술적 점추정 지도; 유의성·위험 분류 없음 |
| Supplementary | [spatial_context.png](../../results/figures/spatial_context.png) | 426동 지역 문맥 설명; 이용효과나 원인 지도 아님 |
| Supplementary | [Stage 3A EDA 그림 목록](08-focused-eda.md#9-산출물) | Baseline 시간대·분포 이해가 필요할 때만 추가; 극한기온 효과로 해석하지 않음 |

Primary 그림의 CI와 Holm 판단을 구분해 caption으로 명시한다. Stage 3C p95/p05 추론 실패는 표 또는 본문에 남기며 primary 그림을 강건성 증거로 소개하지 않는다. 신규 그림·그림 수정은 하지 않았다. 정밀 표는 기존 canonical CSV로 연결하고 필요 시 §3의 반올림 표를 사용한다.

## 8. 결과 후 후속 가설 — POST-HOC / FUTURE WORK

> 고령인구 비중이 높은 지역에서는 한파 상황에서 고령자의 이동이 상대적으로 더 위축되며, 지역별 교통·보행·기후대응 인프라 조건이 이러한 이동 위축을 완충하거나 악화시킬 수 있다.

이 문장은 **결과 이후 제기된 후속 검증 가설**이며 사전 동결 Stage 3 가설이나 현재의 개인 수준·절대 이동 위축 관측 결과가 아니다. 인프라의 완충/악화는 아직 검증하지 않았다.

> 일부 지역에서 지하철이 단순 교통수단을 넘어 기후대응 또는 피난 인프라 역할을 하는가?

이는 추후 연구질문이다. 현재 aggregate boarding 자료는 이 이동목적을 식별할 수 없다.

## 9. AI 사용과 인간 검토 상태

- Human: Stage 3A/B/C 승인 및 이번 Stage 4 Mission 제공. Stage 4 정책 문구·보고서 선택·팀 통합 해석에 대한 **최종 검토 PENDING**이며 이번 문서가 사후 승인을 뜻하지 않는다.
- ChatGPT: 사용자 Mission에 기록된 승인 과학적 synthesis, 정책 tier·해석 경계·작업 범위 설계. 이번 산출물의 독립 정밀검토를 수행했다고 주장하지 않는다.
- Codex: 동결 문서·canonical CSV/JSON 대조, 보고용 synthesis·table·figure 후보 선택, report-map/AI-log 연결, 문서 범위·링크·수치·Git whitespace 검증과 한 번의 집중 정밀검토, 로컬 문서 커밋. 새 분석·외부 문헌 조사·tests/runner 실행·bike 결과 검토 없음.

주요 Mission 원문 reference: 2026-10-07 사용자 첨부 “Mission: Create the Stage 4 subway evidence synthesis and policy-translation record”, attachment ID `868c8da1-a7db-4841-a21f-7520822c254d`. [AI log](ai-usage-log.md)에 사용 범위와 승인 상태를 연결한다. 이전 focused17/full195/production exit0는 Stage 3C의 역사적 기술 검증 근거이며 이번에 재실행하거나 인간 독립 실행으로 기록하지 않는다.

## 10. Team-integration interface

### Subway finding

2024 서울 subway의 동결 Stage 3B 사양에서 극한기온의 연령별 citywide 상대 승차반응 차이와 10–16시 추가 증폭은 명확히 지지되지 않았다(Holm 기각 0/4). Stage 3C에서는 고령인구비중이 높은 동에 위치한 역의 한파일 고령/비고령 상대 승차반응이 더 음의 방향인 station-weighted 문맥적 연관만 primary four-test Holm을 통과했다. 역별 Layer A는 기술적 점추정이며 Stage 3C p95/p05 전체 추론은 NOT ESTIMABLE이다.

### What subway does NOT establish

- 개인·거주자 수준 기온 인과효과, 절대 이동 위축 또는 이동목적·쉼터/피난 이용.
- 입증된 취약 역·교통소외지역·직접적인 이동선택권 격차.
- 쉼터 부족 원인·증설 효과, 보행/환승/무장애 인프라 원인, 정책 효과·탄소감축.
- 비지지 결과의 영효과 증명, 추론 불가 sensitivity의 강건성 증명, 다른 도시·연도 일반화.

### What bike evidence would need to contribute

- 연령별 이용 차이가 실제로 존재하는지와 그 근거·불확실성.
- 인구 정규화 후에도 차이가 유지되는지와 정규화 분모의 타당성.
- 접근성·디지털 이용·장벽 관련 어떤 근거가 실제로 지지되는지.
- 자료·설계가 허용하는 인과 해석 수준과 남은 한계.
- Subway와 기간·지역·연령·이용 단위의 비교 가능성 및 두 근거가 팀 이동선택권 framing을 어느 범위까지 뒷받침하는지.
