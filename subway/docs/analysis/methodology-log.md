# 개인 subway 방법론 기록

작성일: 2026-10-06. `adopted`는 실제 수행·검증된 범위만 의미한다. Stage 2 전처리 기법은 구현·검증 후에만 adopted로 갱신한다.

| 방법명 | 목적 | 선택 이유 | 상태 | 검증 근거 | 주의사항 |
|---|---|---|---|---|---|
| Raw schema inspection | 형식·컬럼·인코딩·행 수·CRS 입력 계약 확인 | 추측 기반 전처리 방지 | adopted | schema snapshot, source contracts, 16 tests, 실제 inspection exit 0 | loadability는 값·join·geometry 품질 보증이 아님 |
| SHA-256 provenance/integrity validation | 원본 snapshot 식별·불변 확인 | 파일명만으로 동일 입력 보장 불가 | adopted | inventory 11개, manifest primary 7개, Raw 전후 SHA-256 불변 | 출처의 신뢰성·모집단 적합성을 hash로 증명하지 못함 |
| Deterministic reproduction validation | 동일 입력의 검사 산출물 반복 재현 | 변경 추적·검토 가능성 확보 | adopted | 검사 2회 생성 파일 hash 불변, diff/staged diff 없음, Git clean | Stage 1 출력만 검증; Stage 2 Parquet는 미검증 |
| PPML | 계수형 승하차 자료의 모형 후보 검토 | 연구 질문·분포·식별 조건에 따라 적합성 검토 | candidate | 아직 fit·진단·비교 없음 | 전처리 완료 후 검토; 현재 채택 아님 |
| GAM / spline | 비선형 관계 후보 검토 | 함수 형태의 유연성 검토 | candidate | 실행 근거 없음 | 복잡도·해석·과적합을 추후 검토 |
| Interaction-effect model | 변수 간 조건부 관계 검토 | 연구 질문에 필요한 경우 검토 | candidate | 실행 근거 없음 | 변수 정의·식별 조건 미확정 |
| Three-way interaction | 세 요인의 조건부 관계 검토 | 명시적 연구 가설이 있을 때만 검토 | candidate | 실행 근거 없음 | 표본 지지·해석 가능성 확인 필요 |
| Fixed effects | 관측되지 않은 단위별 차이의 처리 후보 | 패널 구조와 연구 설계에 따라 검토 | candidate | 실행 근거 없음 | 식별·변동·단위 정의 미확정 |
| Sensitivity analysis | 후속 분석의 가정 의존성 평가 | 분석 선택의 견고성 검토 | candidate | 실행 근거 없음 | 실제 분석과 대안 설정 확정 이후 수행 |

Stage 2 계획의 wide→long, alias mapping, crosswalk, 인구 집계 및 Point-in-Polygon은 모두 **계획 상태**다. 이번 문서 작성으로 adopted가 되지 않는다. 분석 후보의 선택 이유는 검토 목적이며 특정 방법의 적합성이 검증되었다는 진술이 아니다.
