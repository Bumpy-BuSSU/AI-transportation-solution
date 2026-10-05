import json
import unicodedata

import pandas as pd

from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding

ALIAS_COLUMNS = ['dataset_id', 'line', 'station_name_raw', 'station_name', 'evidence', 'verified']
EXCEPTION_COLUMNS = ['exception_code', 'station_code_raw', 'station_name_raw', 'station_name',
                     'source_dataset_id', 'source_file', 'source_row_id', 'candidate_lines',
                     'candidate_names', 'evidence_status']


def normalize_station_name(name: str) -> str:
    return unicodedata.normalize('NFC', name).strip()


def _name(value):
    return normalize_station_name(str(value)) if pd.notna(value) else ''


def _aliases_for(frame: pd.DataFrame, dataset: str, aliases: pd.DataFrame):
    """Normalize only verified source-specific mappings; never assign a line from an alias."""
    out = frame.copy(deep=True)
    out['station_name'] = out['station_name_raw'].map(_name).astype('string')
    out['alias_applied'] = False
    out['alias_line_candidate'] = pd.Series(pd.NA, index=out.index, dtype='string')
    out['alias_evidence'] = ''
    out['alias_error'] = ''
    if set(ALIAS_COLUMNS) != set(aliases.columns):
        out['alias_error'] = 'ALIAS_CONFIGURATION_ERROR'
        return out
    verified = aliases['verified'].map(lambda v: str(v).strip().lower() == 'true').astype(bool)
    active = aliases[verified & aliases['dataset_id'].eq(dataset)].copy()
    active['station_name_raw'] = active['station_name_raw'].map(_name)
    for name, rows in active.groupby('station_name_raw', sort=True):
        mask = out['station_name'].eq(name)
        if dataset == 'total_ridership':
            # A total row already has a source line, so aliases are line-specific.
            for line in out.loc[mask, 'line'].dropna().unique():
                subset = rows[rows['line'].fillna('').astype(str).isin(['', str(line)])]
                _apply_alias(out, mask & out['line'].eq(line), subset)
        else:
            _apply_alias(out, mask, rows)
    return out


def _apply_alias(out, mask, rows):
    if rows.empty or not mask.any():
        return
    choices = rows[['line', 'station_name']].fillna('').drop_duplicates()
    if len(choices) != 1:
        out.loc[mask, 'alias_error'] = 'ALIAS_AMBIGUITY'
        return
    row = rows.iloc[0]
    if pd.isna(row['evidence']) or not str(row['evidence']).strip() or not _name(row['station_name']):
        out.loc[mask, 'alias_error'] = 'ALIAS_EVIDENCE_MISSING'
        return
    out.loc[mask, 'station_name'] = _name(row['station_name'])
    out.loc[mask, 'alias_applied'] = True
    if pd.notna(row['line']) and str(row['line']).strip():
        out.loc[mask, 'alias_line_candidate'] = str(row['line'])
    out.loc[mask, 'alias_evidence'] = str(row['evidence'])


def assign_station_ids(frame: pd.DataFrame) -> StageResult:
    out = frame.copy(deep=True)
    out['canonical_station_id'] = pd.Series(pd.NA, index=out.index, dtype='string')
    valid = out['line'].notna() & out['station_name'].notna() & out['line'].astype('string').str.strip().ne('') & out['station_name'].astype('string').str.strip().ne('')
    # Reversible JSON tuple encoding avoids separator/hash collisions and ignores raw codes.
    pairs = out.loc[valid, ['line', 'station_name']].drop_duplicates()
    ids = {(str(line), str(name)): 'station:' + json.dumps([str(line), str(name)], ensure_ascii=False, separators=(',', ':'))
           for line, name in pairs.itertuples(index=False, name=None)}
    if valid.any():
        out.loc[valid, 'canonical_station_id'] = [ids[(str(line), str(name))] for line, name in out.loc[valid, ['line', 'station_name']].itertuples(index=False, name=None)]
    bad = out.loc[~valid].copy()
    if not bad.empty: bad['exception_code'] = 'UNRESOLVED_STATION_ID'
    findings = [Finding('ERROR', 'station', 'UNRESOLVED_STATION_ID', f'{len(bad)} rows lack line/name')] if len(bad) else []
    return StageResult(out, findings, bad)


def build_senior_crosswalk(senior: pd.DataFrame, total: pd.DataFrame, aliases: pd.DataFrame) -> StageResult:
    """Assign only a unique code+canonical-name line. Return every senior observation.

    Identity labels are frozen to the 2024 total baseline. Reviewed historical
    variants enter through explicit aliases, never display-name heuristics.
    A rename date is evidence, not a reason to split a verified physical station
    identity; station_name_raw and source-row provenance remain unchanged.
    """
    left = _aliases_for(senior, 'senior_ridership', aliases).reset_index(drop=True)
    right = _aliases_for(total, 'total_ridership', aliases).reset_index(drop=True)
    left['station_code_raw'] = left['station_code_raw'].astype('string')
    right['station_code_raw'] = right['station_code_raw'].astype('string')
    left['line'] = pd.Series(pd.NA, index=left.index, dtype='string')
    left['crosswalk_status'] = 'unmatched'
    left['crosswalk_evidence'] = ''
    findings, exception_parts = [], []
    valid_right = right[right['alias_error'].eq('') & right['line'].notna() & right['line'].astype('string').str.strip().ne('') & right['station_code_raw'].notna() & right['station_code_raw'].str.strip().ne('') & right['station_name'].ne('')]
    candidates = {}
    for code, name, line in valid_right[['station_code_raw','station_name','line']].drop_duplicates().itertuples(index=False, name=None):
        candidates.setdefault((code, name), set()).add(str(line))
    multiple = sum(len(lines) > 1 for lines in candidates.values())
    if multiple:
        findings.append(Finding('ERROR', 'total_ridership', 'AMBIGUOUS_TOTAL_KEY', f'{multiple} code/name keys have multiple lines'))
    if right['alias_error'].ne('').any():
        findings.append(Finding('ERROR', 'total_ridership', 'ALIAS_CONFIGURATION_ERROR', 'total aliases contain invalid mappings'))

    grouped = left.groupby(['station_code_raw', 'station_name', 'alias_line_candidate', 'alias_error', 'alias_applied'], dropna=False, sort=False).groups
    for (code, name, alias_line, alias_error, applied), indexes in grouped.items():
        rows = list(indexes)
        valid_key = pd.notna(code) and bool(str(code).strip()) and pd.notna(name) and bool(str(name).strip())
        lines = candidates.get((code, name), set()) if valid_key else set()
        code_candidates = sorted((n, line) for (c, n), ls in candidates.items() if c == code for line in ls) if valid_key else []
        error = alias_error or ''
        if not error and len(lines) > 1: error = 'AMBIGUOUS_CROSSWALK'
        if not error and len(lines) == 1 and pd.notna(alias_line) and str(alias_line) not in lines:
            error = 'CODE_LINE_CONTRADICTION'
        if not error and len(lines) == 1:
            assigned = next(iter(lines))
            left.loc[rows, 'line'] = assigned
            # Total-side aliases also count as alias-backed evidence.
            total_alias = valid_right[(valid_right.station_code_raw == code) & (valid_right.station_name == name)]['alias_applied'].any()
            left.loc[rows, 'crosswalk_status'] = 'alias_matched' if applied or total_alias else 'exact_matched'
            left.loc[rows, 'crosswalk_evidence'] = 'verified alias + total unique code/name/line' if applied or total_alias else 'total unique code+canonical name -> line'
            continue
        error = error or 'UNRESOLVED_CROSSWALK'
        left.loc[rows, 'crosswalk_status'] = 'ambiguous_rejected' if error != 'UNRESOLVED_CROSSWALK' else 'unmatched'
        finding = Finding('ERROR', 'senior_ridership', error, f'{code}/{name}: {len(rows)} affected observations')
        findings.append(finding)
        bad = left.loc[rows].copy()
        bad['exception_code'] = error
        bad['candidate_lines'] = json.dumps(sorted({line for _, line in code_candidates}), ensure_ascii=False)
        bad['candidate_names'] = json.dumps(sorted({n for n, _ in code_candidates}), ensure_ascii=False)
        bad['evidence_status'] = 'missing; candidate only; no alias adopted' if error == 'UNRESOLVED_CROSSWALK' else 'rejected'
        exception_parts.append(bad.reindex(columns=EXCEPTION_COLUMNS))
    assigned = assign_station_ids(left)
    exception_frame = pd.concat(exception_parts, ignore_index=True) if exception_parts else pd.DataFrame(columns=EXCEPTION_COLUMNS)
    return StageResult(assigned.frame, findings, exception_frame)


def match_stations(ridership: pd.DataFrame, stations: pd.DataFrame, aliases: pd.DataFrame) -> StageResult:
    """Outer identity audit by line/name, preserving both unmatched sets.

    Codes can suggest candidates but never authorize a match. Station aliases
    are independently scoped, with verified evidence and optional source line.
    """
    right=stations.copy(deep=True).reset_index(drop=True)
    right['station_name']=right['station_name_raw'].map(_name)
    right['alias_applied']=False
    right['alias_evidence']=''
    findings=[]
    if set(aliases.columns)!=set(ALIAS_COLUMNS):
        findings.append(Finding('ERROR','station','ALIAS_CONFIGURATION_ERROR','alias headers differ'))
    else:
        active=aliases[aliases.dataset_id.eq('station') & aliases.verified.map(lambda v:str(v).strip().lower()=='true')]
        for (line,name),indexes in right.groupby(['line','station_name'],dropna=False).groups.items():
            rows=active[active.station_name_raw.map(_name).eq(name) & active.line.fillna('').astype(str).isin(['',str(line)])]
            if rows.empty:continue
            if rows.station_name.map(_name).nunique()!=1 or rows.evidence.fillna('').str.strip().eq('').any() or rows.station_name.map(_name).eq('').any():
                findings.append(Finding('ERROR','station','ALIAS_CONFIGURATION_ERROR',f'{line}/{name}: ambiguous or unsupported alias'))
                continue
            right.loc[list(indexes),'station_name']=_name(rows.iloc[0].station_name)
            right.loc[list(indexes),'alias_applied']=True
            right.loc[list(indexes),'alias_evidence']=rows.iloc[0].evidence
    left=ridership[['line','station_name','station_code_raw']].drop_duplicates().copy()
    if left.duplicated(['line','station_name']).any():
        findings.append(Finding('ERROR','station','RIDERSHIP_IDENTITY_CONFLICT','multiple raw codes per canonical identity'))
    if right.duplicated(['line','station_name']).any():
        findings.append(Finding('ERROR','station','STATION_IDENTITY_CONFLICT','multiple coordinate rows per canonical identity'))
        bad=right.copy();bad['exception_code']='STATION_IDENTITY_CONFLICT'
        return StageResult(right,findings,bad)
    valid_left=left.line.notna() & left.station_name.notna() & left.line.astype('string').str.strip().ne('') & left.station_name.astype('string').str.strip().ne('')
    valid_right=right.line.notna() & right.station_name.notna() & right.line.astype('string').str.strip().ne('') & right.station_name.astype('string').str.strip().ne('')
    merged=left.loc[valid_left].merge(right.loc[valid_right],on=['line','station_name'],how='outer',suffixes=('_ridership','_station'),indicator=True)
    merged['match_status']=merged['_merge'].astype('string').map({'left_only':'ridership_only','right_only':'station_only','both':'exact_matched'})
    merged.loc[merged['_merge'].eq('both') & merged.alias_applied.fillna(False),'match_status']='alias_matched'
    for invalid,status in [(left.loc[~valid_left],'ridership_only'),(right.loc[~valid_right],'station_only')]:
        if not invalid.empty:
            invalid=invalid.copy();invalid['match_status']=status
            merged=pd.concat([merged,invalid],ignore_index=True,sort=False)
    bad=merged[merged.match_status.isin(['ridership_only','station_only'])].copy()
    if len(bad):
        bad['exception_code']='UNRESOLVED_STATION_IDENTITY'
        findings.append(Finding('ERROR','station','UNRESOLVED_STATION_IDENTITY',f'{len(bad)} unmatched identities; no implicit aliases adopted'))
    return StageResult(merged.drop(columns=['_merge']),findings,bad)
