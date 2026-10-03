Subway Data Preprocessing Design
- Date: 2026-10-03
- Project: AI Transportation Solution
- Scope: 2024 subway data preparation only
- Status: Design approved; implementation not started
Goal
Build a reproducible Python preprocessing pipeline that converts seven 2024 raw datasets into trustworthy analysis-ready inputs with explicit validation and provenance. This phase stops before EDA, visualization, statistical testing, regression, machine learning, or policy scoring.
Execution environment
- Primary: local Windows + Python
- Secondary: Google Colab compatible
- No absolute local paths
- Raw data remains local and is excluded from Git
- Target command: python subway/run_pipeline.py --year 2024
- Same structure must support later 2023 and 2025 expansion
Repository structure
AI-transportation-solution/
├─ subway/
│  ├─ data/
│  │  ├─ raw/
│  │  ├─ clean/
│  │  ├─ processed/
│  │  └─ validation/
│  ├─ src/
│  │  ├─ ingest/
│  │  ├─ clean/
│  │  ├─ transform/
│  │  ├─ validate/
│  │  └─ utils/
│  ├─ config/
│  ├─ notebooks/
│  ├─ logs/
│  ├─ data_manifest.csv
│  └─ run_pipeline.py
├─ bike/
├─ common/
├─ docs/
├─ requirements.txt
├─ .gitignore
└─ README.md
bike/ and common/ are reserved for later team integration. This phase implements only subway/.
Raw data policy
Expected layout:
subway/data/raw/2024/
├─ senior_ridership/
├─ total_ridership/
├─ weather/
├─ station/
├─ population/
├─ boundary/
└─ shelter/
Rules:
1. Keep downloaded filenames unchanged.
2. Never overwrite or manually edit raw files.
3. Exclude subway/data/raw/ from Git.
4. Record provenance and SHA-256 in the manifest.
5. Every manual mapping, exclusion, or correction must be explicit and auditable.
Manifest
subway/data_manifest.csv fields:
- dataset_id
- year
- dataset_name
- provider
- source_url
- raw_path
- reference_date
- download_date
- file_format
- sha256
- license
- notes
Unknown metadata must remain blank or marked unverified; never guessed.
Pipeline architecture
RAW
 ↓
Manifest + SHA-256
 ↓
INGEST
 ↓
CLEAN
 ↓
Clean Validation
 ↓
TRANSFORM
 ↓
Join / Business Validation
 ↓
Processed Data + Validation Reports
Ingest
Read raw sources without modifying them, normalize loading behavior, verify file presence and raw structure.
Clean
Standardize columns/types/dates, normalize station names, reshape hourly ridership wide→long, preserve raw identifiers, normalize spatial metadata, never silently repair suspicious values.
Transform
Combine senior/total ridership, derive non-senior and senior share, build station master, spatially map stations to administrative dongs, build dong population table.
Validate
Validate raw inputs, clean outputs, joins, and domain rules; produce machine-readable and human-readable QA; stop on ERROR.
Configuration
Use only three initial config sources:
1. datasets.yaml: paths, year, output paths, fixed source IDs such as ASOS 108.
2. station_aliases.csv: verified station-name exceptions only.
3. validation_rules.yaml: date coverage, expected days/stations, mandatory columns, negative-value rules.
Clean data contracts
Senior ridership
Output: senior_ridership_2024.parquet
Core fields: date, line, station_code_raw, station_name_raw, station_name, boarding_type, hour_start, hour_end, ridership.
Total ridership
Output: total_ridership_2024.parquet
Same schema as senior ridership; compatibility checks required.
Weather
Output: weather_2024.parquet
Expected: Seoul ASOS station 108, daily 2024 data. Keep temperature, precipitation, wind, humidity, and snow variables. Missing precipitation/snow must not automatically become zero until source semantics are verified.
Stations
Output: stations.parquet
Core fields: line, source station code, raw station name, canonical station name, latitude, longitude. Source station codes are not assumed to be a guaranteed cross-dataset primary key.
Population
Output: population_2024q2.parquet
Use 2024 Q2 to align with the 2024-06-30 boundary. Keep gu, dong, total population and 65+ age bands. Resolve duplicate dong names using gu + dong.
Administrative dong boundary
Output: dong_boundary_2024q2.parquet
Require valid geometry, administrative code/name, and verified CRS.
Climate shelters
Output: climate_shelters.parquet
Keep generated internal ID, type, name, district, address, coordinates, operating hours. Carry a warning until temporal reference is independently verified.
Processed outputs
ridership_2024.parquet
Fields: date, line, station, hour, boarding_type, senior, total, non_senior, senior_share.
Definitions:
- non_senior = total - senior
- senior_share = senior / total
  Rows where senior > total are recorded as exceptions, not silently corrected.
station_master.parquet
Fields: canonical_station_id, line, station_name, latitude, longitude, source_station_code.
station_dong_map.parquet
Fields: canonical_station_id, adm_cd, gu, dong. Generated through point-in-polygon after CRS normalization.
dong_population_2024q2.parquet
Fields: adm_cd, gu, dong, population_total, population_65_plus, senior_population_share.
Validation gates
Gate 0 — Raw integrity
Record file existence, filename, size, SHA-256, encoding/loadability, columns, row count, target year compatibility.
Gate 1 — Individual dataset quality
Check mandatory columns, expected types, valid dates, logical-key duplicates, negative values, mandatory nulls, coordinate validity, geometry validity.
Gate 2 — Cross-dataset consistency
Senior vs total: date overlap, station match rate, hourly structure match, senior <= total.
Ridership vs station master: direct matched / alias matched / unmatched. Never silently drop unmatched stations.
Station vs dong: ideally exactly one dong per station; zero or multiple matches become exceptions.
Gate 3 — Business rules
Check non-senior cannot be negative, aliases come only from explicit config, population components are internally consistent where applicable, and spatial outputs use a known CRS.
Severity model
ERROR
Stops pipeline. Examples: missing required file/columns, major date coverage failure, corrupt geometry, incompatible ridership schemas.
WARNING
Pipeline continues and records issue. Examples: isolated senior>total cells, alias-based matches, uncertain shelter reference date.
INFO
Expected/descriptive conditions. Examples: precipitation/snow missing values pending semantic interpretation, zero usage before effective station operation.
Validation outputs
Stored in subway/data/validation/:
- raw_inventory.csv
- data_quality_report.csv
- join_report.csv
- exceptions_ridership.csv
- exceptions_station.csv
- exceptions_spatial.csv
- pipeline_summary.json
Pipeline status:
- PIPELINE FAILED if any ERROR remains
- PIPELINE PASSED WITH WARNINGS if no ERROR but WARNINGs remain
- PIPELINE PASSED otherwise
Logs
Runtime logs: subway/logs/pipeline_2024_YYYYMMDD_HHMMSS.log.
Full logs may be ignored by Git; validation summaries remain versioned where appropriate.
Dependencies
Initial only:
- pandas
- pyarrow
- openpyxl
- geopandas
- shapely
- pyyaml
Do not add analysis libraries such as scikit-learn or statsmodels in this phase.
Definition of Done
The 2024 data-preparation phase is complete only when:
- raw files are preserved unchanged and excluded from Git
- manifest and SHA-256 provenance are recorded
- seven clean datasets are generated
- station canonicalization is complete and auditable
- senior/total consistency is validated
- non-senior ridership can be derived safely
- station coordinates are matched
- station-to-dong mapping is complete
- dong-level 65+ population is generated
- every exception is recorded
- remaining ERROR count is zero
- every WARNING has an explicit reason
- one command reproduces the 2024 pipeline
- same raw inputs reproduce the same processed outputs
Out of scope
No EDA, charts, correlation analysis, heatwave/cold-wave classification, statistical tests, regression, machine learning, policy scoring, or final report writing in this phase.
Design principles
1. Raw data is immutable.
2. Every transformation is explicit.
3. Every exception is traceable.
4. No suspicious value is silently repaired.
5. Preserve source identifiers where useful.
6. Source-specific exceptions live in config; reusable logic stays in code.
7. Same raw inputs and command must reproduce the same outputs.
8. The 2024 pipeline becomes the template for 2023–2025 expansion.
