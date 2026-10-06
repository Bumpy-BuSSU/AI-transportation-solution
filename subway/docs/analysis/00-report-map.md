# 개인 subway 분석보고서 근거 지도

이 문서는 사용자 개인의 subway 연구 기록이다. 팀 공통 규칙이 아니며 bike/, common/, top-level README에 적용하지 않는다. 기록일: 2026-10-06. Stage 1 COMPLETE / 승인된 baseline 확장 8종·12 files / Stage 2 Tasks 1–4, 6–8 COMPLETE; Task 5 BLOCKED, Task 9–11 NOT STARTED. 최신 근거: [Batch 2R-B](03-approved-authority-adoption.md).

## 현재 working research questions

전체 팀 주제: **“탄소중립 교통 전환 속 고령자의 이동 선택권 격차 분석 — 공공자전거와 도시철도를 중심으로”**. 이 기록은 subway 범위만 다룬다.

- Subway 전체 질문: “극한기온은 서울 고령층의 지하철 이용 패턴을 어떻게 변화시키며, 이러한 변화는 기존 교통 혼잡 및 기후대응 공간의 부족과 어떤 관계가 있는가?”
- Primary: “극한기온에서 65세 이상 고령층의 지하철 이용 변화가 비고령층과 다르게 나타나는가?”
- Secondary: “연령별 차이가 존재한다면 그 차이가 10~16시 daytime/off-peak에서 더 강하게 나타나는가?” Daytime의 최종 정의·검증은 분석 Stage에서 한다.

연구질문 자체는 현재 working question으로 확정되었다. 최종보고서 문장은 분석결과 후 조정 가능하며, 정책결론은 미확정이고 분석결과는 아직 없다. Stage 2는 가설을 검정하지 않는다. Aggregate ridership으로 trip purpose를 증명할 수 없어 최대 “기후회피형 이동과 일치하는 패턴”으로 해석한다.

현재 8개 Raw 데이터셋에는 일별 실제 혼잡 core dataset이 없다. 혼잡 관계는 Stage 2 증거 범위 밖이며 적합한 자료를 확보한 뒤 secondary analysis로 추가하거나 분석 단계에서 최종 연구질문 범위를 조정한다. 자료 없는 혼잡 결과를 예고·추론하지 않는다. Shelter는 clean 보조 공간 layer이며 기후대응 공간 부족의 결과도 아직 없다.

| 최종보고서 항목 | 현재 근거 | 상태와 다음 작업 |
|---|---|---|
| 분석 배경·목적·문제·필요성 | 승인된 [전처리 설계](../../../docs/superpowers/specs/2026-10-03-subway-data-preprocessing-design.md), 사용자 연구 목적 | 위 working question·primary·secondary 질문 확정. 필요성의 최종 논증과 보고서 문장은 근거·분석결과 후 조정; 분석결과·정책결론은 아직 없음 |
| 활용 데이터 | [Raw 연구 기록](01-raw-data-baseline.md), [기술 baseline](../../../docs/subway/2024-raw-schema-baseline.md) | 원래 7종·11 files 보존 + 승인된 직접 65+ source 1종·1 file 확장 |
| 출처·제공기관·URL | [manifest](../../data_manifest.csv) | 확인된 값만 기록. 빈 다운로드일·라이선스 등은 미확인; 제출 전 공식 출처 재검토 |
| 기준시점·기간 | manifest, [source contracts](../../config/source_contracts_2024.yaml) | 승하차·기상 2024, 기존 인구 Q2–Q4는 보조 검증, 직접 65+ Q2가 primary, 경계 2024-06-30. 역 좌표의 2024 적합성·쉼터 시점은 미확정 |
| 수집 및 전처리 | Raw baseline, Stage 1 코드·tests, [Stage 2 계획](../../../docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md) | Raw 검사·provenance·재현성 및 승인된 Tasks 1–8 범위 구현·검증; Task 5 BLOCKED, Task 9–11 미착수 |
| 분석 방법론 | [방법론 로그](methodology-log.md) | schema inspection·SHA-256·재현성 및 승인된 전처리 adopted. 통계모형은 candidate |
| AI 서비스·범위·주요 프롬프트 | [AI 사용 기록](ai-usage-log.md) | ChatGPT/Codex 역할과 주요 지시 요약 기록. 인간 검증은 증거가 있는 범위만 기록 |
| 분석 결과 | 아직 없음 | 미완료. Stage 1 검사 성공을 연구 결과로 대체하지 않음 |
| 정책 제안·기대효과 | 아직 없음 | 미완료. 분석 후 작성 |
| 결과 이미지 | 아직 없음 | 미완료. EDA/시각화는 이후 분석 Stage |
| GitHub 재현 코드 | 저장소의 `subway/tools/inspect_raw_inputs.py`, `subway/tests/`, 기술 baseline | Stage 1 명령 재현 가능. Stage 2 `run_pipeline.py` 미구현. 최종보고서에 배포 시 확인된 repository/commit 링크 추가 |

현재 근거가 없는 항목에는 결과·정책·수치·그림을 만들어 넣지 않는다. 각 후속 Stage 종료 시 해당 문서와 검증 결과를 연결한다.
