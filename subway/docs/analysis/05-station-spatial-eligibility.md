# P-S2-2RD — Task5 spatial eligibility closure

Starting HEAD: `7923c0c24cd4150bfa995c364d259c00a14a0bc0`.
Branch:`subway/preprocessing-pipeline`;approved2026-10-07.
Task5 **COMPLETE** under **eligibility_based_with_documented_exclusions**.
Completion means spatial-analysis eligibility contract finalized, not all
station source problems resolved. Task6/8 COMPLETE; **Task9/10/11 NOT STARTED**.

## Contract and authority boundaries

The existing adopted station source,55 station aliases,5 senior aliases,
three exact approved physical-transfer groups and QA policy remain unchanged.
All274 actual Task8 identities receive exactly one status. The16 station-only
source identities are evidence only and outside the denominator. A new
[analytical policy](../../config/spatial_eligibility_2024.yaml) records the
human's assumptions separately from unchanged source metadata/contracts.

[Eligibility table](../../data/validation/task5_spatial_eligibility.csv) preserves
both source codes, Raw source names/row/file, coordinates, identity status,
code-conflict flag, spatial status/reason, CRS/temporal status and evidence.
[Exclusion-only audit](../../data/validation/task5_spatial_exclusions.csv)
supports review of every excluded station. [Summary](../../data/validation/task5_spatial_eligibility_summary.json)
contains complete status/reason accounting, exact denominators, residual
limits, input/config/output hashes and actual regression evidence.

Only ELIGIBLE /ELIGIBLE_CODE_WARNING enter the separate future spatial subset.
`spatial_subset(core,eligibility)` returns a new frame and never replaces core.
The actual subset was checked but not published as a Task9 output. No geometry,
CRS transformation, Point-in-Polygon, dong mapping or shelter proximity is run.

## Measured eligibility and loss

| Status | Station identities | Integrated rows | Matched rows | Total-only rows | Total(all) | Total(matched) | Senior(all) |
|---|---:|---:|---:|---:|---:|---:|---:|
|ELIGIBLE|237|3469680|3469680|0|3045946574|3045946574|427337965|
|ELIGIBLE_CODE_WARNING|21|307440|307440|0|147948363|147948363|19106930|
|EXCLUDED_COORDINATE|4|35680|35160|520|26486440|26486303|3391265|
|EXCLUDED_IDENTITY|12|175680|175680|0|82367083|82367083|13145793|
|EXCLUDED_TEMPORAL|0|0|0|0|0|0|0|

Denominators: {"integrated_rows": 3988480, "matched_rows": 3987960, "senior_ridership_all_observations": 462981953, "senior_ridership_matched_observations": 462981953, "station_identities": 274, "total_only_rows": 520, "total_ridership_all_observations": 3302748460, "total_ridership_matched_observations": 3302748323}

Excluded shares: excluded_senior_ridership_matched_share=3.571858%, excluded_senior_ridership_share=3.571858%, excluded_station_identity_share=5.839416%, excluded_total_ridership_matched_share=3.295843%, excluded_total_ridership_share=3.295847%.

All-observation totals include the520 total-only cells (sum137); matched total
denominator is separate. There are no senior-only/ambiguous rows. Senior(all)
equals senior(matched) here, not by general assumption. Three matched
senior-excess cells remain in the original accounting with null derived
comparison values; they are not deleted or repaired for these sums.

Exclusion reasons:12 unadopted line6 display-name mappings;2 no accepted
coordinates (까치울/암사역사공원);2 unresolved coordinate collisions
(마곡/발산). No unreviewed alias, KRIC coordinate substitution, code offset,
manual coordinate correction or synthetic identity is added.

The21 line6 exact adopted canonical-name/line mappings have one coordinate
row and no unresolved coordinate collision, plus unique audited current KRIC
name/line/operator/address support. They remain ELIGIBLE_CODE_WARNING with
both incompatible codes and the conflict flag preserved. For 삼각지, current
KRIC's 삼각지(전쟁기념관) is supported by the already audited official OA-22477
row53; corroboration is not adoption of a new Seoul coordinate alias. Current
KRIC is a2026 support file, not historical2024 spatial authority. Existing
approved physical-transfer coincidences do not count as unresolved collisions.

## CRS and temporal assumptions — not source verification

All rows record EPSG4326, longitude=x/latitude=y and
**ANALYTICAL_ASSUMPTION**. The official national2024 station-data standard
explicitly says WGS84; the existing Seoul file has no source-specific datum
declaration. Its raw station_crs remains null. Evidence and exact document
SHA/URL are in the approved policy and prior [2RC audit](04-station-spatial-authority-audit.md).

Mapped pre-existing stations use **SNAPSHOT_STABILITY_ASSUMPTION**:
the2023-10-31,2024-10-31,2025-08-14 labelled snapshots corroborate identical
coordinates for276 existing source rows; residual temporal uncertainty
remains. This is not proof coordinates were continuously unchanged in2024.
Unmapped identities have no accepted-coordinate applicability; Amsa explicitly
records KNOWN_2024_OPENING/2024-08-10 and is excluded for missing accepted
coordinates. Pre-opening core observations remain without test-ride claims.
If a future accepted mapping has a2024 opening, the generic contract excludes
full-year eligibility rather than pretending snapshot stability; any date-
specific eligibility change requires a separate Mission.

## Report-ready confirmed findings / interpretation / limitations

승하차 자료와 역사 위치자료의 역명·외부역코드·좌표를 대조한 결과 일부
자료 간 불일치가 확인되었다. 승인된55개 이름 관계는 명시적 매핑으로
적용하고,21개 코드 불일치는 관측값을 보존한 경고로 관리하였다. 승인된
위치 매핑이 없거나 좌표 충돌이 미해결인16개 역은 core 승하차 분석에
보존하되 공간분석 대상에서 제외하도록 자격 계약을 확정하였다. 제외
사유와 이용량 비중은 별도 검증자료로 관리한다.

이는 공공자료의 상호운용성·메타정보 한계로 해석하며, 모든 제공기관
오류가 확정됐다는 주장이 아니다. 향후 공간 결과는274개 역 전체를
대표하지 않을 수 있다. 제외 비중이 작다는 이유로 기준을 조정하거나
PASS threshold를 설정하지 않았다. CRS·snapshot 가정과 exclusion
선택이 후속 공간 결과에 미칠 영향은 최종보고서 한계로 유지한다.

## TDD and fresh verification

- Baseline108 tests PASS. New eligibility13 tests initially RED (missing
  module), then GREEN. Actual diagnostic exposed overstrict KRIC display-name
  corroboration for 삼각지; an additional test was observed FAIL, then GREEN.
  Final full suite: **122/122 PASS**.
- `python -m unittest discover -s subway/tests -v`:122 PASS.
- `python subway/tools/inspect_raw_inputs.py --year 2024`:exit0,8 datasets /
  12 files,ERROR/WARNING/INFO all0; original inspection outputs Git-identical.
- `preflight(repo,2024)`:empty findings. All12 Raw SHA values unchanged;
  direct population SHA e48f83ca75f7f92a5a83e39834440c0f3149ace1113c3533102797e4d0338d76.
- Actual Task8 regenerated accounting:3,988,480 integrated;3,987,960 matched;
  520 total-only;0 senior-only/ambiguous;3,987,957 valid non-senior;
  3,968,169 valid share;19,788 zero/zero;all counts/sums and exception/join
  CSV hashes equal the accepted baseline. No core deletion.
- Actual Task4/7 summaries equal accepted baseline; Task6 inputs/config/
  accepted426-dong output/400-dong comparison hashes unchanged.
- All existing authority configs, manifest and historical validation files
  remain byte-identical to starting HEAD. Existing source APIs stay intact.
- Eligibility/exclusion CSV and summary written twice with reversed rows:
  all output hashes equal. Explicit stable keys line/name/canonical ID;
  same recorded Python/pandas/library environment.

These are Codex's automated checks, not independent human manual reruns.
Historical diagnostics retain the statuses they reported at their creation;
this closure and the new summary provide the current Task5 status.

## Artifact SHA-256

- `task5_spatial_eligibility.csv`: `d5fa6b5843d1be0ea399d27abe3f6c7dfa9414a91f7bd6deb25b7b03c759b080`
- `task5_spatial_eligibility_summary.json`: `6bdcd7d659dcaef82dd9b369fe2c9874850ebc5f575a814292e02272c9577fcc`
- `task5_spatial_exclusions.csv`: `7e42d7a3dd6a985fb3493f58edb858239a9a0240b97c8a44572dbc1899dbc12b`
