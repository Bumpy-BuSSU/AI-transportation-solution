# 실행 방법

[프로젝트 소개](../README.md) · [검증 기록](validation.md) · [데이터 출처](data-and-ai.md)

모든 명령은 저장소 루트에서 실행합니다. 분석 경로와 의존성 파일을 따르며, 실행하면 해당 결과 폴더의 파일이 갱신될 수 있습니다. 저장된 결과는 먼저 별도 보관하거나 새 작업 폴더에서 실행하세요.

## 저장소 받기

```bash
git clone --branch dev https://github.com/Bumpy-BuSSU/AI-transportation-solution.git
cd AI-transportation-solution
```

현재 안내는 `dev` 기준입니다. 검증 기록의 분석 코드로 고정하려면 다음 명령을 사용합니다. 이 커밋에는 이후의 README 개편이 포함되지 않습니다.

```bash
git checkout 6c8581a1705d6e0304e38c17a312a57ecf56e44e
```

개발을 이어갈 때는 `git switch dev`로 돌아옵니다.

## 가공 자료로 빠른 실행

원본이 필요 없는 05·07·15·16·20·22의 여섯 단계만 실행합니다. 전체 24단계 재현이나 지하철 원본 전처리를 포함하지 않습니다.

```bash
python -m venv .venv-mobility
```

| 환경 | 활성화 |
| --- | --- |
| Windows PowerShell | `.\.venv-mobility\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv-mobility/bin/activate` |

```bash
python -m pip install -r requirements.txt
python run_all.py --quick
```

탄소·정책·비용 단계만 실행하려면:

```bash
python run_all.py --only 15 16 22
```

한글 그래프에는 NanumGothic·맑은 고딕 등 코드에서 지원하는 한글 글꼴이 필요합니다.

## 원본부터 전체 분석

```bash
python run_all.py
```

`data/raw/manifest.csv`와 `scripts/01_download.py`에 출처와 수집 경로가 있습니다. 원본 다운로드·처리가 포함되므로 데이터 제공처의 접근 가능 여부와 실행 시간을 확인하세요. 특정 단계부터 시작할 때는 선행 산출물이 필요합니다.

```bash
python run_all.py --from 14
```

결과는 `outputs/tables/`와 `outputs/figures/`에 저장됩니다.

## 2024년 지하철 날씨 검증

지하철 분석용 환경을 사용합니다. 위 환경을 사용 중이면 먼저 `deactivate`로 종료합니다.

```bash
python -m venv .venv-subway
```

| 환경 | 활성화 |
| --- | --- |
| Windows PowerShell | `.\.venv-subway\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv-subway/bin/activate` |

```bash
python -m pip install -r subway/requirements.txt -r subway/requirements-analysis.txt
```

원본 자료는 `subway/data_manifest.csv`, `subway/config/datasets.yaml`, `subway/config/source_contracts_2024.yaml`의 경로와 승인된 파일·해시를 따라 준비합니다. 역 좌표·경계·승하차·기상 등 원본이 모두 저장소에 포함된 것은 아닙니다.

```bash
python subway/run_pipeline.py --year 2024
python subway/run_eda.py --year 2024
python subway/run_confirmatory.py --year 2024
python subway/run_spatial_heterogeneity.py --year 2024
```

테스트:

```bash
python -m unittest discover -s subway/tests -v
```

테스트 일부도 원본 자료를 읽습니다. 폴더만 만들거나 저장된 CSV만 복사하면 전체 검사를 통과할 수 있는 것은 아닙니다.

## 확인된 실행환경

| 확인 환경 | 버전·범위 |
| --- | --- |
| 데스크탑 지하철 테스트 | Python 3.11.9, pandas 3.0.6, geopandas 1.2.0, pyarrow 25.0.1, matplotlib 3.10.7, statsmodels 0.15.0. 195 tests OK |
| 별도 실행 확인 | Python 3.12, pandas 3.0.6, geopandas 1.2.0, pyogrio 0.12.1, matplotlib 3.10.7, statsmodels 0.15.0 |

검증한 범위와 환경 차이는 [검증 기록](validation.md)을 따릅니다. 의존성 파일 전체가 버전 고정된 환경 잠금 파일은 아닙니다. 한 환경에서의 통과가 모든 운영체제·버전의 실행을 보장하지는 않습니다.
