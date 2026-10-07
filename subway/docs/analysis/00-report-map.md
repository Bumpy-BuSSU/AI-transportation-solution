# 개인 subway 분석보고서 근거 지도

최신 종합 기록: [Stage 4 evidence synthesis & policy translation](12-evidence-synthesis-policy.md) — 승인된 Stage 3A/B/C 동결 근거의 문서 종합 / **Stage 4 HUMAN REVIEW PENDING 2026-10-07**. 이전 완료·미착수·PENDING 문구는 각 시점의 이력이며 최신 synthesis와 후속 승인 기록을 함께 따른다.

이 문서는 사용자 개인의 subway 연구 기록이다. 팀 공통 규칙이 아니며 bike/, common/, top-level README에 적용하지 않는다. 현재 상태: 2026-10-07 **Stage 1 COMPLETE / Stage 2 preprocessing COMPLETE / Task 11 COMPLETE**. 승인된 baseline은 8종·12 Raw files다. **Task 9 및 Task 10 HUMAN APPROVED 2026-10-07**. 인간이 자동 테스트를 독립 실행했다는 뜻은 아니다. Canonical 종료 근거는 [2024 clean/transform 기술 baseline](../../../docs/subway/2024-clean-transform-baseline.md) 및 [현재 canonical QA summary](../../data/validation/pipeline_summary.json)다. Stage 3A focused EDA는 HUMAN APPROVED 2026-10-07. Stage 3B는 사전 동결 H1/H2 PPML·지정 sensitivity 실행 COMPLETE / **HUMAN APPROVED 2026-10-07**이다. 네 primary test의 Holm 기각은0/4이며 정책결론과 Secondary2 공간분석은 없다. 최신 [H1/H2 근거](10-confirmatory-h1-h2.md). 이전 Tasks의 PENDING/NOT STARTED는 당시 기록으로 유지한다.

## 현재 working research questions

전체 팀 주제: **“탄소중립 교통 전환 속 고령자의 이동 선택권 격차 분석 — 공공자전거와 도시철도를 중심으로”**. 이 기록은 subway 범위만 다룬다.

- Subway 전체 질문: “극한기온은 서울 고령층의 지하철 이용 패턴을 어떻게 변화시키며, 이러한 변화는 기존 교통 혼잡 및 기후대응 공간의 부족과 어떤 관계가 있는가?”
- Primary: “극한기온에서 서울시 내 65세 이상 지하철 이용자의 이용 변화는 비고령층과 다르게 나타나는가?”
- Secondary 1: “이러한 연령별 차이는 10~16시 주간 비첨두 시간대에서 더 강하게 나타나는가?” 시간대의 최종 운영 정의·검증은 분석 Stage에서 한다.
- Secondary 2: “이러한 차이는 서울 내 역·행정동별로 어떻게 다르며, 지역의 고령인구와 기후대응 공간 조건과 어떤 관계가 있는가?”

연구질문 자체는 현재 working question으로 확정되었다. 최종보고서 문장은 분석결과 후 조정 가능하며, 정책결론은 미확정이며 현재 기술 EDA와 사전 동결 H1/H2 결과는 아래 최신 기록에 연결한다. Stage 2는 가설을 검정하지 않는다. Aggregate ridership으로 trip purpose를 증명할 수 없어 최대 “기후회피형 이동과 일치하는 패턴”으로 해석한다.

현재 8개 Raw 데이터셋에는 일별 실제 혼잡 core dataset이 없다. 혼잡 관계는 Stage 2 증거 범위 밖이며 적합한 자료를 확보한 뒤 secondary analysis로 추가하거나 분석 단계에서 최종 연구질문 범위를 조정한다. 자료 없는 혼잡 결과를 예고·추론하지 않는다. Shelter는 clean 보조 공간 layer이며 기후대응 공간 부족의 결과도 아직 없다.

| 최종보고서 항목 | 현재 근거 | 상태와 다음 작업 |
|---|---|---|
| 분석 배경·목적·문제·필요성 | 승인된 [전처리 설계](../../../docs/superpowers/specs/2026-10-03-subway-data-preprocessing-design.md), 사용자 연구 목적 | 위 working question·primary·secondary 질문 확정. 필요성의 최종 논증과 보고서 문장은 근거·분석결과 후 조정; H1/H2 결과는 최신 근거로 연결하며 정책결론은 아직 없음 |
| 활용 데이터 | [Raw 연구 기록](01-raw-data-baseline.md), [기술 baseline](../../../docs/subway/2024-raw-schema-baseline.md) | 원래 7종·11 files 보존 + 승인된 직접 65+ source 1종·1 file 확장 |
| 출처·제공기관·URL | [manifest](../../data_manifest.csv) | 확인된 값만 기록. 빈 다운로드일·라이선스 등은 미확인; 제출 전 공식 출처 재검토 |
| 기준시점·기간 | manifest, [source contracts](../../config/source_contracts_2024.yaml) | 승하차·기상 2024, 기존 인구 Q2–Q4는 보조 검증, 직접 65+ Q2가 primary, 경계 2024-06-30. 역 좌표는 승인된 snapshot-stability/CRS 분석 가정과 exclusions 적용; source-specific 검증 및 쉼터 시점 한계 유지 |
| 수집 및 전처리 | Raw baseline, Stage 1 코드·tests, [Stage 2 계획](../../../docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md) | **Stage 2 전처리 COMPLETE**. [종료 baseline](../../../docs/subway/2024-clean-transform-baseline.md), [canonical QA](../../data/validation/pipeline_summary.json), Tasks 9/10 사람 승인 및 Task11 최종 검증으로 근거 연결 |
| 분석 방법론 | [방법론 로그](methodology-log.md) | schema inspection·SHA-256·재현성 및 승인된 전처리 adopted. 사전 동결 H1/H2 PPML·지정 HAC만 실제 실행; 나머지 통계모형은 candidate |
| AI 서비스·범위·주요 프롬프트 | [AI 사용 기록](ai-usage-log.md) | ChatGPT/Codex 역할과 주요 지시 요약 기록. 인간 검증은 증거가 있는 범위만 기록 |
| 분석 결과 | [Stage 3A focused EDA](08-focused-eda.md), `subway/results/tables/`, `subway/results/figures/` | [동결 H1/H2 결과](10-confirmatory-h1-h2.md) 생성. Primary Holm 기각0/4, 현재 사양 NOT SUPPORTED; 기술 EDA와 추론 결과를 구분. Secondary2는 controlled reconstruction 완료 / SCIENTIFIC REVIEW PASS·HUMAN APPROVED 2026-10-07; [Stage3C evidence](11-spatial-heterogeneity.md) |
| 정책 제안·기대효과 | 아직 없음 | 미완료. 분석 후 작성 |
| 결과 이미지 | Stage 3A 기술 EDA 그림 5개 | 기술적 탐색 그림이며 최종 보고서 채택 여부는 사람 검토 후 결정. [H1/H2 effects](../../results/figures/confirmatory_effects.png)는 pointwise95% CI를 표시; 최종보고서 채택은 사람 검토 후 결정 |
| GitHub 재현 코드 | 저장소의 `subway/tools/inspect_raw_inputs.py`, `subway/tests/`, 기술 baseline | Stage1 및 `python subway/run_pipeline.py --year 2024` 재현 가능. Task11 종료 검증 완료; [종료 baseline](../../../docs/subway/2024-clean-transform-baseline.md)의 환경·hash·계약 참조 |

현재 근거가 없는 항목에는 결과·정책·수치·그림을 만들어 넣지 않는다. 각 후속 Stage 종료 시 해당 문서와 검증 결과를 연결한다.


- [P-S2-2RC station spatial authority audit](04-station-spatial-authority-audit.md):
  historical KRIC acquisition limits, official WGS84 standard, separate
  current support diagnostics and conditional source proposal; Task5 BLOCKED.


- [P-S2-2RD Task5 eligibility closure](05-station-spatial-eligibility.md): core 보존, 공간 제외 사유·이용량 비중, 승인된 분석 가정. 이전2RC의 BLOCKED는 당시 역사 기록이다.

- [P-S2-T9 strict station-dong mapping](06-station-dong-mapping.md): 258개 적격 역 중243 mapped/15 명시적 ZERO_MATCH; 원본 core 보존, 누적 제외 비중과426/426 인구 경계 검증. Task9 결과 인간 검토 PENDING.

## P-S2-T10 current empirical scope — 2026-10-07

현재 서울은 공공자전거·인구·경계·기상ASOS108·기후대응 공간자료의 정합성이 검증된 첫 실증지역이다.
연구 프레임워크 자체가 서울에 영구 한정되는 것은 아니다. 서울 밖 도시철도 관측도 full core에 보존한다.
비교 가능한 지역별 경계·인구·기상·교통 자료를 검증하면 향후 수도권/다른 지역의 이동선택권 격차 비교로 확장할 수 있다.
현재 지역 간 결과는 없고 서울 결과를 지역 간 격차로 일반화하지 않는다. [Task10 record](07-pipeline-orchestration.md).


## P-S2-T11 current closeout — 2026-10-07

Task10 HUMAN APPROVED 2026-10-07. Stage2 preprocessing / Task11 COMPLETE.
최종 단일 검증:158 tests OK, pipeline exit0 / ERROR0 WARNING16 INFO2,
Raw inspection exit0 / ERROR·WARNING·INFO 모두0. 8datasets/12Raw,7clean/4processed,
exact input/config/output hashes 및 summary bytes는 승인 Task10 baseline과 일치한다.
현재 eligible IN243/OUT15/UNRESOLVED0, full274 master는 IN243/OUT15/UNRESOLVED16.
15 ZERO_MATCH는 현재 서울 연구범위 밖이고 core에 남는다. 16은 Task5 공간 제외이며 outside로 단정하지 않는다.

보고서의 수집·전처리·품질·연구지역·재현성·한계 근거 문장은
[종료 baseline §13](../../../docs/subway/2024-clean-transform-baseline.md#13-stage-2-definition-of-done와-보고서-근거-문장)을 참조한다.
EDA 결과, 가설검정 결과, 통계 추정치, charts, 정책 제안, 기대효과는 **모두 미완료**다.
최종5쪽 보고서나 정책결론을 작성하지 않았다. 서울의 향후 실증 결과를 현재 지역 간 격차나
trip purpose·탄소감축 인과효과로 표현하지 않는다. 합의된 primary/secondary 질문은 유지한다.


## P-S3A-EDA focused descriptive analysis — 2026-10-07

Stage 2 승인 산출물만 사용해 현재 서울 실증 표본을 구성했다. 원래 core 3,988,480행·274 identity 중 현재 연구지역 243 identity / 3,557,520행이 EDA base에 들어갔다. 공간범위에서 430,960행이 제외되며, 그중 219,600행은 현재 서울 경계 밖 15 identity, 211,360행은 Task5 공간 미확정 16 identity다. core 자체는 수정하지 않는다. 현재 서울 표본은 모두 matched이며 senior>total 1셀만 연령 비교 통계에서 제외하여 valid age-comparison 3,557,519행을 사용한다.

서울 ASOS108은 366일 모두 mean/max/min 기온이 존재한다. 10–16시는 기존 20개 hour bin 중 `10_11`~`15_16` 여섯 구간으로 정확히 구현 가능함을 확인했다. 기술적으로 고령 이용은 비고령보다 10–16시에 더 집중된 시간대 구조를 보이지만, 이는 극한기온 효과가 아니다. 기온 분위수별 일 이용량 프로파일은 양 극단에서 낮아지는 비선형 형태를 보여 이후 비선형 함수형을 검토할 근거가 있으나, 계절·요일을 조정하지 않은 기술통계이므로 효과·인과로 해석하지 않는다.

Count 분포는 senior/non-senior 모두 평균 대비 분산이 매우 크고, 역별 연간 이용량 및 senior share도 큰 이질성이 있다. 이는 이후 count-model 분산 가정과 station fixed effects 필요성을 검토할 근거다. 주말 일평균 이용량은 평일보다 뚜렷하게 낮아 calendar adjustment가 필요하다. 극한기온 cutoff, PPML/Poisson/NB/GAM, FE 조합, cluster SE는 아직 채택하지 않는다.

세부 근거: [08-focused-eda.md](08-focused-eda.md). 현재 WIP artifact summary는 `human_eda_review=PENDING`, `extreme_threshold_status=NOT ADOPTED`, `hypothesis_test=NOT PERFORMED`, `regression=NOT FITTED`를 유지한다.


## P-S3B specification freeze — 2026-10-07

Stage3A HUMAN APPROVED 2026-10-07. 로컬 focused 9 tests / full 167 tests OK 및 EDA 정상 실행을 사람 검토 근거로 사용한다.
[confirmatory specification](09-confirmatory-specification.md)과 `subway/config/confirmatory_analysis_2024.yaml`에 H1/H2 사양을 결과 생성 전에 고정한다.

핵심 계약은 citywide 일별 ASOS108 exposure에 맞춘 daily aggregation, boarding primary / alighting sensitivity,
hot p90(`temperature_max>=32.75`) / cold p10(`temperature_min<=-3.05`) primary,
p95/p05 sensitivity, exact 10–16 daytime, PPML + date-cluster inference, 네 개 primary test의 Holm 보정이다.
이 단계에서는 coefficient/p-value/가설판정이 아직 없다. Secondary2 공간 이질성도 시작하지 않는다.


## P-S3B-RESULT current state — 2026-10-07

SPEC_FREEZE_SHA f5433eb98d96d8098c265de0859282dcc53046f1, pre-fit YAML fix596f0dbe00951a7444f30fc4fa41e88a529e6e8e 그대로 실행했다. Focused11/full178 OK, runner exit0.
Primary boarding, p90hot32.75°C / p10cold-3.05°C, daytime10–16, date-cluster PPML 및4-test Holm 불변.
모든 primary pointwise95% CI가0을포함하고 Holm 기각0/4이다. H1/H2는현재사양에서 NOT SUPPORTED이며 차이가없다는증명은아니다.
추정치·불확실성·p95/p05·alighting·HAC(7) 전체는 [결과 기록](10-confirmatory-h1-h2.md), [canonical family](../../results/models/confirmatory_test_family.csv)에 연결한다.
이전 no-model-result 기록은 당시 이력이다. H1/H2 결과는생성했지만 최종 contest report·정책제안·기대효과·trip purpose·인과결론은작성하지않았다. Secondary2는미착수다. 사람결과검토 PENDING.


## P-S3B-HUMAN-APPROVAL — 2026-10-07

사용자는 ChatGPT의 원격 정밀검토 후 Stage3B frozen H1/H2 결과를 승인했다.
승인된 해석은 현재 사전 사양에서 primary four-test family의 Holm 기각이 0/4이며 H1/H2가 **NOT SUPPORTED**라는 점까지다.
이는 연령차가 없다는 증명도, 반대방향 효과가 입증되었다는 뜻도 아니다.
정책제안·trip purpose·인과적 shelter-seeking·탄소감축·지역 간 격차 결론은 여전히 미승인/미도출이며,
Secondary2 공간 이질성은 다음 별도 Stage로 남긴다.

## P-S3C-RECONSTRUCTION current evidence — 2026-10-07

[Stage3C cumulative evidence ledger](11-spatial-heterogeneity.md)에 목적/출처/기간/QA/모형/정밀 Primary 표/Layer A 기술분포/p95/p05 점추정 및 covariance 실패/해석한계/AI 역할/재현 명령을 연결했다.
Secondary2 기술 실행 완료, 인간 과학적 결과검토 PENDING. Cold×고령인구비중만 frozen4-test Holm을 통과했다. 민감도는 네 점추정만 보존하고 전체 NOT ESTIMABLE이다.
그림은 [Layer A paired map](../../results/figures/station_extreme_heterogeneity.png), [all-dong context](../../results/figures/spatial_context.png), [Primary pointwise CI](../../results/figures/spatial_moderation_effects.png) 세 개다.
기존 H1/H2 NOT SUPPORTED 결과 유지. 이전 NOT STARTED/PENDING 문구는 당시 기록이다. 이번 재구축은 missing f002cc1 복구가 아니며 종전29PASS를 검증 증거로 사용하지 않는다.
정책·인과·승객 이동목적·위험 역 분류·최종보고서 초안은 이번 범위 밖이다.

## P-S3C-HUMAN-APPROVAL — 2026-10-07

Stage 3C controlled reconstruction `f5e0328a4928d4373f91967860ea00e6190da8c8`의 인간 과학적 검토는 **PASS**다. 승인된 범위의 과학적 작업이 완료됐고 [누적 evidence](11-spatial-heterogeneity.md)는 이후 최종보고서 synthesis에 사용 가능하다.
Layer A는 기술적 점추정만, Primary는 Cold×고령인구비중만 Holm 통과한 문맥적 연관으로 해석한다. p95/p05 전체 추론은 covariance 실패에 따른 NOT ESTIMABLE이며 비유의성이 아니다. Stage3B 결과·통계 방법은 불변이며 추가 optional EDA/sensitivity는 필요하지 않다.
앞선 PENDING 및 generated summary의 PENDING은 인간 검토 전 기술 실행 이력이며, 이 후속 승인 기록으로 현재 상태를 구분한다. 이번은 문서 closeout만 수행했고 과학적 분석을 재실행하지 않았다.

## P-S4-EVIDENCE-SYNTHESIS — 2026-10-07

Canonical [Stage 4 synthesis](12-evidence-synthesis-policy.md)는 승인된 Stage 3A/B/C만 사용한다. 새 통계 방법·변수·분석·tests/runner 실행·그림 재생성은 없으며 methodology-log는 변경하지 않는다. Stage 4 정책 번역 및 최종보고서 채택은 **인간 검토 PENDING**이다.

| 최종보고서 항목 | 최신 근거·선택 |
|---|---|
| 분석 결과·질문별 판단 | Stage 4 §3 및 §7 요약표: H1/H2 NOT SUPPORTED(Holm 0/4), Cold×고령인구비중만 문맥적 조절 연관 지지, shelters/10k 비지지, Stage 3C p95/p05 NOT ESTIMABLE |
| 통합 결론·이동선택권 framing | Stage 4 §4. 지역 문맥에 따른 이질성에 주목; subway 단독으로 이동선택권 격차를 입증하지 않음 |
| 정책 제안·기대 기여 | Stage 4 §5 Tier 1 우선 모니터링·추가 평가와 Tier 2 인프라 평가 가설. 정책 효과·격차 감소·탄소감축 크기는 미검증; 인간 검토 대기 |
| 최소 결과 이미지 | 기존 confirmatory_effects.png 및 spatial_moderation_effects.png를 primary 후보로 선택. Pointwise CI와 Holm 판단을 구분; Layer A 지도·공간 문맥·EDA 그림은 supplementary 후보 |
| AI 사용·인간 검토 | Stage 4 §9 및 [AI log](ai-usage-log.md)의 P-S4 기록. 기존 과학적 승인과 이번 synthesis 검토를 구분 |
| 후속 연구·bike 통합 | Stage 4 §8 post-hoc 가설 및 문서 말미의 team-integration interface. Bike 결과는 조사하지 않고 확인 checklist만 제공 |

현재 산출물은 subway 보고용 근거 package이며 최종 팀 5쪽 보고서나 팀 통합 결과가 아니다. Stage 4 §6의 인과·거주지·이동목적·위험/취약 역·쉼터 해법·강건성 과장 금지 경계를 유지한다.
