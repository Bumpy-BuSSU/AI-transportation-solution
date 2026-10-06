# 개인 subway 분석보고서 근거 지도

이 문서는 사용자 개인의 subway 연구 기록이다. 팀 공통 규칙이 아니며 bike/, common/, top-level README에 적용하지 않는다. 기록일: 2026-10-07. Stage 1 COMPLETE / 승인된 baseline 확장 8종·12 files / Stage 2 Tasks 1–10 구현·검증 COMPLETE; Task 9 HUMAN APPROVED on2026-10-07, Task 10 결과 인간 검토 PENDING. Task 11 NOT STARTED. 현재 실증지역은 설정된 서울이며 core coverage는 더 넓다. 최신 근거: [Task10 execution](07-pipeline-orchestration.md).

## 현재 working research questions

전체 팀 주제: **“탄소중립 교통 전환 속 고령자의 이동 선택권 격차 분석 — 공공자전거와 도시철도를 중심으로”**. 이 기록은 subway 범위만 다룬다.

- Subway 전체 질문: “극한기온은 서울 고령층의 지하철 이용 패턴을 어떻게 변화시키며, 이러한 변화는 기존 교통 혼잡 및 기후대응 공간의 부족과 어떤 관계가 있는가?”
- Primary: “극한기온에서 서울시 내 65세 이상 지하철 이용자의 이용 변화는 비고령층과 다르게 나타나는가?”
- Secondary 1: “이러한 연령별 차이는 10~16시 주간 비첨두 시간대에서 더 강하게 나타나는가?” 시간대의 최종 운영 정의·검증은 분석 Stage에서 한다.
- Secondary 2: “이러한 차이는 서울 내 역·행정동별로 어떻게 다르며, 지역의 고령인구와 기후대응 공간 조건과 어떤 관계가 있는가?”

연구질문 자체는 현재 working question으로 확정되었다. 최종보고서 문장은 분석결과 후 조정 가능하며, 정책결론은 미확정이고 분석결과는 아직 없다. Stage 2는 가설을 검정하지 않는다. Aggregate ridership으로 trip purpose를 증명할 수 없어 최대 “기후회피형 이동과 일치하는 패턴”으로 해석한다.

현재 8개 Raw 데이터셋에는 일별 실제 혼잡 core dataset이 없다. 혼잡 관계는 Stage 2 증거 범위 밖이며 적합한 자료를 확보한 뒤 secondary analysis로 추가하거나 분석 단계에서 최종 연구질문 범위를 조정한다. 자료 없는 혼잡 결과를 예고·추론하지 않는다. Shelter는 clean 보조 공간 layer이며 기후대응 공간 부족의 결과도 아직 없다.

| 최종보고서 항목 | 현재 근거 | 상태와 다음 작업 |
|---|---|---|
| 분석 배경·목적·문제·필요성 | 승인된 [전처리 설계](../../../docs/superpowers/specs/2026-10-03-subway-data-preprocessing-design.md), 사용자 연구 목적 | 위 working question·primary·secondary 질문 확정. 필요성의 최종 논증과 보고서 문장은 근거·분석결과 후 조정; 분석결과·정책결론은 아직 없음 |
| 활용 데이터 | [Raw 연구 기록](01-raw-data-baseline.md), [기술 baseline](../../../docs/subway/2024-raw-schema-baseline.md) | 원래 7종·11 files 보존 + 승인된 직접 65+ source 1종·1 file 확장 |
| 출처·제공기관·URL | [manifest](../../data_manifest.csv) | 확인된 값만 기록. 빈 다운로드일·라이선스 등은 미확인; 제출 전 공식 출처 재검토 |
| 기준시점·기간 | manifest, [source contracts](../../config/source_contracts_2024.yaml) | 승하차·기상 2024, 기존 인구 Q2–Q4는 보조 검증, 직접 65+ Q2가 primary, 경계 2024-06-30. 역 좌표는 승인된 snapshot-stability/CRS 분석 가정과 exclusions 적용; source-specific 검증 및 쉼터 시점 한계 유지 |
| 수집 및 전처리 | Raw baseline, Stage 1 코드·tests, [Stage 2 계획](../../../docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md) | Raw 검사·provenance·재현성 및 Tasks 1–10 구현·검증; Task9 인간 승인; Task10 E2E COMPLETE / 인간 결과 검토 PENDING; Task11 미착수 |
| 분석 방법론 | [방법론 로그](methodology-log.md) | schema inspection·SHA-256·재현성 및 승인된 전처리 adopted. 통계모형은 candidate |
| AI 서비스·범위·주요 프롬프트 | [AI 사용 기록](ai-usage-log.md) | ChatGPT/Codex 역할과 주요 지시 요약 기록. 인간 검증은 증거가 있는 범위만 기록 |
| 분석 결과 | 아직 없음 | 미완료. Stage 1 검사 성공을 연구 결과로 대체하지 않음 |
| 정책 제안·기대효과 | 아직 없음 | 미완료. 분석 후 작성 |
| 결과 이미지 | 아직 없음 | 미완료. EDA/시각화는 이후 분석 Stage |
| GitHub 재현 코드 | 저장소의 `subway/tools/inspect_raw_inputs.py`, `subway/tests/`, 기술 baseline | Stage1 및 `python subway/run_pipeline.py --year 2024` 재현 가능. Task11 최종 closeout 미착수. 최종보고서에 배포 시 확인된 repository/commit 링크 추가 |

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
