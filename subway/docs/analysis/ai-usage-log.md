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

P-S2-B1A: **Task 3 crosswalk evidence resolution and Batch 1 hardening**. 원문 reference: 2026-10-06 사용자 첨부 “Mission: Stage 2 Batch 1A — Resolve Task 3 and Harden Batch 1”, attachment ID `0cc290f3-39e4-4b28-90f8-36bb2e8fe1eb`. ChatGPT가 서울특별시고시 제2024-521호 「도시철도 역명 개정 확정 고시」(2024-10-31)의 공식 supporting evidence 후보를 조사·제안했다. Codex는 두 Raw 파일의 같은 code 및 total 고유 line/이름을 자동 재검증하고, 나라장터 노원구 「불암산역·삼각지(전쟁기념관)역 역명개정 정비사업 과업지시서」(2025.4., 2쪽)의 고시 참조와 source-name 관계를 재확인했다. 인간 사용자는 결과 mapping 제안·보고를 검토하고 명시적 alias 채택을 승인했다. 이는 인간이 고시를 직접 발견하거나 독립적으로 열람했다는 기록이 아니다. 공식 supporting URL은 `station_aliases.csv`의 evidence에 기록한다. 종로3가 부역명 차이는 인간 검토 source alias이며 공식 개명이라고 주장하지 않는다.

분석 identity의 canonical label은 **2024 total_ridership 명칭으로 고정**한다. 확인된 개명·부역명·문장부호 변형은 명시적 alias로만 같은 identity에 연결하며 Raw 명칭은 보존한다. 이는 현재 공식 표시 역명에 대한 주장이 아니다. Alias는 이름 관계별 5행·빈 line으로 기록하고, line은 각 code+canonical name의 total 고유 후보에서 구한다. Codex가 추가한 alias/ID 안정성 및 writer 정렬 테스트와 hash 검증은 자동 검사이며 인간의 수동 재실행으로 기록하지 않는다. Writer byte 재현성 범위는 summary에 기록한 동일 Python/pandas/NumPy/pyarrow/GeoPandas/Shapely 환경이다.

P-S2-B2: **Stage 2 Tasks 4–7 source cleaning and spatial-input validation**. 원문 reference: 2026-10-06 사용자 첨부 “Mission: Stage 2 Implementation Batch 2 — Tasks 4 to 7”, attachment ID `182b8532-9f05-48c0-9d3a-ee5a788a582b`.

ChatGPT는 Batch 1A를 검토하고 AI-log 역할 표기 보정을 제안했으며, 공식 station/population/KMA metadata와 evidence 제약을 검토하여 Batch 2 Mission을 작성했다. Codex는 저장소 로컬 구현, RED→GREEN 테스트, 실제 Raw 정제·미매칭 진단, hash/회귀/재현성 자동 검증을 수행했다. 별도 코드 리뷰에서 발견한 중복 역 진단 소실과 null 인구 단위 검증 결함은 실패 테스트로 재현 후 수정했다. 인간의 Batch 2 수용 여부 및 Task 8 시작 승인은 **아직 대기 중**이다.

Task 4는 108번 단일 지점·366일·9개 변수를 보존하며 빈 강수/적설/풍속은 missing으로 유지한다. Task 5는 205 exact / 69 ridership-only / 71 station-only 및 전체 후보를 기록한다. 새 station alias는 채택하지 않았고 CRS·2025 snapshot의 2024 적용성은 미확인으로 Task 5 BLOCKED다. Task 6은 다운로드 메타정보의 표명·출처·명 단위, 공식 25구 표시, SGIS 공식 단계별 코드 설명과 전체 source 순서 및 경계 parent별 완전한 동 집합을 대조하여 25구·426동 계층을 검증했다. 동명 `.`/`·` 차이 7개는 설정의 명시적 관계로만 처리하며 원본 표기는 보존한다. 이는 여러 자료의 완전 집합 대조에 근거한 Codex의 계층 판정이다. 그러나 26동의 Q2 계 항목 32셀에 있는 `-`의 이 표에 대한 의미는 확정하지 못했다. 0 대체 없이 해당 동을 예외로 남기므로 Task 6 BLOCKED이며 유효 400동의 합계를 서울 전체 인구로 해석하지 않는다. 공식 항목 `계`의 산식을 창작하지 않는다.

Task 7은 원본 경계 426개 geometry·EPSG:5179·20240630 및 쉼터 412개 좌표·명시된 EPSG:5186을 검증한다. 구 이름은 검증된 인구 계층의 ADM_CD/동명 관계로만 부여하며 geometry repair나 공간 결합은 없다. 쉼터 기준시점 미확인은 WARNING으로 보존한다. Raw/manifest/Stage 1/기존 5개 senior alias/Batch 1 baseline은 그대로 유지한다. Task 8 이상은 시작하지 않는다. 상세 자동 검증 결과와 환경은 `subway/data/validation/batch2_summary.json`에 기록하며 인간 수동 검증으로 기록하지 않는다.

P-S2-B3: **Task 8 auditable senior-total ridership integration**. 원문 reference: 2026-10-06 사용자 첨부 “Mission: Stage 2 Implementation Batch 3 — Task 8 Core Ridership Integration”, attachment ID `e2cf7c25-9c96-4116-a261-165993c3f34e`.

Batch 2 population review 보정: ChatGPT가 공식 서울 등록인구 통계표의 통계부호 범례 **“- : 자료없음”**을 확인했으며, Codex는 이번 Mission을 통해 제공받은 외부 근거로 기록한다. 공식 source: https://stat.eseoul.go.kr/statHtml/statHtml.do?con=&orgId=201&tblId=DT_201003_A010006 . 이전 “의미 미확정” 표기를 “공식 자료없음”으로 정정한다. 인간이 해당 source를 독립 열람했다고 주장하지 않는다. 26동·32개 Q2 고령 연령대 셀은 여전히 결측이며 0 대체·보간·분기 변경은 없다. Task 6 BLOCKED와 유효 400동의 부분집합 해석을 유지한다. 인구 정제 구현은 변경하지 않는다.

Codex는 Task 2 정제 long 및 Task 3 승인 identity를 사용하여 date × canonical_station_id × hour_bin × boarding_type의 full outer integration을 구현했다. Raw 역코드는 공통 PK가 아니며 양쪽 provenance를 분리한다. 중복·미확인 identity는 거부하되 원본 행을 보존하며, 유효 matched에서 senior≤total일 때만 non_senior를 계산한다. total>0에서만 senior_share를 계산하고 0/0은 null이다. Station 좌표·weather·population 결합은 없고 Task 5 CRS는 null 상태다.

실제 2024 원본 대조에서 senior>total은 3셀(2역·3일·2시간대)이며 하남시청 같은 하차 시간대에서 2일 반복됐다는 점을 명시한다. 개별 예외와 파생 null은 severity에 관계없이 유지한다. 정책은 통계적 유의성 주장이 아닌 운영 품질 검사이며, count≥20(20-bin source 한 행 규모), rate≥0.0001(유효 matched 1만 셀당 1셀), 동일 date/station/boarding의 초과 hour≥2, 동일 station/hour/boarding의 반복 date≥3 중 하나면 ERROR다. 현재 3셀은 WARNING이며 source 값의 정확성을 인증하는 의미가 아니다. 정책·실제 분모·집중도·양쪽 provenance는 Batch 3 summary/exception에 기록한다.

테스트·실제 데이터 진단·Raw hash·회귀·재현성 확인은 Codex 자동 검증이다. 인간의 Batch 3 결과 수용은 **아직 대기 중**이며 Task 9는 **NOT STARTED**다. 이번 Task 8 실행 승인은 해당 Mission에 근거하며 Batch 3 결과의 사전 인간 승인을 뜻하지 않는다.


P-S2-2RA: **Task 5/6 blocker evidence resolution before spatial mapping**. 원문 reference: 2026-10-06 사용자 첨부 “Mission: Stage 2 Batch 2R-A — Resolve Task 5/6 Blockers Before Spatial Mapping”, attachment ID `6359a14e-f2d2-4f57-9057-9bfe1de8e7eb`.

**2026-10-06 인간 승인 기록: Batch 3 / Task 8 APPROVED.** ChatGPT는 remote-code/result review 후 Task 8을 수용하고 공식 역명변경 OA-22477 및 직접 65+ 인구 후보 DT_201004_O020003과 증거 gate를 제안했다. 인간 사용자는 이번 Mission에서 Task 8 결과를 승인했다. 이는 Codex 자동 테스트·진단과 별개의 수용 결정이며 인간이 테스트를 직접 재실행했다는 주장이 아니다. 앞선 “대기 중” 기록은 당시 상태다. 기존 generated Batch 3 summary의 `human_batch3_acceptance=pending`은 조사한 이전 local 생성 경로의 역사적 값으로 보존하고, 현재 수용 결정은 이 날짜별 연구 기록에 관리한다. 해당 기술 산출물은 재계산 후 세 파일 모두 baseline SHA와 같았다. 채택된 `senior_excess_policy`는 **2024 baseline QA 정책으로 고정**하며 별도 방법론 변경 승인 없이 후속 연도에 맞춰 조정하지 않는다. Task 8 승인은 Task 9 승인을 뜻하지 않는다.

Codex는 로컬 원본 재계산, 공식 파일/컬럼/API/과거 버전 조사, 별칭 gate 검증, 중복 좌표 RED→GREEN 테스트, 실제 Task 8/Task 4/7 회귀 및 인구 후보 400동 독립 대조를 수행했다. 자동 검사와 Codex의 증거 판정을 인간의 직접 source 열람이나 수동 검증으로 기록하지 않는다. 전체 station 후보 158개를 일괄 승인하지 않았으며 line-6 코드/이름 모순과 마곡/발산 좌표 충돌을 보존한다. 공식 대체 좌표는 감사 후보에 한정한다.

인구 후보는 2024Q2 25구·426동·required missing 0, 기존 유효 400동의 total/65+ 각각 exact 400·mismatch 0이다. 공식 메타정보의 분기 말 기준 및 65+ 외국인 포함을 기록한다. 신규 인구 source contract는 **인간 미승인**이고 교체 제안 후 중지한다. station 55개 명시적 alias 및 환승 3그룹 검토안은 실제 gate를 통과했으나 automatic approval review가 권위 설정 반영을 두 차례 거부하며 명시적 재승인을 요구하여, 채택하지 않고 제안으로만 보존했다. 기존 senior 5행 및 설정/Raw는 유지한다. 인간은 **Task 9 및 새로운 인구 소스를 승인하지 않았다**. Tasks 9/10/11 **NOT STARTED**. 상세 근거·한계·소스 계약 제안은 `02-spatial-input-blocker-review.md`와 Batch 2R diagnostics에 기록한다.


## P-S2-2RB — approved station evidence and direct-65+ population source adoption (2026-10-06)

ChatGPT precision-reviewed remote Batch 2R-A, approved exactly 55 reviewed station aliases, exactly three physical-transfer coordinate groups and DT_201004_O020003 source-contract adoption; it explicitly did not approve Task 9 or station CRS. The human supplied this authority and retains final project approval. No independent human rerun of Codex tests is claimed.

Codex implemented only those authoritative configurations, corrected the official-rename evidence contradiction without changing its mapping, preserved blocking code-conflict flags, and migrated Task 6 to the exact approved direct aggregate. Codex executed TDD/regression, 102 passing tests, actual 426/400/26 checks, original Raw integrity, the 8-dataset/12-file baseline extension, deterministic acceptance artifacts and unchanged Task 8/4/7 accounting. The old age source and historical 400/26 diagnostics remain validation/supplementary evidence; missing individual age bands were not manufactured. Task 5 remains BLOCKED; Task 6 COMPLETE; Task 9/10/11 NOT STARTED. See [authority adoption record](03-approved-authority-adoption.md) for gates, provenance and limits.


## P-S2-2RC — Task 5 spatial station authority audit (2026-10-07)

ChatGPT precision-reviewed Batch 2R-B, accepted Task 6 COMPLETE, identified
the official national station standard as a candidate, and designed the
separation of analytical identity / source code / spatial eligibility.
Codex audited official public sources, preserved exact local audit bytes,
found explicit station-specific WGS84 definitions in the 2024 standard,
and generated reproducible 274-identity, 21-code-conflict, 14/16-unmatched,
coordinate and temporal diagnostics plus a conditional source-contract
proposal. The portal2024 label does not authenticate the downloaded2026
bytes; exact KRIC2024/2023 exports were not acquired. Current2026 support is
never counted as authoritative2024 coverage. Codex executed RED→GREEN audit
gate tests and fresh integrity/regression checks, not human manual reruns.

The human has **NOT approved** a replacement station spatial source, a CRS
assumption or Task9. Official WGS84 standard evidence resolves the datum
research question but no CRS/source configuration is changed. The 55
approved station aliases, five senior aliases, three transfer groups, QA
policy, twelve Raw files and Task6/8 outcomes remain unchanged. Task5
**BLOCKED**; Task6/8 **COMPLETE**; Task9/10/11 **NOT STARTED**.
See [spatial authority audit](04-station-spatial-authority-audit.md).


## P-S2-2RD — Task5 closure by documented spatial eligibility (2026-10-07)

Human decision: stop pursuing perfect source resolution; retain all problematic
stations in core ridership, exclude unresolved/problematic identities only from
the spatial subset, quantify loss and retain source limitations. No further
historical KRIC search or Task9 was authorized.

ChatGPT precision-reviewed and accepted Batch2R-C, approved eligibility-based
Task5 closure, EPSG4326 as an analytical assumption supported by the official
national station standard (not verified source metadata), and practical
snapshot stability with residual temporal uncertainty.

Codex implemented the separate deterministic eligibility contract, observed
RED→GREEN tests, executed actual4million-row Task8/Task4/7 regression, quantified
status counts and all/matched observation exclusion shares, and verified exact
Raw/config/history integrity and reversed-order report hashes. A failing
actual assertion exposed an overstrict exact-KRIC-label gate for line6
삼각지; the previously audited official 병기 relationship now corroborates
identity without changing the Seoul alias or reconciling codes. No human
manual rerun is claimed. Full122 tests PASS; Task5 COMPLETE under
eligibility_based_with_documented_exclusions; Task6/8 COMPLETE;
Task9/10/11 NOT STARTED. See [eligibility closure](05-station-spatial-eligibility.md).

## P-S2-T9: strict station-to-dong Point-in-Polygon mapping — 2026-10-07

- Human: Task5 결과를 수용하고 이번 Task9 Mission을 전달했다. Task9 결과는 이후 인간 검토가 필요하며 현재 PENDING이다. 인간이 테스트를 직접 실행했다고 기록하지 않는다.
- ChatGPT: Task5 closure를 precision-review하고 Task9 구현을 승인했으며 strict spatial mapping / documented-exception 규칙을 정의했다. 첨부 Mission에 기록된 역할이다.
- Codex: GIS 변환/PIP, RED→GREEN TDD18 tests, 실제258역 diagnostics,426/426 ADM_CD population-boundary 검증, Task5/6/8 회귀와 결정성/12 Raw 불변 검사를 수행했다. 전체140 tests PASS. Task10/11 미착수.
- 결과:243 MAPPED/15 ZERO_MATCH. 인구 값은 mapped 역에만 연결하고 원본 core는 보존했다. CRS 및 시간 가정은 source-specific 확정으로 바꾸지 않았다. [증거](06-station-dong-mapping.md).
