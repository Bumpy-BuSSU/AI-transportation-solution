# Mobility Choice 통합 기록

## 범위와 기준

Bumpy-BuSSU/AI-transportation-solution을 최종 공동 저장소로 사용한다. s-min04의 전체 분석 구조와 ilwoo-maker의 지하철 분석을 함께 보존한다.

- 기준 `dev`: `b6957032de9206263d4be53c975a137974e79737`
- 상류: https://github.com/s-min04/mobility_choice
- 상류 기준 커밋: `a841eeb518483ad0ef6dc2ae3256480988c6c237`
- 통합 브랜치: `integration/mobility-choice`
- 방식: unrelated histories merge. 양쪽 부모 및 기존 작성자 이력을 보존한다.

## 충돌 해결

공통 경로는 `.gitignore`, `README.md` 두 파일이다. `.gitignore`는 기존 Python·지하철 규칙을 유지하며 루트 `data/raw/manifest.csv`만 원본 제외 규칙에서 예외로 둔다. README는 두 분석의 안내로 갱신하며 상류 README 원문은 `docs/mobility-choice-upstream-README.md`에 보존한다.

상류 README 원문은 상대 링크까지 원본 그대로 보관한 기록이며, 링크를 따라 실행 안내를 읽을 때는 루트 README에 연결한 상류 기준 버전을 사용한다.

기존 `docs/collaboration.md`에는 확장된 분석 영역과 별도 실행환경을 반영한다. s-min04의 분석은 따릉이만을 다루지 않으므로 `bike/`로 옮기지 않는다. 루트 분석 코드·입력·결과와 `subway/` 파일은 수정하지 않는다. 새 통합 실행기나 공통 의존성 파일은 추가하지 않는다.

## 데이터와 기존 결과

상류 저장소에 이미 추적된 가공 데이터·결과·원본 출처 manifest를 가져온다. 기존 지하철 파일은 그대로 유지한다. 이번 작업에서 새로운 원본 자료를 내려받거나 추가하지 않는다. 기존 `docs/report.pdf`는 상류의 과거 보고서이며 최신 제출본으로 표시하지 않는다.

## 검증

- 파일 보존: 기준 저장소 193개 및 상류 163개 파일을 Git blob 해시로 비교했다. 의도적으로 수정한 README·제외 규칙·협업 문서를 제외한 기존 파일은 모두 동일하다. 양쪽 공통 파일은 README와 `.gitignore`뿐이다.
- 제외 규칙: 루트·지하철 원본 및 두 로컬 가상환경은 제외되고 루트 원본 출처 manifest는 추적 가능한 것을 확인했다. 새 원본 파일은 추가하지 않았다.
- 통합 전후 지하철 테스트: 같은 Python 3.12 환경에서 각각 184 tests 실행, 각각 1 failure·18 errors. 실패/오류 19개 항목의 이름이 완전히 같았다. 경계 SHP와 부속 파일, 역 등 로컬 원본 누락으로 인한 실패이며 전체 PASS로 표시하지 않는다. `setUpClass` 오류도 포함하므로 검사 개수와 오류 항목 개수는 별개다.
- 검증 환경: pandas 3.0.6, geopandas 1.2.0, pyogrio 0.12.1, matplotlib 3.10.7, statsmodels 0.15.0. 이 실행환경에서 pyogrio 0.13.0은 import 단계 SIGBUS가 발생해 0.12.1로 확인했다. pandas 2.2.3에서는 기존 categorical outer join 테스트가 실패했고 3.0.6에서는 통과했다. 저장소의 의존성 파일은 변경하지 않았다.
- 상류 기준 복사본에서 `python run_all.py --quick`: 05·07·15·16·20·22의 6단계 완료. 원본 다운로드를 포함한 전체 24단계 재현은 아니다.
- 통합 트리의 별도 복사본에서 `python run_all.py --only 15 16 22`: 3단계 완료. 원래 추적된 결과 파일을 덮어쓰지 않았다.
- 통합 복사본에서 재계산한 표 10개(`e4_slopes`, `e5_scenarios`, `e6_dong_reduction`, `e7_sensitivity`, `f1_quadrants`, `f2_dong_quadrant`, `f3_fare_incidence`, `f4_place_policies`, `f5_vkt_share`, `l1_cost_effect`)는 저장된 표와 pandas 값 비교에서 일치했다(상대·절대 허용오차 1e-8).
- 검토: 별도 읽기 전용 리뷰에서 통합으로 새로 생긴 결함을 발견하지 않았다. 원본 노트북은 상류 저장소를 복제하므로 통합 저장소의 실행 명령과 구분하도록 README에 표시했다.
- 남은 확인: 원본 자료를 갖춘 환경에서 지하철 전체 테스트 및 두 분석의 전체 재실행. 새로운 원본을 다운로드해 검증하지 않았다. 환경을 고정하는 추가 작업은 별도 검토 대상이다.

CSV에 원래 있던 CRLF 줄바꿈을 유지했다. 일반 `git diff --check`는 원본 manifest의 CR을 공백으로 보고하므로 `git -c core.whitespace=cr-at-eol diff --cached --check`로 확인했다.

## 반영 절차

`integration/mobility-choice`에서 검증 후 `dev` 대상 PR로 제안한다. PR 병합 시 merge commit을 사용해야 상류 전체 이력이 `dev`에서도 보존된다. `main`은 제출 결과 점검 후 별도 PR로 반영한다.
