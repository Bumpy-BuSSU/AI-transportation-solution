# 지하철 Raw 스키마 기준선 구현 계획

> **Agent 작업 지침:** 이 계획은 Task 단위로 구현한다. 구현 시 `superpowers:subagent-driven-development` 또는 `superpowers:executing-plans`를 사용한다.

**목표:** 2024년 지하철 분석에 사용할 7종 Raw 데이터를 읽기 전용으로 점검하고, SHA-256·실제 스키마·파일 형식·인코딩·CRS를 기록하여 이후 전처리 구현이 추측 없이 진행되도록 기준선을 확정한다.

**구조:** 이 단계에서는 데이터를 정제하거나 변환하지 않는다. `subway/data/raw/2024/` 아래 파일을 결정적으로 탐색하고, CSV/Excel/Shapefile 구조를 점검해 manifest와 validation 산출물을 만든다. 마지막에는 실제 관측된 컬럼명만 사용한 `source_contracts_2024.yaml`을 확정한다.

**기술 스택:** Python, pandas, pyarrow, openpyxl, geopandas, shapely, pyyaml, Python 표준 `unittest`

**설계 문서:** `docs/superpowers/specs/2026-10-03-subway-data-preprocessing-design.md`

## 전역 제약

- 주 실행 환경은 Windows + Python, 보조 환경은 Google Colab이다.
- 절대 경로를 코드에 넣지 않는다.
- Raw 데이터는 로컬에만 두고 Git에 올리지 않는다.
- Raw 기준 경로는 `subway/data/raw/2024/`이다.
- 데이터셋 ID는 다음 7개로 고정한다.
  - `senior_ridership`
  - `total_ridership`
  - `weather`
  - `station`
  - `population`
  - `boundary`
  - `shelter`
- 내려받은 Raw 파일명은 변경하지 않는다.
- SHA-256과 출처 정보를 기록하되, 확인되지 않은 메타데이터는 추측하지 않는다.
- 수동 매핑·제외·보정은 모두 명시적으로 기록한다.
- Stage 1에서 다루는 기본 형식은 CSV, XLS/XLSX, SHP다.
- Shapefile의 `.dbf`, `.shx`, `.prj`, `.cpg` 등은 inventory에는 포함하되 별도 논리 테이블로 보지 않는다.
- 같은 Raw 입력이면 versioned inspection 산출물은 동일해야 한다.
- 실행 로그는 timestamp를 포함할 수 있으나 validation 산출물에는 실행시각을 넣지 않는다.
- 이 단계에서는 EDA, 시각화, 통계검정, 회귀, ML, 정책 점수화를 하지 않는다.
- 강수·적설 결측을 자동으로 0으로 바꾸지 않는다.
- 역 코드는 데이터셋 간 공통 PK라고 가정하지 않는다.
- Python 의존성은 루트가 아니라 `subway/requirements.txt`에 둔다.
- 공통 Python 환경이나 CI는 추가하지 않는다.
- 최종 목표 명령은 `python subway/run_pipeline.py --year 2024`이지만 Stage 1에서는 구현하지 않는다.

## 중점 검토 항목

1. 하나의 데이터셋 폴더에 여러 파일 또는 여러 Excel 시트가 있을 때 임의로 하나를 고르지 않고 모두 기록한다.
2. 한글 CSV 인코딩은 정해진 후보 순서로만 판별하고 선택 결과를 기록한다.
3. Shapefile은 sidecar까지 provenance에 포함하되 실제 스키마는 `.shp` 기준으로 읽는다.
4. 기존 manifest에 수동으로 기록한 메타데이터는 재실행 시 덮어쓰지 않는다.
5. 동일 Raw 입력에서 inventory/schema/summary 산출물이 재실행해도 동일해야 한다.

---

## Task 1. Stage 1 기본 구조와 경로 계약

**생성/수정 파일**
- 생성: `subway/requirements.txt`
- 생성: `subway/config/datasets.yaml`
- 생성: `subway/src/__init__.py`
- 생성: `subway/src/ingest/__init__.py`
- 생성: `subway/src/utils/__init__.py`
- 생성: `subway/src/validate/__init__.py`
- 생성: `subway/src/utils/paths.py`
- 생성: `subway/tests/__init__.py`
- 생성: `subway/tests/test_paths.py`
- 수정: `.gitignore`

**인터페이스**
- `load_dataset_config(config_path: Path, year: int) -> dict[str, dict[str, object]]`
- `resolve_repo_relative(repo_root: Path, relative_path: str) -> Path`

### 구현 순서

- [ ] 7개 dataset ID, 2024 Raw 경로, 절대경로 거부, 누락 dataset 오류에 대한 실패 테스트 작성
- [ ] `python -m unittest subway.tests.test_paths -v` 실행 후 실패 확인
- [ ] `subway/requirements.txt` 생성
- [ ] `subway/config/datasets.yaml`에 7개 dataset ID와 repository-relative 경로만 정의
- [ ] `paths.py` 구현
- [ ] `.gitignore`에 `subway/logs/*.log` 추가
- [ ] 테스트 재실행 후 통과 확인
- [ ] 커밋: `feat: scaffold subway raw inspection`

`subway/requirements.txt`에는 아래만 둔다.

```text
pandas
pyarrow
openpyxl
geopandas
shapely
pyyaml
```

---

## Task 2. 결정적 파일 탐색과 SHA-256 inventory

**생성 파일**
- `subway/src/utils/hashing.py`
- `subway/src/ingest/discovery.py`
- `subway/tests/test_discovery.py`

**인터페이스**
- `sha256_file(path: Path) -> str`
- `discover_raw_files(dataset_id: str, dataset_dir: Path) -> list[RawFileRecord]`

`RawFileRecord` 필드:
- `dataset_id`
- `relative_path`
- `filename`
- `extension`
- `size_bytes`
- `sha256`
- `role`

`role`은 `primary`, `sidecar`, `unsupported` 중 하나다.

### 구현 순서

- [ ] SHA-256, 정렬 순서, primary/sidecar/unsupported 분류 테스트 작성
- [ ] 테스트 실패 확인
- [ ] 스트리밍 방식 SHA-256 구현
- [ ] Raw 디렉터리 재귀 탐색 및 deterministic sort 구현
- [ ] Raw 파일을 생성·수정·이름변경하지 않는지 테스트
- [ ] 전체 테스트 통과 확인
- [ ] 커밋: `data: add deterministic raw inventory`

---

## Task 3. 파일 형식별 실제 스키마 점검

**생성 파일**
- `subway/src/ingest/schema_inspector.py`
- `subway/tests/test_schema_inspector.py`

**인터페이스**
- `inspect_primary_file(path: Path) -> dict[str, object]`

### CSV

기록 항목:
- format
- encoding
- columns
- dtypes
- row_count
- loadable
- error

인코딩 후보 순서는 아래로 고정한다.

```text
utf-8-sig
utf-8
cp949
euc-kr
```

### Excel

기록 항목:
- format
- sheets
- loadable
- error

각 sheet별:
- columns
- dtypes
- row_count

여러 sheet가 있으면 임의로 하나를 선택하지 않는다.

### Shapefile

기록 항목:
- format
- columns
- dtypes
- row_count
- crs
- geometry_types
- bounds
- loadable
- error

### 구현 순서

- [ ] UTF-8-SIG/CP949 한글 CSV 테스트 작성
- [ ] 실패 확인 후 CSV inspector 구현
- [ ] 2개 sheet XLSX 테스트 작성
- [ ] Excel inspector 구현
- [ ] EPSG:5179 Shapefile 테스트 작성
- [ ] Shapefile inspector 구현
- [ ] `python -m unittest subway.tests.test_schema_inspector -v` 통과 확인
- [ ] 커밋: `data: inspect raw source schemas`

버전 관리되는 schema artifact에는 sample row 값을 저장하지 않는다.

---

## Task 4. Manifest 병합과 Raw validation

**생성 파일**
- `subway/src/ingest/manifest.py`
- `subway/src/validate/raw_validation.py`
- `subway/tests/test_manifest.py`
- `subway/tests/test_raw_validation.py`
- `subway/data_manifest.csv`

**Manifest 컬럼 순서**

```text
dataset_id
year
dataset_name
provider
source_url
raw_path
reference_date
download_date
file_format
sha256
license
notes
```

**인터페이스**
- `merge_manifest(existing: pd.DataFrame, inventory: list[RawFileRecord], year: int) -> pd.DataFrame`
- `validate_raw_stage(dataset_config, inventory, schema_snapshot) -> list[Finding]`

`Finding`:
- severity
- dataset_id
- code
- message
- relative_path

severity는 `ERROR`, `WARNING`, `INFO`만 사용한다.

### 구현 순서

- [ ] manifest 병합 테스트 작성
- [ ] 수동 메타데이터 보존 테스트 작성
- [ ] 확인되지 않은 메타데이터를 자동 생성하지 않는 테스트 작성
- [ ] 실패 확인 후 manifest 구현
- [ ] dataset 폴더 누락, primary 파일 없음, unreadable 파일, CRS 누락 등 validation 테스트 작성
- [ ] raw validation 구현
- [ ] `python -m unittest subway.tests.test_manifest subway.tests.test_raw_validation -v` 통과 확인
- [ ] 커밋: `data: add raw provenance validation`

---

## Task 5. Stage 1 CLI와 결정적 산출물

**생성 파일**
- `subway/tools/inspect_raw_inputs.py`
- `subway/tests/test_inspect_raw_inputs.py`

**실행 명령**

```bash
python subway/tools/inspect_raw_inputs.py --year 2024
```

**산출물**
- `subway/data/validation/raw_inventory.csv`
- `subway/data/validation/raw_schema_snapshot.json`
- `subway/data/validation/raw_inspection_report.csv`
- `subway/data/validation/raw_inspection_summary.json`
- 갱신된 `subway/data_manifest.csv`

ERROR가 하나라도 있으면 exit code 1, 없으면 0으로 한다.

### 구현 순서

- [ ] 임시 repository fixture 기반 E2E CLI 테스트 작성
- [ ] 동일 입력 2회 실행 시 byte-stable인지 테스트
- [ ] manifest 수동 메타데이터 보존 테스트
- [ ] dataset 누락 시 exit code 1 테스트
- [ ] 실패 확인 후 CLI 구현
- [ ] `python -m unittest discover -s subway/tests -v` 전체 통과 확인
- [ ] 커밋: `feat: add subway raw inspection command`

---

## Task 6. 실제 2024 Raw 기준선 확정

**생성/수정 파일**
- 생성/갱신: `subway/data/validation/raw_inventory.csv`
- 생성/갱신: `subway/data/validation/raw_schema_snapshot.json`
- 생성/갱신: `subway/data/validation/raw_inspection_report.csv`
- 생성/갱신: `subway/data/validation/raw_inspection_summary.json`
- 수정: `subway/data_manifest.csv`
- 생성: `subway/config/source_contracts_2024.yaml`
- 생성: `docs/subway/2024-raw-schema-baseline.md`

### 구현 순서

- [ ] `python -m pip install -r subway/requirements.txt`
- [ ] 실제 Raw 데이터 7종을 `subway/data/raw/2024/`에 배치
- [ ] `python subway/tools/inspect_raw_inputs.py --year 2024` 실행
- [ ] ERROR 0 확인
- [ ] manifest의 출처·제공기관·URL·기준시점·다운로드일·라이선스·비고를 증거 기반으로만 입력
- [ ] `source_contracts_2024.yaml`에 실제 관측된 파일·sheet·encoding·CRS·source header만 기록
- [ ] `docs/subway/2024-raw-schema-baseline.md`에 7개 데이터의 실제 파일명·컬럼·행 수·CRS·매핑 근거 정리
- [ ] inspection command 2회 재실행 후 deterministic diff 확인
- [ ] 전체 unit test 재실행
- [ ] 최종 inspection exit 0 확인
- [ ] 커밋: `data: freeze 2024 subway raw schema baseline`

## Stage 1 완료 조건

다음이 모두 충족되어야 Stage 1을 종료한다.

- 실제 2024 Raw 데이터 7종이 로컬에 존재한다.
- 모든 primary source가 loadable이다.
- 모든 Raw 파일의 SHA-256이 기록된다.
- inventory와 schema snapshot이 재현 가능하다.
- manifest의 수동 메타데이터가 재실행 후에도 유지된다.
- 행정동 경계 CRS는 추정이 아니라 실제 source에서 확인된다.
- multi-file/multi-sheet ambiguity가 모두 명시적으로 해결되거나 blocking 상태로 남는다.
- `source_contracts_2024.yaml`에는 실제 관측된 source header만 존재한다.
- `docs/subway/2024-raw-schema-baseline.md`에 관측 사실과 수동 매핑 판단이 구분되어 기록된다.
- validation ERROR가 0이다.

## Stage 1에서 하지 않는 것

- 고령/전체 승하차 정제
- 기상 데이터 정제
- 역명 canonicalization
- 인구 데이터 정제
- 기후동행쉼터 정제
- 공간 join
- senior/non-senior 파생
- `run_pipeline.py` 완성
- EDA 및 분석

Stage 1 완료 후 별도 Stage 2 구현 계획에서 아래를 수행한다.

```text
ingest
→ 7개 데이터 clean
→ clean validation
→ transform / join
→ business validation
→ processed output
→ python subway/run_pipeline.py --year 2024
```

Stage 2는 `source_contracts_2024.yaml`과 `docs/subway/2024-raw-schema-baseline.md`를 source schema의 권위 있는 기준으로 사용한다.
