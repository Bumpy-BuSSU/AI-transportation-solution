# 결과와 근거 안내

[프로젝트 소개로 돌아가기](../README.md)

핵심 결과를 먼저 확인하고, 필요한 표·코드로 이동할 수 있도록 정리했습니다. 수치는 저장된 분석 결과에 따른 값이며 이 문서 작성 중 새로운 모형을 적합하지 않았습니다.

| 질문 | 대표 결과·산출물 | 계산·해석 근거 |
| --- | --- | --- |
| 보행·이용 조건에 따라 선택지가 달라지는가 | [동별 지수](../outputs/tables/b0_dong_mci_all.csv), [요약](../outputs/tables/b_summary.json) | [지수 산정](../scripts/02_build_index.py), [민감도](../outputs/tables/b3_sensitivity.csv) |
| 접근성과 차량 이용이 연관되는가 | [선택권 집단별 비교](../outputs/tables/a1_mci_quartiles.csv), [식별 점검](../outputs/tables/j1_slope_robustness.csv) | [이용 분석](../scripts/07_model_usage.py), [추가 점검](../scripts/20_identification.py) |
| 어디에서 탄소 감축 여지가 큰가 | [거리·출발지 분해](../outputs/tables/m3_carbon_levers.csv), [도착 동별](../outputs/tables/n1_cprime_by_dong.csv) | [탄소 계산](../scripts/23_carbon_levers.py), [도착지 계산](../scripts/24_destination_access.py) |
| 날씨 반응의 연령차가 있는가 | [H1/H2 4개 주요 검정](../subway/results/models/confirmatory_test_family.csv) | [연령차 검정 사양·해석](../subway/docs/analysis/10-confirmatory-h1-h2.md) |
| 역 소재 행정동별 반응이 다른가 | [지역별 주요 검정](../subway/results/models/spatial_moderation_primary.csv), [민감도](../subway/results/models/spatial_moderation_sensitivity.csv) | [지역별 분석](../subway/docs/analysis/11-spatial-heterogeneity.md), [정책 시사점](../subway/docs/analysis/12-evidence-synthesis-policy.md) |
| 지역에 따라 무엇을 먼저 지원할까 | [정책 판별](../outputs/tables/f2_dong_quadrant.csv), [대상지](../outputs/tables/n6_policy_targets.csv) | [정책 진단](../scripts/16_policy_diagnosis.py) |

## 지표와 대상

- 이동선택권 지수는 공급·접근 조건의 사전진단 지표(0~3점)입니다. 실제 이동권 전체를 측정하지 않습니다.
- 동별 지수는 거주 가능 격자 단순평균입니다. README의 2.05점·0.90점은 동별 지수의 65세 이상 인구 가중평균입니다.
- 101.6만 명은 고령자 조건에서 지수 1 미만 지역에 거주하는 추정 고령인구입니다. 기본값을 포함한 14개 조건에서는 약 46만~146만 명으로 달라졌습니다.
- 고령자 접근 조건은 65세 이상, KT 고령자 이동은 70대 이상입니다. 지하철 심층검증은 고령권종·비고령 승차를 비교합니다.
- 427개 동의 정책 판별과 2024년 역 소재 173개 동의 날씨 검정은 대상·시점이 다릅니다. 공간분석 우선 25개 동, 우선지원 72개 동, C′ 상위 50개 동도 선정 목적이 다릅니다.

## 탄소 시나리오

A·B는 서울 내 출발 이동을 서울 평균과 비교합니다. C′는 서울 밖에서 지수 1 미만 동으로 도착하는 이동을 같은 거리대의 지수 1 이상 동 수준으로 전환한다고 가정합니다. A+B+C′는 약 40.9만 tCO₂이며, C′ 전체는 약 30.9만 tCO₂, C′ 상위 50개 동은 약 16.2만 tCO₂입니다.

가정: 사람 기준 전환 이동 건수 × 평균 거리 × 도로거리 보정 약 1.39 ÷ 탑승인원 1.3명 × 승용차 배출계수 약 194.6gCO₂/km × 평일 250일. 거리대 구분은 직선거리 기준입니다. 실제 노선·배차·전환량과 추가 운행 배출을 반영한 순탄소효과는 시범운행으로 평가해야 합니다.

## 날씨 검정

2024년 주요 극한일은 일최고기온 32.75℃ 이상과 일최저기온 −3.05℃ 이하로, 관측분포 상·하위 10% 기준입니다. 공식 기상특보 기준과 다릅니다. 각 검정군의 네 검정에 Holm 보정을 적용했습니다.

서울 전체 추가 연령차 검정의 비지지는 차이가 없다는 증명이 아닙니다. 지역별 결과는 역 소재 행정동 맥락과 상대 승차반응의 연관이며 개인의 절대 이동 감소나 정책 인과효과를 입증하지 않습니다. 지역별 상·하위 5% 민감도 검정은 공분산 문제로 추론 불가입니다.

## README 그림 출처

| 그림 | 근거 |
| --- | --- |
| 접근성 | `b0_dong_mci_all.csv`, `b_summary.json`, `a1_mci_quartiles.csv` |
| 탄소 감축 여지 | `m3_carbon_levers.csv`의 A·B·C′ |
| 날씨 반응 | `subway/results/models/confirmatory_test_family.csv`, `spatial_moderation_primary.csv` |

`docs/assets/`의 세 결과 그림은 검토한 보고서의 시각화를 재사용했습니다. 통계 적합·원본 CSV·기존 분석 그림은 변경하지 않았습니다. 첫 화면의 배너는 프로젝트 소개용이며 데이터 차트가 아닙니다.

기존 `docs/report.pdf`는 저장된 과거 보고서이며 최종 제출본으로 지정하지 않았습니다.
