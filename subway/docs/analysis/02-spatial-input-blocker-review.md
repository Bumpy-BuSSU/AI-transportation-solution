# Stage 2 Batch 2R-A: spatial-input blocker evidence

Mission reference: **P-S2-2RA**, 2026-10-06, user attachment
`6359a14e-f2d2-4f57-9057-9bfe1de8e7eb`.
Starting branch `subway/preprocessing-pipeline`, HEAD
`91e107016f3cc8e73e8dc600de18ec5174d483c7`.

## Acceptance and scope

The human approved Batch 3 / Task 8 on **2026-10-06**. The research/AI log
records this decision separately from Codex tests. Inspection of the generation
path found that the previous local Batch 3 diagnostic driver generated
`human_batch3_acceptance=pending`. That technical summary is a historical
artifact; it is preserved byte-for-byte. The dated AI-log acceptance supersedes
its historical approval field. No human manual test rerun is claimed.
The adopted 2024 `senior_excess_policy` remains frozen and unchanged.
Task 8 acceptance does not authorize Task 9. **Tasks 9, 10 and 11 NOT STARTED.**

## Station identity evidence and proposal

Actual-source recomputation reproduced 276 coordinate rows and 274 ridership
identities: **205 exact / 69 ridership-only / 71 station-only**. There are
135 unmatched identities with 158 candidate relations: 146 adjunct, eight
code-supported name differences, four station suffix relations; five identities
have no candidate. These counts are measured, not defaults.

The official [OA-22477 rename file](https://data.seoul.go.kr/dataList/OA-22477/F/1/datasetView.do)
was downloaded: `서울교통공사_역명변경현황_20250313.csv`, 65 rows,
SHA-256 `fc1c285c6309c63c4c3f5b4928d47ec50fb3a2008c5e959d4c3a623fd68b6f52`.
Its license is 공공누리 제1유형. It separates actual name changes and 병기역명.
For example 당고개→불암산 is dated 2024-10-31; 뚝섬유원지→자양(뚝섬한강공원)
is dated 2024-02-29. 병기/display differences are not asserted as true renames.
An exact official relation and revision date, when available, are in the
proposed alias evidence. Punctuation variants that do not exactly equal the
official file are described as reviewed source variants.

**55 station aliases are proposed; zero adopted.** Each proposal has the
same provider family, same normalized line and external source code, exactly
one identity on both sides, no competing identity/code-line contradiction,
explicit raw→2024-total name relation and evidence; raw names are preserved.
The five senior aliases are unchanged. No generic parenthesis/suffix stripping
or fuzzy rule is added to the pipeline.

`batch2r_station_identity_resolution.csv` retains all 345 baseline audit rows,
candidate JSON, both codes, temporal limitation and proposed evidence. The 55
relationships appear on their two unmatched sides; **110 evidence rows mean
55 proposals**, not 110 aliases. A local simulation with only those explicit
proposals gives **205 exact / 55 alias / 14 ridership-only / 16 station-only**,
260/274 (94.8905%) name/line coverage. This is not authoritative acceptance.
Twenty-one existing exact name/line matches disagree on the external code,
all on line 6. They remain separately flagged. Of 260 simulated name matches,
239 have compatible external-code evidence; these numbers do not certify
coordinate accuracy or spatial eligibility.

Several line-6 source codes align with a different adjacent-name identity in
ridership. A unique code alone therefore does not prove a rename. Those
competing aliases remain unresolved. There is no Raw code correction.
Line-7 총신대입구↔이수 is a proposed source display relationship corroborated
by KRIC line S1107; OA-22477's line-4 rename is not used as line-7 evidence.

Automatic approval review rejected both attempts to apply the 55 aliases and
three reviewed transfer groups to authoritative config, requiring explicit
human reapproval. The concrete proposals were independently checked locally;
`station_aliases.csv` and `validation_rules.yaml` remain unchanged. Approval
is requested for these exact scoped changes, not an unrestricted normalization.

## Duplicate coordinates and five no-candidate identities

There are four groups / eight rows:

| Group | Evidence classification | Current severity | Proposed severity |
| --- | --- | --- | --- |
| 까치산, lines 2/5 | verified physical transfer | ERROR, 2 rows | INFO |
| 충무로, lines 3/4 | verified physical transfer | ERROR, 2 rows | INFO |
| 태릉입구, lines 6/7 | verified physical transfer | ERROR, 2 rows | INFO |
| 마곡 / 발산, both line 5 | unrelated identities, same coordinate | ERROR, 2 rows | ERROR |

[Official KRIC dataset 32](https://data.kric.go.kr/rips/M_01_01/detail.do?id=32)
provides transfer line and road-address evidence. Physical transfer evidence
does not close the separate line-6 source-code disagreement.
The current configuration has no adopted transfer exceptions, so **all eight
current ERROR rows remain**. The tested validator can apply a reviewed complete
member set if later approved; absent/unverified/blank evidence, extra rows,
same-identity duplicates and unrelated collisions remain ERROR.

- 2 / 200 까치산: no line-2 Task 8 identity; total Raw records it only under
  line 5 / 2519 (732 wide rows). Extra line-sensitive transfer coordinate,
  without forcing a ridership mapping. Intentional source aggregation is not
  asserted without provider documentation.
- 3 / 321 충무로: total Raw only line 4 / 423 (732 rows); same treatment.
- 6 / 2649 신내: no 2024 total Raw name 신내. Official Seoul evidence establishes
  its 2019 opening, but the source omission's cause remains unresolved.
  An unused coordinate identity does not itself block actual observations.
- 7 / 2753 까치울: 14 actual total wide rows, all retained. The official KRIC
  candidate has name 까치울, line 도시철도 7호선, provider 인천교통공사,
  lat 37.506236 / lon 126.81095, source code 3753, row reference 2022-04-30.
  The different code namespace is retained; no code-only join or substitution.
- 8 / 2810 암사역사공원: 306 actual total wide rows. Official KRIC candidate
  S1108, source code 0809, lat 37.557167 / lon 127.137556, reference 2024-12-31.
  [Official service started 2024-08-10](https://scpm.seoul.go.kr/seoul-policy/evt0064).
  Raw contains 18 pre-opening rows on nine dates, total 261 and 78 nonzero
  cells. These remain source observations; they are not labeled test rides.

The KRIC download is `전체_도시철도역사정보_20260630.xlsx`, 1099 rows, acquired
2026-10-06, SHA-256
`cdf1d84a7e5c898b2aacd622783ba8ba9af35c40bee0561dc97d55ce8e063f94`.
The public-data landing metadata still labels an older 20241231 file; the
actual downloaded file label and individual row dates are kept separately.
[Dataset 15013205](https://www.data.go.kr/data/15013205/standard.do) states
이용허락범위 제한 없음. Coordinates are lawful official audit evidence, but
adding them requires a source contract and CRS/temporal review. None adopted.

## CRS and temporal contracts

**All four Task 5 components remain BLOCKED:** identity (remaining unresolved
and code contradictions; safe aliases awaiting approval), coordinate coverage
(missing current-source coordinates plus unresolved collisions), temporal and CRS.

For [same-source dataset 15099316](https://www.data.go.kr/data/15099316/fileData.do),
the current metadata, downloaded column-definition XLSX and public OAS including
historical schemas contain no explicit WGS84/EPSG:4326 statement. Provider
documentation search found no same-source explicit CRS. Column/range/convention
and alternative-source CRS do not establish this source's CRS. Contract stays null.
Column file SHA-256:
`ac4123a00bd89acd99db656360473bddb10518181797777cf206305ff10128cf`.
[OAS definition](https://infuser.odcloud.kr/oas/docs?namespace=15099316/v1) SHA-256:
`8063c2d57be8c3cac37a5ff69a9e83649cd0d39f6ca637e38e1911915244bd9b`.

Same-source official versions 2023-10-31 and 2024-10-31 were actually acquired.
Both are byte-identical, SHA-256
`9da58a78b07852906b9b9c75c539770d8a50a16c0cb5b8c21b23383327f85ce6`.
All 276 line/code pairs have equal numeric coordinates to the 2025 snapshot.
This corroborates historical published snapshots. It does not establish
freshness or unchanging full-year locations: even the October-2024 file omits
the August-2024 opening. The row-level temporal category remains unresolved
for all full-period applications, except the separately documented 2024 opening
event for 암사역사공원. No location-change event was established; absence of
such evidence is not proof. Current reference stays 2025-08-14; writing date
is never treated as opening date.

## Population candidate viability

Official [DT_201004_O020003](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_O020003&conn_path=I2)
was acquired without interactive-download failure. Export title is **등록인구**,
in 주민등록인구(동별) context; provider 서울특별시 / 서울특별시기본통계.
Explicit period **2024 2/4**, quarterly end **2024-06-30**.
Official export filename `등록인구_20261006115823.csv`, local audit filename
`DT_201004_O020003_2024Q2_20261006.csv`, downloaded 2026-10-06,
UTF-8 BOM. SHA-256:
`e48f83ca75f7f92a5a83e39834440c0f3149ace1113c3533102797e4d0338d76`.
Metadata SHA-256:
`d84b715b3f0a903d45a4b5efa74838390b6f103a65141bb581b49618839e5073`.
Public export requires no login; no separate license text appears in the export
or its table metadata. Provider and source must be attributed.

The export has one Seoul total, 25 gu and **426 dongs**, unique gu+dong keys.
Official hierarchical codes retain gu parents, disambiguating the two 신사동.
All 426 keys equal the verified 2024 boundary hierarchy after only the existing
seven explicit typography relations. Both required measures are numeric for
all dongs: **zero missing among 852 required cells**. Statistical symbols are
not coerced. The 26 existing incomplete dongs now have direct candidate values.
All-dong candidate totals are 9,619,861 residents / 1,785,286 aged 65+.

| Compared measure, existing complete 400 dongs | Exact | Mismatch | Max absolute difference | Difference distribution |
| --- | ---: | ---: | ---: | --- |
| candidate 계 vs existing total | 400 | 0 | 0 | 0: 400 |
| direct 65세이상고령자 vs existing eight-band sum | 400 | 0 | 0 | 0: 400 |

There are no mismatch examples. No averaging, reconciliation, zero fill or
imputation occurred. Official metadata states quarter-end observations and
**65세이상 고령자 수: 외국인 포함**. The export supplies 계 and 한국인 as
different fields; the matched denominator is 계. The identical overlap
supports compatibility for this period, without claiming all future tables or
years have identical semantics. **Candidate viability PASS; authoritative Task
6 remains BLOCKED pending human source-contract approval.**

## Explicit population source-adoption proposal — NOT implemented

1. Add dataset ID `population_direct_65_plus`; retain current `population` as
   independent validation/supplementary age-band evidence, not the primary clean
   population calculation after approved migration.
2. Proposed Raw path:
   `subway/data/raw/2024/population_direct_65_plus/201_DT_201004_O020003_2024Q2_20261006.csv`.
   Preserve downloaded bytes, filename provenance, SHA and official metadata.
   The audit candidate is outside Raw and is not committed as authoritative Raw.
3. Add one manifest record with provider, table ID, official URL, period,
   UTF-8 BOM encoding, CSV type, download date, license/access information and
   checksum; keep the current population manifest record unchanged.
4. Add an exact source contract for the approved export layout, hierarchical
   region codes and names, selected `계` and direct `65세이상고령자`, 명 unit,
   2024Q2 and required-missing/severity rules. Do not sum the eight age bands
   for the new primary output; no statistical-symbol coercion.
5. Keep clean output fields gu, dong, adm_cd, population_total,
   population_65_plus, senior_population_share, reference_period and per-source
   provenance. Ratio only if total>0. Keep raw labels, official region codes,
   items, units and input filename/checksum provenance.
6. Verify exact 25-gu / 426-dong hierarchy and boundary equality with only
   approved explicit typography aliases. Preserve current 400/26 diagnostics
   as historical validation and compare the 400 overlaps independently.
7. Migration tests: exact input schema/quarter/items, invalid/missing symbols,
   parent-key validation (both 신사동), duplicates/orphans, boundary equality,
   400 exact cross-validation, direct aggregate computation, ratio denominator
   and repeat artifact hashes. Existing age-source tests remain evidence tests.
8. Stage 1 impact: append a new source/provenance entry, Raw inventory and
   schema snapshot through a separately approved baseline extension. Existing
   eleven Raw hashes stay immutable. Do not label new source as an original
   seven-source baseline. Stage 2 dependency/plan must explicitly accept the
   additional source before changing Task 6's primary contract.

**STOP before authoritative replacement. Human approval required.** Neither
this proposal nor passing tests authorizes Task 9.

## Reproduction and validation

Non-authoritative downloaded files, requests and audit driver are preserved in
the calling chat workspace `_batch2ra`; the five checked-in diagnostics have
relative source paths and no execution timestamp. Each CSV uses unique sorted
keys; summaries use sorted JSON keys. All five hashes matched after regeneration.

Official acquisition recipe:

- OA-22477 file form: POST `https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false`,
  fields infId=OA-22477, infSeq=2, seq=1, seqNo blank.
- Same-source 2024 coordinate CSV: `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003064319&fileDetailSn=1&insertDataPrcus=N`;
  2023 file ID `FILE_000000002836485`. Historical metadata/IDs came from
  `/tcs/dss/selectHistAndCsvData.do` and `/tcs/dss/selectDpkDetailInfo.do`.
- KRIC: `https://data.kric.go.kr/rips/dataset/download.file?type=filedata&id=32&operation=1`.
- Population: official table, select 2024 2/4 only, all Seoul/gu/dong levels,
  계 and 65세이상고령자 (additional household/Korean/sex fields retained in
  audit), code inclusion, statistical symbols ON, original precision, CSV.
  Preserve official code parents rather than plain forward filling. Web form
  uses orgId=201, tblId=DT_201004_O020003, quarter `Q,202402,@`, ITM_ID=T001;
  geography OV_L1_ID, measure OV_L2_ID (002=계, 006=65+). Official form requests
  `/statHtml/downGrid.do` then `/statHtml/downNormal.do`; metadata from
  `/statHtml/downMeta.do`, viewSubKind=2_META. Request JSON is locally preserved.

Executed verification:

- `python -m unittest discover -s subway/tests -v`: baseline 80 PASS;
  two new behavior tests failed before fixes; full post-change **83 PASS**.
- Actual Task 8 regeneration: 3,988,480 integrated; 3,987,960 matched;
  520 total-only; zero senior-only/ambiguous; three excess;
  non_senior 3,987,957; senior_share 3,968,169; matched 0/0 19,788.
  All three regenerated Batch 3 file SHAs equal the tracked baseline exactly.
- Task 4 and Task 7 actual regenerated summaries equal Batch 2 baselines.
- Existing eleven Raw SHAs were individually recomputed and equal baseline.
- Existing five senior aliases, QA policy, CRS metadata and source contracts
  unchanged; no Task 9/10/11 implementation or spatial joining.

Closeout checks freshly executed: Raw inspection twice, exit 0, seven datasets /
eleven files, ERROR=0 / WARNING=0 / INFO=0. `git diff --exit-code` on the five
Stage 1 generated files returned 0; `git diff --check` returned 0. The independent
read-only review identified null/NaN/false/zero transfer evidence acceptance;
RED tests reproduced it and the validator now requires nonblank string evidence.
The full 83 tests passed again after that fix. Exact-match fallback from a
rejected alias was reviewed: independent raw name/line evidence remains an
exact audit match, but its explicit alias-code ERROR remains blocking; this is
not spatial acceptance. The reviewer did not require a future Task 9 feature.
Commit/push SHAs and final working-tree/remote agreement are reported in the
Mission closeout message, avoiding a self-referential commit hash in this file.
