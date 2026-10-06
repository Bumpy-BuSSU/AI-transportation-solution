# P-S2-2RC — Task 5 spatial source authority proposal (2026-10-07)

Task 5 remains **BLOCKED**. Retain the current authoritative configuration.
The exact KRIC **2024-12-31** export was **not obtained**. The candidate's
historical filename and SHA are therefore null, rather than a fabricated
2024 filename or the hash of a 2026 file. Task 6 and Task 8 remain COMPLETE;
Task 9/10/11 are **NOT STARTED**. No spatial layer or Task 9 output is created.

## Official-source acquisition and source quality

[Public Data Portal 15013205](https://www.data.go.kr/data/15013205/standard.do)
labels the dataset 국가철도공단_도시광역철도_역사정보_20241231, 1,073 rows.
Its official [KRIC id32 link](https://data.kric.go.kr/rips/M_01_01/detail.do?id=32)
currently supplies **전체_도시철도역사정보_20260630.xlsx**, 1,099 rows,
313,132 bytes, downloaded 2026-10-07 from
`https://data.kric.go.kr/rips/dataset/download.file?type=filedata&id=32&operation=1`.
SHA-256: `cdf1d84a7e5c898b2aacd622783ba8ba9af35c40bee0561dc97d55ce8e063f94`.
Provider: 국가철도공단 / 전국도시철도운영기관. Access: public official file,
no login; portal license is 이용허락범위 제한 없음. These exact bytes are retained
locally for audit, outside authoritative Raw and outside this Git commit.
Individual row reference dates remain separate from the export reference date.

The live detail page and alternate KRIC id1294 page expose current files and
no historical selector. The portal standard-page download manager and file
history JavaScript were read; their public standard-data/column/history
endpoints returned HTTP500, including a request with the actual detail UUID.
Multiple official-domain searches for 20231231/20241231 did not locate exact
historical id32 bytes. The KRIC coordinate complaint's attachment list is
empty; its upload control is not an old-file download. Thus acquisition
failure is an observed limitation of this audit, not proof that the provider
has no archive. No external request/message was sent to the provider.

The [official KRIC administrator reply dated 2025-04-15](https://data.kric.go.kr/rips/M_04_04/detail.do?id=79&page=4)
states that operator-supplied coordinates would be corrected and updated
after a report about swapped and misformatted coordinates in the 2024 file.
This adds a revision/provenance gate: even a future file bearing the 2024
label needs exact bytes, revision provenance and row-level quality checks.
Third-party GIS conversions or files declaring their own EPSG are not
accepted as the official 2024 original or official CRS evidence.

## Identity, code and coordinate evidence are separate

The current baseline remains 205 exact / 55 approved aliases / 14
ridership-only / 16 station-only, with 260/274 name-line matches and 21
line-6 code conflicts. All 60 alias rows, including the five senior aliases,
remain byte-identical. A source code is supporting lineage, never a global
station primary key, and no numeric offset or Raw code rewrite is applied.

`batch2rc_station_candidate_mapping.csv` covers every 274 Task 8 identity.
2024 candidate counts: exact0, reviewed0, unresolved274, ambiguous0,
verified coordinates0. Missing-coordinate and duplicate-candidate counts
are **unavailable**, since no historical dataset was acquired; unavailable
records must not be described as observed empty coordinates in a file.

The separately labelled **2026 support** uses line + exact name, the exact
approved line-scoped aliases, or explicit OA-22477 rename relations. It
requires the official operator and retains each official address and source
row number. Observed KRIC line mapping includes I4101→1 for Seoul Metro,
S1102/S1121/S1122→2 (the latter two are explicitly named 2호선 in the file),
I1103→3, I1104→4, S1105/6/7/8→5/6/7/8. Other operators/lines are excluded
from this support search. No stripping of parentheses or station-code-only
match is allowed. Exactly265 + reviewed-name5 =270 unique support matches,
ambiguous0, duplicate candidate identity groups0, missing coordinates on
those270 rows0. Four remain unresolved: line2 교대(법원.검찰청), line5 종로3가,
line5 하남시청(덕풍·신장), line8 남한산성입구(성남법원.검찰청). These figures
are not historical coverage or permission to adopt new mappings.

Every one of the21 line-6 conflicts has ridership/Seoul names, codes and
coordinates, empty explicitly unavailable KRIC2024 fields, and separately
dated 2026 operator/address/name/code/coordinates. All21 remain **unresolved**
for the requested 2024 physical-station verification. Current support
corroborates their name-line identities. Three differently sourced code
systems demonstrably cannot be treated as a universal equal-code key;
neither a universal conversion nor the cause of each discrepancy is proven.
Exact-name evidence does not automatically decide spatial eligibility.

## Every remaining 14 / 16 identity

`batch2rc_unmatched_identity_audit.csv` contains all30 individual records,
including each side of the12 line-6 display pairs. Official OA-22477 rows54/55
explicitly link 녹사평↔녹사평(용산구청) and 봉화산↔봉화산(서울의료원), dated
2013-12-26. These two name relationships are proposed for separate approval;
their incompatible codes and coordinate authority remain separate gates.
No alias is adopted in this Mission.

The other10 pairs — 고려대(종암), 광흥창(서강), 대흥(서강대앞),
상월곡(한국과학기술연구원), 새절(신사), 안암(고대병원앞), 월곡(동덕여대),
월드컵경기장(성산), 증산(명지대앞), 화랑대(서울여대입구) against the respective
bare Seoul names — still lack an independently accepted explicit relation
between those two source names. Several full names directly occur in the
current official KRIC file and support the ridership identity; that does not
automatically approve a bare-Seoul-name alias across incompatible codes.

The other four station-only identities are 까치산 line2 (approved transfer
counterpart of ridership line5), 충무로 line3 (counterpart of ridership line4),
신내 line6, 연신내 line6. They are outside the actual Task8 line-specific
identity set; no forced match or synthetic ridership row is created. For
신내, the [official 2019 opening notice](https://mediahub.seoul.go.kr/archives/1261413)
corroborates preexistence; it does not explain its omission from this Raw.

## 까치울 / 암사역사공원

Neither has an authenticated KRIC2024 row. Current support only:

| Task8 identity | KRIC2026 source code/line | Operator | Official address | Latitude | Longitude | Row reference |
|---|---|---|---|---|---|---|
| line7 /2753 /까치울 | 3753 /S1107 | 인천교통공사 | 경기도 부천시 원미구 길주로 지하 626 (춘의동) | 37.506236 | 126.81095 | 2022-04-30 |
| line8 /2810 /암사역사공원 | 0809 /S1108 | 서울교통공사 | 서울시 강동구 아리수로 27번길 2 | 37.557167 | 127.137556 | 2024-12-31 |

These are official **current-export support coordinates**, not adopted
authoritative 2024 coordinates. Exact name/line + provider/address supports
identity without equating the source codes. 까치울's14 wide rows are all zero;
its full-year coordinate temporal applicability remains unresolved.

[Official passenger service evidence](https://scpm.seoul.go.kr/seoul-policy/evt0064)
sets 암사역사공원 service start to **2024-08-10**. Proposed future rule:
date<2024-08-10 is excluded from operational spatial analysis; date>=that
date still requires accepted coordinates and source contract. Retain all
Raw and Task8 observations. Before opening,18 wide rows over9 dates contain
total261 across78 nonzero cells; these are not labelled test rides. The
opening event does not establish the cause of those observations.

## Coordinate comparison and Magok/Balsan

Requested Seoul↔KRIC2024 compared count is0; median/max differences are
null, not zero or PASS. The separately dated Seoul2025↔KRIC2026 diagnostic
compares256 safely name-related identities: exact188, different68. Median
absolute differences: latitude0 / longitude0 degrees; maximum: latitude
0.009077999999995257 / longitude0.07301563000000044 degrees. Outliers ranked
by maximum absolute component difference are 용답, 잠실새내, 마곡, 발산,
신답, 이촌(국립중앙박물관), 서울역, 디지털미디어시티, 명동, 시청. This ranking
is an angular diagnostic, not geodesic distance; no arbitrary tolerance
declares any coordinate PASS, and no difference is called a relocation.

Seoul assigns both 마곡/발산 37.562182,126.82693. KRIC2026 gives:

- 마곡 /0514 /S1105: 37.55865,126.837693; 공항대로 지하163(마곡동).
- 발산 /0515 /S1105: 37.558692,126.837633; 공항대로 지하267(마곡동).

These are numerically different by only latitude0.000042 /
longitude0.000060 degrees despite different station names and street
numbers. No independent entrance geometry or official corrected coordinates
were obtained to reconcile this near-coincidence. Thus the required KRIC2024
choice is **C: unresolved**, and the current support also cannot establish
independently plausible distinct locations. Keep the collision blocker and
both Raw sources untouched; don't substitute these nearly coincident points.

## CRS finding: outcome A, explicit WGS84 standard

The official [19th-revision notice (2024.10)](https://www.data.go.kr/bbs/rcr/selectRecsroom.do?originId=PDS_0000000001227&atchFileId=FILE_000000003049184)
provides `공공데이터 제공 표준(전문)_업로드.hwpx`,2,256,495 bytes.
SHA `d3d464f6a9dd9f6dfd3ff61fec966c95ccce8aec085c234ba3af9e665d3c67cd`.
Section42 도시철도역사정보, item10 역위도 and item11 역경도 explicitly
specify **WGS84**. Item10 defines the point as the center of exits managed
by the operator. The [20th-revision official attributes](https://www.data.go.kr/data/15156444/fileData.do)
independently reproduce the same dataset42/items10/11 definitions. Its
downloaded CSV SHA is
`b6092f441eb8e7b3a70deb6605e6770ac2fb2414a48f69f6b9a71f1e8c717d0a`.
The matching service/provider scope is 레일포털/국가철도공단; unrelated parking
or shelter coordinate definitions are not the evidence for this conclusion.

Proposed KRIC contract: geographic **WGS84**, decimal degrees,
longitude=x / latitude=y; GIS representation **EPSG:4326** is a proposed
identifier inferred from the explicitly named WGS84 datum, not an EPSG
number literally printed in the standard. No datum-assumption proposal is
needed (A, not B/C). This normative contract does not prove every provider
row conforms: numeric/order/format/entrance-point and discrepancy checks
are still required. No CRS is assigned and no configuration is replaced.
This result does not verify the existing Seoul coordinate source's CRS.

## Temporal audit

All274 identities are classified in `batch2rc_temporal_audit.csv`:
stable_preexisting0, opened_during_2024 **1** (암사역사공원),
renamed_during_2024_same_physical_station **4** (line4 당고개; line4/6 삼각지;
line7 자양(뚝섬한강공원)), coordinate_change_detected0, unresolved **269**.
These are event/available-evidence classifications, not approved annual
spatial eligibility. Formal rename dates come from OA-22477 (including
2024-10-31 병기 for the two 삼각지 line identities).

Official Seoul files labelled2023-10-31 and2024-10-31 have identical SHA
`9da58a78b07852906b9b9c75c539770d8a50a16c0cb5b8c21b23383327f85ce6`;
all276 coordinates also match the current Seoul source. They are **October**
snapshots, not year-end; the 2024-labelled file omits Amsa despite its August
opening. Consequently these corroborate snapshot equality only. They do
not satisfy the requested year-end comparison or prove continuous location
stability/no relocation. KRIC2023 and2024 year-end exports remain missing.

## Conditional adoption proposal — not ready for approval

| Contract field | Proposed rule / current gate |
|---|---|
| Candidate ID | public15013205 /KRIC32; future internal `station_kric_standard_2024` (proposal only) |
| Exact2024 Raw /SHA | not acquired /null; must authenticate bytes and correction revision before review |
| Provider /license | 국가철도공단 /전국도시철도운영기관; official portal terms and acquisition metadata pinned |
| Identity | canonical2024 total line+name; exact or explicit evidence-backed line-scoped relation; operator/address retained; ambiguous relations excluded |
| Codes | preserve all original codes as provenance; source-scoped, never sole join or numeric offset |
| Coordinate rule | valid numeric decimal coordinates, official point semantics, independent discrepancy review; unresolved/missing excluded explicitly with reasons |
| Temporal | compare genuine official2023/2024 snapshots, record event-specific dates; Amsa pre-service excluded; snapshot equality is corroboration only |
| CRS | official WGS84 standard; proposed EPSG4326 representation, x=longitude/y=latitude; validate each row, source-contract acceptance pending |
| Fallback | no silent Seoul fallback, year substitution, averaging or coordinate edit; explicit unresolved/exclusion list requires human acceptance |
| Seoul role if adopted | VALIDATION/SUPPLEMENTARY; historical coordinates and errors preserved; current authority remains unchanged now |
| Task5/9 impact | Task5 BLOCKED until all required station coverage/exclusions,21 conflicts,collision,temporal and contract gates accepted; Task9 NOT STARTED |

KRIC's explicit datum and broader current name coverage justify continued
investigation of an exact2024 primary candidate. They do not justify source
replacement with the currently downloaded file. Human approval of a new
station authority and mappings remains absent; no CRS assumption or Task9
approval is implied by this audit.

## Reproduction and frozen-state verification

The committed `subway/tools/generate_batch2rc_audit.py` produces the six JSON/CSV
diagnostics from hash-pinned local audit files and current frozen baseline,
using audit-only helpers. It refuses Raw as an output directory. Supply the
six files named in `PINNED` to an audit directory; the Seoul historical file
URLs use attachment IDs `FILE_000000002836485` (2023) and
`FILE_000000003064319` (2024), `fileDetailSn=1` at the official
`https://www.data.go.kr/cmm/cmm/fileDownload.do` endpoint. OA-22477 rename.csv
is the previously retained exact official export. A future changed download
must fail the pin, not silently refresh evidence. Exact public URLs and
SHA metadata for newly acquired evidence are retained in the candidate
summary/proposal. Re-run with two different temporary output directories
and compare all six SHA values. This Markdown proposal is a reviewed audit
document, not an automatically inferred authority decision.

Five meaningful audit-gate tests were observed RED (missing module), then
GREEN: row reference cannot backdate the export; exact bytes required;
name relations line-scoped; empty comparison unavailable; nonexact values
not a tolerance pass. Pipeline analysis code and semantic configurations
are unchanged. New audit reports have explicit LF attributes to preserve
their recorded hashes on Windows checkouts. Existing attribute lines are
preserved. See `04-station-spatial-authority-audit.md` for fresh full-suite,
Raw/preflight/Task8/Task4/7 and integrity results.
