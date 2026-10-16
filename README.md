# AI Transportation Solution

덜컹덜컹 서울버숭의 교통문제 해결 데이터 분석 프로젝트다. 이동선택권·차량 이용·탄소 분석과 2024년 서울 지하철의 날씨 반응 심층검증을 함께 관리한다.

## 분석 구성

| 영역 | 위치 | 담당 및 범위 |
| --- | --- | --- |
| 전체 분석 | `run_all.py`, `scripts/`, `data/`, `outputs/`, `notebooks/` | s-min04의 이동선택권·KT 이동·군집·날씨·혼잡·탄소 분석 |
| 지하철 심층검증 | `subway/` | ilwoo-maker의 2024년 지하철 전처리·탐색·확증검정·지역별 이질성 분석 |
| 공동 문서 | `docs/` | 협업 규칙과 통합 기록 |

`notebooks/quickstart.ipynb`는 상류 저장소를 복제하는 원본 노트북이다. 통합 저장소에서는 아래 루트 실행 명령을 사용한다.

두 분석은 기간·대상·모형이 다르다. 기존 전체 분석의 날씨 관찰과 지하철 확증검정 결과를 서로 대체하거나 동일 추정치로 합치지 않는다.

## 실행

저장소 루트에서 실행한다. 두 분석은 별도 가상환경을 사용하며 의존성 파일을 합치지 않는다.

### 전체 분석

```bash
python -m venv .venv-mobility
# 환경을 활성화한 뒤 실행
python -m pip install -r requirements.txt
python run_all.py --quick
```

`--quick`은 원본이 필요 없는 일부 단계만 실행하며 전체 분석 재현을 뜻하지 않는다. 전체 실행은 `python run_all.py`이며 원본 다운로드와 상당한 실행 시간이 필요하다. 입력·산식·단계별 설명은 [팀원 저장소의 기준 버전 README](https://github.com/s-min04/mobility_choice/blob/a841eeb518483ad0ef6dc2ae3256480988c6c237/README.md)를 참고한다. 원래 README는 상류 버전의 기록이며 통합 후 실행 검증 결과는 아래 통합 기록에서 확인한다.

### 2024년 지하철 심층검증

```bash
python -m venv .venv-subway
# 환경을 활성화한 뒤 실행
python -m pip install -r subway/requirements.txt -r subway/requirements-analysis.txt
python subway/run_pipeline.py --year 2024
python subway/run_eda.py --year 2024
python subway/run_confirmatory.py --year 2024
python subway/run_spatial_heterogeneity.py --year 2024
```

원본 입력을 별도로 준비해야 하며 저장된 결과만으로 전체 재실행이 가능한 것은 아니다. 입력 계약과 분석 단계는 [지하철 분석 안내](subway/docs/analysis/00-report-map.md), `subway/config/`와 `subway/data_manifest.csv`를 확인한다.

테스트:

```bash
python -m unittest discover -s subway/tests -v
```

## 결과와 출처

- 전체 분석: `outputs/tables/`, `outputs/figures/`, `data/raw/manifest.csv`
- 지하철 심층검증: `subway/results/`, `subway/data/validation/`, `subway/data_manifest.csv`
- `docs/report.pdf`는 팀원 저장소에서 가져온 기존 보고서 스냅샷이며 최종 제출 보고서가 아니다.
- [통합 기준·검증 기록](docs/integration/2026-10-16-mobility-choice.md)
- [협업 규칙](docs/collaboration.md)

원본 데이터는 기본적으로 Git에서 제외한다. 기존에 추적 중인 파일은 자동으로 삭제하지 않으며, 이 통합은 기존 데이터의 재배포 조건을 새로 승인하는 작업이 아니다. 데이터별 출처와 이용 조건은 각 manifest와 제공기관 안내를 따른다.
