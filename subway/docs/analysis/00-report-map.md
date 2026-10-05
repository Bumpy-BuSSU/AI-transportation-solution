# 개인 subway 분석보고서 근거 지도

이 문서는 사용자 개인의 subway 연구 기록이다. 팀 공통 규칙이 아니며 bike/, common/, top-level README에 적용하지 않는다. 기록일: 2026-10-06. Stage 1 COMPLETE / Stage 2 계획 작성, 구현 미착수.

| 최종보고서 항목 | 현재 근거 | 상태와 다음 작업 |
|---|---|---|
| 분석 배경·목적·문제·필요성 | 승인된 [전처리 설계](../../../docs/superpowers/specs/2026-10-03-subway-data-preprocessing-design.md), 사용자 연구 목적 | 데이터 준비 목적 확인. 최종 연구 질문·필요성 논증은 아직 미확정이며 설계에서 추론해 작성하지 않음 |
| 활용 데이터 | [Raw 연구 기록](01-raw-data-baseline.md), [기술 baseline](../../../docs/subway/2024-raw-schema-baseline.md) | 7종 입력·파일 형식 확인 완료 |
| 출처·제공기관·URL | [manifest](../../data_manifest.csv) | 확인된 값만 기록. 빈 다운로드일·라이선스 등은 미확인; 제출 전 공식 출처 재검토 |
| 기준시점·기간 | manifest, [source contracts](../../config/source_contracts_2024.yaml) | 승하차·기상 2024, 인구 Q2–Q4 입력 중 Q2 사용 계획, 경계 2024-06-30. 역 좌표의 2024 적합성·쉼터 시점은 미확정 |
| 수집 및 전처리 | Raw baseline, Stage 1 코드·tests, [Stage 2 계획](../../../docs/superpowers/plans/2026-10-05-subway-clean-transform-pipeline.md) | Raw 검사·provenance·재현성 완료. clean/processed 전처리는 미구현 |
| 분석 방법론 | [방법론 로그](methodology-log.md) | schema inspection·SHA-256·재현성 검사만 adopted. 통계모형은 candidate |
| AI 서비스·범위·주요 프롬프트 | [AI 사용 기록](ai-usage-log.md) | ChatGPT/Codex 역할과 주요 지시 요약 기록. 인간 검증은 증거가 있는 범위만 기록 |
| 분석 결과 | 아직 없음 | 미완료. Stage 1 검사 성공을 연구 결과로 대체하지 않음 |
| 정책 제안·기대효과 | 아직 없음 | 미완료. 분석 후 작성 |
| 결과 이미지 | 아직 없음 | 미완료. EDA/시각화는 이후 분석 Stage |
| GitHub 재현 코드 | 저장소의 `subway/tools/inspect_raw_inputs.py`, `subway/tests/`, 기술 baseline | Stage 1 명령 재현 가능. Stage 2 `run_pipeline.py` 미구현. 최종보고서에 배포 시 확인된 repository/commit 링크 추가 |

현재 근거가 없는 항목에는 결과·정책·수치·그림을 만들어 넣지 않는다. 각 후속 Stage 종료 시 해당 문서와 검증 결과를 연결한다.
