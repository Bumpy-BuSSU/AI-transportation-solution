# 개인 subway AI 사용 기록

작성일: 2026-10-06. 모든 대화를 보관하지 않고 의사결정에 영향을 준 사용만 기록한다. 정확한 원문을 보유하지 않은 과거 사용은 **주요 지시 요약**으로 기록한다. ChatGPT의 과거 역할은 사용자가 이번 Mission에 제공한 역할 기록에 근거하며, 이 저장소 조사에서 해당 대화 원문을 독립 확인하지 않았다.

| AI 서비스 | Stage | 활용 목적·범위 | 주요 지시 요약 | AI 제안/수행 | 인간 검증 | 최종 채택 여부 |
|---|---|---|---|---|---|---|
| ChatGPT | 설계 / Stage 1 | 연구 목적에 맞는 데이터 구성, Raw 기준과 preprocessing architecture 설계 보조 | Raw 불변·provenance·검증을 갖춘 지하철 전처리 설계 | 7종 구성 및 단계별 검사 방향 보조 | 사용자 제공 Mission에 승인 설계가 있다고 명시. 상세 인간 검토 과정은 원문 미보유 | 승인 설계가 저장소에 존재; 분석모형 채택은 아님 |
| ChatGPT | Stage 1 | Population CSV 손상 진단 방향과 SpreadsheetML 대체 전략 판단 | 손상 Raw를 수선하지 않고 동일 조건 대체 export 확인 | 진단 방향·대체 전략 보조 | 사용자 제공 기록 및 baseline에 대체 입력 선택 기재. 사람의 개별 검증 동작·프롬프트 원문은 미확인 | SpreadsheetML 입력 채택; 데이터 sheet·test는 코드 근거로 확인 |
| ChatGPT | Stage 1 / 계획 | Codex Mission Prompt 작성 및 Codex 결과 정밀검토 보조 | 구현·검증·범위 제한을 명확히 하는 작업 지시 작성 | 작업 지시와 검토 관점 보조 | 이번 Mission은 인간 사용자가 전달. 과거 리뷰의 전체 내역은 미확인 | 이번 문서 Mission 지시 채택; Stage 2 구현 승인으로 해석하지 않음 |
| Codex | Stage 1 | repository/code 직접 조사, SpreadsheetML 지원·regression test | 실제 형식과 데이터 sheet를 확인하고 Raw 수정 없이 지원 | 현재 코드에 형식 인식·worksheet 분리·regression test 존재; 과거 역할은 사용자 기록에 근거 | 인간의 개별 수동 검사 내역은 미보유. 16 tests와 실제 inspection은 자동 검증으로 구분 | 현재 브랜치에 구현 존재 |
| Codex | Stage 1 종료 | Git working-tree/index 문제 systematic debugging | 원인→가설→최소 실험→최소 수정→전체 검증, 추측성 수정 금지 | blob/바이트/attributes/mode/stat 비교; 임시 index 실험 후 5개 stat cache 갱신 | 사용자에게 증거·결과 보고. 자동 hash/test/Git 확인을 인간 검증으로 표기하지 않음 | 내용 변경 없는 index 수정 완료; LF 정책 유지 |
| Codex | Stage 1 종료 | unit test·inspection·hash·Git clean-state 검증 | 16 tests, inspection 0, Raw 불변, 반복 실행 clean 확인 | 실제 명령 실행 및 결과 확인 | 사용자 수동 재실행 여부는 확인되지 않음; 자동 검증 결과는 technical baseline 참조 | Stage 1 완료 근거로 기록 |
| Codex | Stage 1 closeout / Stage 2 계획 | 기존 문서·코드·Raw 읽기 전용 조사와 계획 작성 | Stage 2 구현 없이 closeout·개인 기록·작업별 TDD 계획만 작성 | crosswalk·이름·인구 계층의 미확정 사항 식별; 문서 작성 | 초기 작성 당시 인간 리뷰 전. 이후 인간 리뷰에서 기술 계획 구조 승인·research context 보정 요구 확인; 구현 승인은 아직 아님 | 문서 기록 완료 시점의 계획이며 구현·alias·CRS 채택 아님 |
| Codex + 인간 리뷰 | Stage 2 계획 보정 | 확정 working research questions와 정보 보존·severity 계약 정합성 보정 | 2026-10-06 Mission: Research-context correction before Stage 2 implementation | 기존 11 Task를 유지하고 연구 맥락·혼잡 scope gap·senior>total escalation 문서를 보정 | Stage 2 planning output은 인간 검토를 받았고 기술 구조는 승인됨. Research context 부족에 대한 수정 요구가 이번 Mission으로 전달됨 | 문서 보정 지시 채택; Stage 2 구현 승인은 아직 아님 |

앞으로 주요 Codex Mission Prompt는 가능한 경우 원문을 보존하거나 제목·날짜·첨부 식별자 등 명확한 prompt reference를 남긴다. 과거 원문을 재구성하거나 창작하지 않는다. 이번 보정의 원문 reference는 사용자 첨부 **“Mission: Research-context correction before Stage 2 implementation”**, 2026-10-06, attachment ID `6a410799-1908-4927-bb78-513e8d7044a4`의 `붙여넣은 텍스트.txt`다. 이는 원문 참조이며 새로 만든 prompt 원문이 아니다.

AI 제안, AI가 실행한 자동 검사, 인간의 승인·수동 검증은 서로 다른 증거다. 출처 의미·CRS·alias처럼 아직 확인되지 않은 사항은 AI가 제안하더라도 확인 완료로 기록하지 않는다.

P-S2-B1A: **Task 3 crosswalk evidence resolution and Batch 1 hardening**. 원문 reference: 2026-10-06 사용자 첨부 “Mission: Stage 2 Batch 1A — Resolve Task 3 and Harden Batch 1”, attachment ID `0cc290f3-39e4-4b28-90f8-36bb2e8fe1eb`. 인간이 해당 Mission에서 8개 키의 source-name 관계와 서울특별시고시 제2024-521호 「도시철도 역명 개정 확정 고시」(2024-10-31)를 검토 근거로 제공하고 명시적 alias 채택을 지시했다. Codex는 두 Raw 파일의 같은 code 및 total 고유 line/이름을 자동 재검증하고, 나라장터 노원구 「불암산역·삼각지(전쟁기념관)역 역명개정 정비사업 과업지시서」(2025.4., 2쪽)의 고시 참조를 확인했다. 공식 supporting URL은 `station_aliases.csv`의 evidence에 기록한다. 종로3가 부역명 차이는 인간 검토 source alias이며 공식 개명이라고 주장하지 않는다.

분석 identity의 canonical label은 **2024 total_ridership 명칭으로 고정**한다. 확인된 개명·부역명·문장부호 변형은 명시적 alias로만 같은 identity에 연결하며 Raw 명칭은 보존한다. 이는 현재 공식 표시 역명에 대한 주장이 아니다. Alias는 이름 관계별 5행·빈 line으로 기록하고, line은 각 code+canonical name의 total 고유 후보에서 구한다. Codex가 추가한 alias/ID 안정성 및 writer 정렬 테스트와 hash 검증은 자동 검사이며 인간의 수동 재실행으로 기록하지 않는다. Writer byte 재현성 범위는 summary에 기록한 동일 Python/pandas/NumPy/pyarrow/GeoPandas/Shapely 환경이다.
