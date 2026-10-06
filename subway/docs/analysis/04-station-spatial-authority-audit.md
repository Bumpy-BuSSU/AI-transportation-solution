# P-S2-2RC — Station spatial authority audit

Starting HEAD: `054b5d09754801413789377909ec7f45cf278ca8`.
Branch: `subway/preprocessing-pipeline`. Audit date:2026-10-07.

Exact KRIC2024 and2023 historical exports were not obtained. The portal2024
metadata link returns a2026 XLSX; it is retained locally as separately dated
support, never adopted as2024 Raw. The official2024 standard explicitly
states WGS84 for the station latitude/longitude attributes (outcome A).
Historical acquisition, row quality, identity/temporal and accepted source
contract gates remain open; **Task5 BLOCKED**. Task6/8 COMPLETE;
**Task9/10/11 NOT STARTED**.

The [complete source proposal](../../data/validation/batch2rc_spatial_source_proposal.md)
records exact acquisition URLs/SHA/license,274 identities,21 line6 conflicts,
14/16 remaining identities, specific missing stations, coordinate outliers,
CRS scope, temporal classifications and a conditional adoption contract.
It expressly retains the existing authority configuration. All historical
KRIC fields are null/unavailable;2026 support fields are independently named.

## Verification executed by Codex

| Command/check | Fresh result |
|---|---|
| `python -m unittest discover -s subway/tests -v` | 107 tests PASS (102 original +5 audit gates) |
| `python subway/tools/inspect_raw_inputs.py --year 2024` (twice) | both exit0;8 datasets /12 files;ERROR/WARNING/INFO all0 |
| `git diff --exit-code -- subway/data_manifest.csv subway/data/validation/raw_inventory.csv subway/data/validation/raw_schema_snapshot.json subway/data/validation/raw_inspection_report.csv subway/data/validation/raw_inspection_summary.json` | exit0 after repeated inspection |
| `preflight(repo,2024)` | empty findings |
| Exact Raw SHA /direct-population index bytes |12 files unchanged; direct SHA e48f83ca75f7f92a5a83e39834440c0f3149ace1113c3533102797e4d0338d76 |
| Frozen55 files | existing configs, manifest and validation artifacts byte-identical to starting HEAD; existing source modules have identical Git clean-filter blobs (normal Windows CRLF checkout preserved) |
| Fresh station cleaning/matching |276 rows;205 exact /55 aliases /14 ridership-only /16 station-only;21 code conflicts; regenerated2RB CSV SHA identical |
| Senior aliases | five original rows +header SHA c3181cf850c8f69f5a26dca4bc27cf4f1c30b76eb67c7ff65f947dee2fd5aa98 |
| Actual Task8/Task4/7 regression | Task8 accounting and exception/join CSV SHA equal; weather/boundary/shelter summaries equal accepted baseline |
| `python -m subway.tools.generate_batch2rc_audit --audit-dir <audit-files> --output-dir <temporary-dir>` | six JSON/CSV files independently regenerated;all SHA equal |

Task8 re-computation: integrated3,988,480;matched3,987,960;total-only520;
senior-only0;ambiguous0;valid non-senior3,987,957;valid share3,968,169;
zero/zero19,788;three senior-excess cells preserved. Total input sum
3,302,748,460 (matched3,302,748,323 +total-only137), senior462,981,953.
Task4 remains366 days/station108; Task7 remains426 boundary geometries
EPSG5179 and412 shelter points EPSG5186. Task6's accepted426-dong output,
400-dong comparison and all primary/supplementary contracts are unchanged.

Audit-gate tests were first run and failed with the missing audit module,
then all5 passed. Audit support code is separate from unchanged analysis
modules and never assigns a source or CRS. No Raw or semantic config changes
are made. Seven narrowly scoped LF attributes protect new deterministic
report bytes at checkout; all existing attributes remain in place.

The local audit directory contains the exact downloaded candidates and
standard documents as requested. It is outside Raw/Git. The reproducible
generator requires the six pinned input files, including prior exact official
Seoul snapshots and rename export, and fails on changed download hashes.
The diagnostic script used to re-execute actual Task8/4/7 writes only scratch
files; its historical carry-forward status metadata is not used to infer
current Task6 status. Current Task6 status is asserted from the accepted2RB
authority summary plus unchanged exact inputs/config/output hashes.

## Audit artifact SHA-256

- `batch2rc_coordinate_comparison.csv`: `3ab771137bcd43023fa2a4edf2d6558c88029769a8a20dfbce09fe1064e8c948`
- `batch2rc_kric_candidate_summary.json`: `b91f39c13b62c625e0c48c4fe09241d261d645defa9d25607551cfe1a337d4a4`
- `batch2rc_line6_code_audit.csv`: `4e3d3b1358c5124259f9a9168303bb0ff05ee3cd81a79e8646f22d9cdad00879`
- `batch2rc_spatial_source_proposal.md`: `77f221b7fa47c85bbcfedfcfc93a0cc27437e5d16574e60e1c11a2d22be6c3df`
- `batch2rc_station_candidate_mapping.csv`: `d4dc9f56b8ae49838a73929fddcc93aead3e481960990c2d7eea7761aabbd694`
- `batch2rc_temporal_audit.csv`: `e3a925bf245ea9e553919b698f0ddac13aab42f8366761790f62783841d62058`
- `batch2rc_unmatched_identity_audit.csv`: `32b0b726c9bd5a5513dd824557969f550a3c48021d3504c33cf63aaea72afeff`

## Rulings and limits

- Historical file unavailable: keep all2024 spatial fields unavailable and
  treat2026 only as support. Cost if historical bytes actually exist elsewhere:
  another acquisition/review is required; no unsupported2024 adoption occurs.
- October source equality does not meet a year-end/continuous-observation gate:
  stable_preexisting remains0; only four official rename events and one opening
  event are classified. Cost: conservative unresolved counts remain higher.
- Exact WGS84 standard scope applies to KRIC station attributes, not automatically
  to the Seoul file or individual row correctness. Cost: row/contract review
  remains necessary despite the resolved normative datum question.
- Retain acquired local audit bytes after review to satisfy the Mission's exact
  byte preservation requirement; remove no other Mission's workspace.

## Scoped changed files

- `subway/.gitattributes`
- `subway/docs/analysis/00-report-map.md`
- `subway/docs/analysis/ai-usage-log.md`
- `subway/docs/analysis/04-station-spatial-authority-audit.md`
- `subway/tools/audit_station_candidate.py`
- `subway/tools/generate_batch2rc_audit.py`
- `subway/tests/test_station_candidate_audit.py`
- `subway/data/validation/batch2rc_coordinate_comparison.csv`
- `subway/data/validation/batch2rc_kric_candidate_summary.json`
- `subway/data/validation/batch2rc_line6_code_audit.csv`
- `subway/data/validation/batch2rc_spatial_source_proposal.md`
- `subway/data/validation/batch2rc_station_candidate_mapping.csv`
- `subway/data/validation/batch2rc_temporal_audit.csv`
- `subway/data/validation/batch2rc_unmatched_identity_audit.csv`
