"""Direct official population aggregates; boundary attributes corroborate identity.

No geometry join, CRS conversion, age-band filling or source reconciliation.
The old age-band cleaner remains a separate validation/supplementary source.
"""
import re

import pandas as pd

from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding

DATASET = 'population_direct_65_plus'
PROVENANCE = ['source_row_id', 'source_sha256', 'reference_period', 'reference_date', 'unit']


def _integer(value):
    # Parse integer digits directly: never coerce symbols/booleans through float.
    if isinstance(value, bool) or pd.isna(value) or not re.fullmatch(r'\d+', str(value)):
        return None
    number = int(str(value))
    return number if number < 2**63 else None


def clean_direct_population(frame, boundary, rules, source_file):
    raw = frame.copy(deep=True).reset_index(drop=True)
    contract = rules['source_contracts'][DATASET]
    findings, parts = [], []

    def error(code, message, table=raw):
        findings.append(Finding('ERROR', DATASET, code, message, source_file))
        bad = table.copy()
        bad['exception_code'] = code
        parts.append(bad)

    def result(out=None):
        return StageResult(pd.DataFrame() if out is None else out, findings,
                           pd.concat(parts, ignore_index=True, sort=False) if parts else pd.DataFrame())

    if frame.columns.duplicated().any() or set(frame.columns) != set(contract['columns'] + PROVENANCE):
        error('SOURCE_SCHEMA_DRIFT', 'exact source fields and provenance required')
        return result()
    if (len(raw) != contract['row_count'] or raw.source_row_id.isna().any()
            or raw.source_row_id.duplicated().any()):
        error('SOURCE_ROW_CONTRACT', 'complete unique source rows required')
        return result()
    for column in ['source_sha256', 'reference_period', 'reference_date', 'unit']:
        expected = contract['sha256'] if column == 'source_sha256' else contract[column]
        invalid = raw[column].ne(expected).fillna(True)
        if invalid.any():
            error('SOURCE_PROVENANCE_CONTRACT', column, raw.loc[invalid])
    if findings:
        return result()

    geography = raw[contract['geography_column']].astype('string').str.extract(r'^(\d{3}(?:\d{3}){0,2}) (.+)$')
    if geography.isna().any().any():
        error('HIERARCHY_CONTRACT', 'explicit 3/6/9-digit geography codes and labels required')
        return result()
    raw['source_code'], raw['source_label'] = geography[0], geography[1]
    if raw.source_code.duplicated().any():
        error('HIERARCHY_CONTRACT', 'source geography code duplicate')
        return result()
    city = raw[raw.source_code.str.len().eq(3)]
    gu = raw[raw.source_code.str.len().eq(6)]
    dong = raw[raw.source_code.str.len().eq(9)].copy()
    if (len(city) != 1 or city.iloc[0].source_code != '001' or city.iloc[0].source_label != '합계'
            or len(gu) != contract['expected_gu'] or gu.source_label.duplicated().any()
            or set(gu.source_label) != set(rules['population']['gu_names'])
            or not gu.source_code.str.startswith('001').all()):
        error('HIERARCHY_CONTRACT', 'one Seoul parent and exact official gu set required')
        return result()
    dong['source_gu_code'] = dong.source_code.str[:6]
    dong['gu'] = dong.source_gu_code.map(gu.set_index('source_code').source_label)
    dong['dong'] = dong.source_label.replace(rules['population'].get('boundary_name_aliases', {}))
    if (len(dong) != contract['expected_dong'] or dong.gu.isna().any()
            or dong.duplicated(['gu', 'dong']).any() or dong.gu.nunique() != contract['expected_gu']):
        error('HIERARCHY_CONTRACT', 'complete unique gu/dong parent keys required')
        return result()

    if not {'ADM_CD', 'ADM_NM', 'BASE_DATE'}.issubset(boundary):
        error('BOUNDARY_KEY_CONTRACT', '2024 Q2 boundary attributes required')
        return result()
    b = boundary[['ADM_CD', 'ADM_NM', 'BASE_DATE']].copy()
    codes = b.ADM_CD.astype('string')
    if (len(b) != contract['expected_dong'] or codes.duplicated().any()
            or not codes.str.fullmatch(r'11\d{6}', na=False).all()
            or not b.BASE_DATE.astype('string').eq('20240630').all()):
        error('BOUNDARY_KEY_CONTRACT', 'unique complete Q2 SGIS keys required')
        return result()
    b['prefix'] = codes.str[:5]
    parents = {key: set(group.ADM_NM) for key, group in b.groupby('prefix')}
    gu_prefixes = {}
    for name, group in dong.groupby('gu'):
        hits = [key for key, names in parents.items() if names == set(group.dong)]
        if len(hits) != 1:
            error('BOUNDARY_KEY_CONTRACT', f'{name}: exact complete parent membership not corroborated')
            return result()
        gu_prefixes[name] = hits[0]
    if len(set(gu_prefixes.values())) != len(parents):
        error('BOUNDARY_KEY_CONTRACT', 'parent membership must be bijective')
        return result()
    lookup = {(row.prefix, row.ADM_NM): str(row.ADM_CD) for row in b.itertuples()}
    if len(lookup) != len(b):
        error('BOUNDARY_KEY_CONTRACT', 'duplicate parent/name boundary key')
        return result()
    dong['adm_cd'] = [lookup[(gu_prefixes[g], d)] for g, d in zip(dong.gu, dong.dong)]

    records = []
    for _, row in dong.iterrows():
        total, senior = _integer(row[contract['total_column']]), _integer(row[contract['senior_column']])
        if total is None or senior is None:
            error('INVALID_DIRECT_POPULATION', f'{row.gu}/{row.dong}: nonnegative integer people required', raw.loc[[row.name]])
            continue
        valid_share = total > 0 and senior <= total
        if senior > total:
            error('SENIOR_EXCEEDS_TOTAL', f'{row.gu}/{row.dong}', raw.loc[[row.name]])
        if total == 0:
            findings.append(Finding('WARNING', DATASET, 'ZERO_TOTAL', f'{row.gu}/{row.dong}: share null', source_file))
        records.append(dict(gu=row.gu, dong=row.dong, adm_cd=row.adm_cd, population_total=total,
                            population_65_plus=senior, senior_population_share=senior/total if valid_share else None,
                            reference_period=row.reference_period, reference_date=row.reference_date,
                            source_dataset_id=DATASET, source_file=source_file, source_row_id=row.source_row_id,
                            source_sha256=row.source_sha256, source_table=contract['table_id'], source_url=contract['source_url'],
                            source_code=row.source_code, source_gu_code=row.source_gu_code, dong_name_raw=row.source_label,
                            source_total_item=contract['total_column'], source_senior_item=contract['senior_column'], unit=row.unit,
                            hierarchy_evidence='official source code parents + exact complete Q2 boundary parent/name-set bijection; SGIS codes not equated to statistics codes'))
    out = pd.DataFrame(records)
    if len(out) != contract['expected_dong']:
        error('HIERARCHY_COVERAGE', 'required direct dong population values incomplete')
    return result(out)


def compare_population_sources(primary, supplementary, *, expected_overlap=400):
    """Compare independently cleaned values; any mismatch blocks acceptance."""
    required = ['adm_cd', 'gu', 'dong', 'population_total', 'population_65_plus']
    errors = []

    def error(message):
        errors.append(Finding('ERROR', DATASET, 'POPULATION_CROSS_VALIDATION', message))

    for frame in [primary, supplementary]:
        if not set(required).issubset(frame):
            error('required comparison fields absent')
            return StageResult(pd.DataFrame(), errors, frame.copy())
        if (frame[required].isna().any().any() or frame.adm_cd.duplicated().any()
                or frame.duplicated(['gu', 'dong']).any()):
            error('comparison keys/values missing or duplicated')
            return StageResult(pd.DataFrame(), errors, frame.copy())
        for column in ['population_total', 'population_65_plus']:
            if frame[column].map(_integer).isna().any():
                error('comparison requires exact nonnegative integer values')
                return StageResult(pd.DataFrame(), errors, frame.copy())
    comparison = supplementary[required].merge(primary[required], on='adm_cd', how='left',
                                               suffixes=('_supplementary', '_primary'), validate='one_to_one')
    if len(comparison) != expected_overlap or comparison.isna().any().any():
        error('required overlap/key coverage differs')
    mismatch = pd.Series(False, index=comparison.index)
    for key in ['gu', 'dong']:
        mismatch |= comparison[key+'_supplementary'].ne(comparison[key+'_primary']).fillna(True)
    for measure in ['population_total', 'population_65_plus']:
        # Object integer arithmetic avoids float conversion of exact values.
        left = comparison[measure+'_primary'].map(lambda v: _integer(v))
        right = comparison[measure+'_supplementary'].map(lambda v: _integer(v))
        comparison[measure+'_difference'] = left - right
        mismatch |= comparison[measure+'_difference'].ne(0).fillna(True)
    if mismatch.any():
        error('independent source identity/value mismatch; no reconciliation permitted')
    exceptions = comparison.copy() if errors else pd.DataFrame()
    if errors:
        exceptions['exception_code'] = 'POPULATION_CROSS_VALIDATION'
    return StageResult(comparison, errors, exceptions)
