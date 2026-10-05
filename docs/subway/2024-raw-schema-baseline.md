# 2024 지하철 분석 Raw 스키마 기준선

## 1. 목적

이 문서는 지하철 분석에 사용하는 2024년 Raw 데이터 7종의 실제 관측 스키마를 고정한다. Stage 1에서는 파일 형식, 인코딩, 컬럼, 행 수, CRS와 같은 입력 계약만 확인하며 정제·파생변수 생성·공간 결합·통계분석은 수행하지 않는다.

기준 산출물은 다음과 같다.

- `subway/data/validation/raw_inventory.csv`
- `subway/data/validation/raw_schema_snapshot.json`
- `subway/data/validation/raw_inspection_report.csv`
- `subway/data/validation/raw_inspection_summary.json`
- `subway/data_manifest.csv`
- `subway/config/source_contracts_2024.yaml`

## 2. Stage 1 검사 결과

실제 2024 Raw 검사에서 다음이 확인되었다.

- 데이터셋: 7종
- inventory 파일: 11개
- primary file: 7개
- ERROR: 0
- WARNING: 0
- INFO: 0
- status: `RAW INSPECTION PASSED`

11개 파일은 행정동 경계 Shapefile primary 1개와 sidecar 4개, 나머지 6개 데이터셋의 primary file로 구성된다.

## 3. 데이터별 관측 사실

### 3.1 boundary

- primary: `bnd_dong_11_2024_2Q.shp`
- format: Shapefile
- row count: 426
- CRS: `EPSG:5179`
- geometry: `Polygon`
- columns: `BASE_DATE`, `ADM_NM`, `ADM_CD`, `geometry`
- sidecar: `.dbf`, `.shx`, `.prj`, `.cpg`

Stage 2에서 지하철역 좌표를 행정동에 연결할 때 polygon layer로 사용한다.

### 3.2 population

- primary: `201_DT_201003_A010006_20261005224604.xls`
- 실제 format: SpreadsheetML(XML)
- encoding: `euc-kr`
- worksheets: `데이터`, `메타정보`
- selected sheet: `데이터`
- title row count: 1
- data row count: 8,136
- columns:
  - `동별`
  - `연령별`
  - `항목`
  - `단위`
  - `2024. 2/4`
  - `2024. 3/4`
  - `2024. 4/4`

동일 조건 CSV export에서는 마지막 레코드가 닫히지 않은 상태로 끝나는 문제가 반복되었다. Raw를 임의 수선하지 않고 동일 조건의 SpreadsheetML `.xls`를 다시 내려받아 기준 입력으로 선택했다.

Stage 2에서는 행정구 구조를 복원한 뒤 단순 동명이 아니라 `자치구 + 행정동`을 식별키로 사용한다. 65세 이상 인구 합산도 Stage 2에서 수행한다.

### 3.3 senior_ridership

- primary: `서울교통공사_역별 일별 시간대별 노인 승하차인원 정보_20260831.csv`
- format: CSV
- encoding: `cp949`
- row count: 199,398
- 주요 columns: `연번`, `수송일자`, `역번호`, `역명`, `승하차구분`, 시간대별 승하차량
- source에는 `호선` 컬럼이 없다.
- 첫 시간대는 `06시간대이전`, 마지막 시간대는 `24시간대이후`이다.

공식 설명에서 노인 권종은 65세 이상을 의미한다.

### 3.4 total_ridership

- primary: `서울교통공사_역별 일별 시간대별 승하차인원 정보_20260831.csv`
- format: CSV
- encoding: `cp949`
- row count: 199,424
- 주요 columns: `연번`, `수송일자`, `호선`, `역번호`, `역명`, `승하차구분`, 시간대별 승하차량
- 첫 시간대는 `06시이전`, 마지막 시간대는 `24시이후`이다.

senior 데이터와 양 끝 시간대 컬럼명이 다르므로 Stage 2에서 명시적으로 정규화한다. `non_senior = total - senior`는 품질검증을 통과한 매칭 행에 대해서만 생성한다.

### 3.5 weather

- primary: `OBS_ASOS_DD_20261003150614.csv`
- format: CSV
- encoding: `cp949`
- row count: 366
- columns:
  - `지점`, `지점명`, `일시`
  - `평균기온(°C)`, `최저기온(°C)`, `최고기온(°C)`
  - `일강수량(mm)`
  - `최대 풍속(m/s)`, `평균 풍속(m/s)`
  - `평균 상대습도(%)`
  - `일 최심신적설(cm)`, `일 최심적설(cm)`

강수·적설 빈값은 Stage 1에서 0으로 해석하지 않는다. 의미 확인 후 Stage 2에서 처리한다.

### 3.6 station

- primary: `서울교통공사_1_8호선 역사 좌표(위경도) 정보_20260917.csv`
- format: CSV
- encoding: `cp949`
- row count: 276
- columns: `연번`, `호선`, `고유역번호(외부역코드)`, `역명`, `위도`, `경도`, `작성일자`, `작성기준일`

역코드는 데이터셋 간 단독 primary key로 사용하지 않는다. Stage 2의 승하차-역사 연결은 호선과 정규화 역명, alias 근거를 중심으로 설계한다.

### 3.7 shelter

- primary: `서울시 기후동행쉼터.csv`
- format: CSV
- encoding: `cp949`
- row count: 412
- columns: `순번`, `쉼터_구분`, `쉼터명`, `구이름`, `도로명주소`, `X좌표(EPSG:5186)`, `Y좌표(EPSG:5186)`, `운영시간`

좌표 컬럼명과 공식 설명은 EPSG:5186을 지시한다. 다만 Raw snapshot 자체의 기준시점은 확정하지 않으므로 412행을 2024년 당시 쉼터 현황이라고 단정하지 않는다. 핵심 가설 검증이 아니라 보조 공간 레이어로 사용한다.

## 4. 데이터 간 핵심 스키마 차이

1. senior에는 `호선`이 없고 total에는 존재한다.
2. senior와 total의 첫·마지막 시간대 label이 다르다.
3. 역번호를 데이터셋 간 직접 join key로 고정하지 않는다.
4. 공간 데이터의 좌표체계가 서로 다르므로 Stage 2에서 명시적으로 조화한다.
5. population은 binary Excel이 아니라 SpreadsheetML이며 `데이터` sheet 선택이 필요하다.

## 5. 출처 메타데이터 원칙

`subway/data_manifest.csv`에는 확인 가능한 데이터명, 제공기관, URL, 기준시점, 다운로드일, 라이선스만 기록한다. 확인되지 않은 값은 추정하지 않는다.

특히 다음은 과장하지 않는다.

- shelter 412행 snapshot의 기준시점
- 역사 위도·경도의 CRS를 Raw CSV만으로 확정하는 것
- 공식 페이지에서 확인하지 못한 이용조건을 추정하는 것

## 6. Stage 2로 넘기는 계약

Stage 2는 `subway/config/source_contracts_2024.yaml`을 source schema 기준으로 사용한다.

다음 작업은 Stage 2 범위다.

- 7개 데이터 clean schema 정의
- 승하차 wide → long 변환
- 시간대 label 정규화
- 역명·호선 canonicalization과 alias 관리
- senior/total 매칭과 non-senior 안전 생성
- ASOS 결측 의미 처리
- 행정동별 65세 이상 인구 집계
- CRS 조화와 Point-in-Polygon
- 기후동행쉼터 보조 공간 결합

EDA와 통계 분석은 그 이후 단계에서 수행한다.

## 7. 재현성

Raw 파일은 Git에 올리지 않고 원본을 수정하지 않는다. Stage 1은 inventory, schema snapshot, SHA-256, manifest와 source contract를 Git에 남겨 입력 snapshot을 식별한다.

검사 명령:

```powershell
python subway/tools/inspect_raw_inputs.py --year 2024
```

Stage 1 종료 전에는 위 명령을 두 번 실행하여 산출물 차이가 없는지 확인하고, 전체 unit test와 최종 inspection exit code를 다시 검증한다.
