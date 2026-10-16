from pathlib import Path
import unicodedata

import pandas as pd
import yaml

from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding

OUTPUT_COLUMNS = ['date', 'line', 'station_code_raw', 'station_name_raw', 'station_name',
                  'boarding_type', 'hour_bin', 'hour_start', 'hour_end', 'ridership',
                  'source_hour_column', 'ridership_raw', 'source_dataset_id', 'source_file',
                  'source_row_id', 'source_sequence_raw']


def load_ridership_rules(config_dir: Path) -> dict:
    rules = yaml.safe_load((config_dir / 'validation_rules.yaml').read_text(encoding='utf-8'))
    year = rules['year']
    contracts = yaml.safe_load((config_dir / f'source_contracts_{year}.yaml').read_text(encoding='utf-8'))
    if contracts['year'] != year:
        raise ValueError('source contract year mismatch')
    return dict(rules, source_contracts=contracts['contracts'])


def clean_ridership(frame: pd.DataFrame, dataset_id: str, year: int, rules: dict, source_file: str) -> StageResult:
    """Keep invalid/unmatched observations traceable; consumers must honor ERROR findings."""
    findings, exceptions = [], []
    raw = frame.copy(deep=True).reset_index(drop=True)
    raw['source_row_id'] = pd.Series(range(1, len(raw) + 1), dtype='Int64')
    raw['source_dataset_id'] = dataset_id
    raw['source_file'] = source_file

    def schema_failure(message):
        failed = raw.copy(); failed['exception_code'] = 'SOURCE_SCHEMA_DRIFT'
        return StageResult(pd.DataFrame(columns=OUTPUT_COLUMNS),
                           [Finding('ERROR', dataset_id, 'SOURCE_SCHEMA_DRIFT', message, source_file)], failed)

    if dataset_id not in {'senior_ridership', 'total_ridership'} or year != rules.get('year'):
        return schema_failure('unsupported dataset/year')
    try:
        contract = rules['source_contracts'][dataset_id]
        config = rules['ridership']
        if config['boarding_map'] != {'승차': 'boarding', '하차': 'alighting'} or config['line_map'] != {f'{n}호선': str(n) for n in range(1, 9)}:
            return schema_failure('unsupported boarding/line mapping')
        hour_map = config['time_bins'][dataset_id]
        if frame.columns.duplicated().any() or set(frame.columns) != set(contract['columns']):
            return schema_failure('source headers differ from authoritative contract')
        if len(hour_map) != 20 or not set(hour_map).issubset(frame.columns):
            return schema_failure('explicit 20-bin configuration mismatch')
        expected_bins = {'before_06': (None, 6), 'after_24': (24, None),
                         **{f'{h:02d}_{h+1:02d}': (h, h+1) for h in range(6, 24)}}
        configured_bins = {spec['hour_bin']: (spec['hour_start'], spec['hour_end']) for spec in hour_map.values()}
        if configured_bins != expected_bins:
            return schema_failure('noncanonical time bins or endpoint bounds')
    except (KeyError, TypeError) as exc:
        return schema_failure(f'missing required ridership configuration: {exc}')

    def report(code, mask, table, message):
        if mask.any():
            findings.append(Finding('ERROR', dataset_id, code, f'{message}: {int(mask.sum())}', source_file))
            bad = table.loc[mask].copy(); bad['exception_code'] = code
            exceptions.append(bad)

    for column in ['연번', '수송일자', '역번호', '역명', '승하차구분'] + (['호선'] if dataset_id == 'total_ridership' else []):
        missing = raw[column].isna() | raw[column].astype('string').str.strip().eq('').fillna(False)
        report('MANDATORY_NULL', missing, raw, column)

    date_strings = raw['수송일자'].astype('string')
    dates = pd.to_datetime(date_strings.where(date_strings.str.fullmatch(r'\d{4}-\d{2}-\d{2}', na=False)), format='%Y-%m-%d', errors='coerce')
    report('INVALID_DATE', dates.isna() | dates.dt.year.ne(year), raw, 'date')
    expected_dates = set(pd.date_range(f'{year}-01-01', f'{year}-12-31'))
    if set(dates.dropna()) != expected_dates:
        findings.append(Finding('ERROR', dataset_id, 'DATE_COVERAGE', 'global date coverage differs from requested year', source_file))
    raw['date'] = dates
    raw['station_code_raw'] = raw['역번호'].astype('string')
    raw['station_name_raw'] = raw['역명'].astype('string')
    raw['station_name'] = raw['station_name_raw'].map(lambda v: unicodedata.normalize('NFC', v).strip() if pd.notna(v) else pd.NA).astype('string')
    raw['source_sequence_raw'] = raw['연번'].astype('string')
    boarding = rules['ridership']['boarding_map']
    raw['boarding_type'] = raw['승하차구분'].map(boarding).astype('string')
    report('UNKNOWN_BOARDING', raw['boarding_type'].isna(), raw, 'boarding label')
    if dataset_id == 'total_ridership':
        raw['line'] = raw['호선'].map(rules['ridership']['line_map']).astype('string')
        report('UNKNOWN_LINE', raw['line'].isna(), raw, 'line label')
    else:
        raw['line'] = pd.Series(pd.NA, index=raw.index, dtype='string')

    keys = ['date', 'station_code_raw', 'station_name', 'boarding_type']
    if dataset_id == 'total_ridership': keys.append('line')
    report('LOGICAL_DUPLICATE', raw.duplicated(keys, keep=False), raw, 'duplicate wide logical key')
    ids = ['date', 'line', 'station_code_raw', 'station_name_raw', 'station_name', 'boarding_type',
           'source_dataset_id', 'source_file', 'source_row_id', 'source_sequence_raw']
    long = raw.melt(id_vars=ids, value_vars=list(hour_map), var_name='source_hour_column', value_name='ridership_raw')
    for col, key in [('hour_bin','hour_bin'), ('hour_start','hour_start'), ('hour_end','hour_end')]:
        mapping = {source: spec[key] for source, spec in hour_map.items()}
        long[col] = long['source_hour_column'].map(mapping)
    long['hour_start'] = long['hour_start'].astype('Int64')
    long['hour_end'] = long['hour_end'].astype('Int64')
    missing = long['ridership_raw'].isna() | long['ridership_raw'].astype('string').str.strip().eq('').fillna(False)
    numeric = pd.to_numeric(long['ridership_raw'], errors='coerce')
    invalid = (~missing) & (numeric.isna() | numeric.isin([float('inf'), float('-inf')]) | numeric.mod(1).ne(0) | numeric.ge(2**63) | numeric.lt(-(2**63)))
    report('MANDATORY_NULL', missing, long, 'ridership')
    report('INVALID_NUMERIC', invalid, long, 'ridership must be a finite int64 count')
    report('NEGATIVE_VALUE', numeric.lt(0), long, 'negative ridership')
    long['ridership'] = numeric.mask(invalid | missing).astype('Int64')
    long = long[OUTPUT_COLUMNS].reset_index(drop=True)
    exception_frame = pd.concat(exceptions, ignore_index=True, sort=False) if exceptions else pd.DataFrame(columns=OUTPUT_COLUMNS + ['exception_code'])
    return StageResult(long, findings, exception_frame)
