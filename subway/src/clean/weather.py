"""Daily ASOS values; blank observations remain missing."""
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding

WEATHER_COLUMNS = dict(zip(
    ['평균기온(°C)', '최저기온(°C)', '최고기온(°C)', '일강수량(mm)',
     '최대 풍속(m/s)', '평균 풍속(m/s)', '평균 상대습도(%)', '일 최심신적설(cm)', '일 최심적설(cm)'],
    ['temperature_mean', 'temperature_min', 'temperature_max', 'precipitation',
     'wind_max', 'wind_mean', 'humidity_mean', 'snow_new_max', 'snow_depth_max']))


def clean_weather(frame, year, rules, source_file):
    out = frame.copy(deep=True).reset_index(drop=True)
    out['source_row_id'] = range(1, len(out)+1)
    out['source_file'] = source_file
    out['source_dataset_id'] = 'weather'
    findings, parts = [], []
    def report(code, mask, message, severity='ERROR'):
        if mask.any():
            findings.append(Finding(severity, 'weather', code, f'{message}: {int(mask.sum())}', source_file))
            if severity == 'ERROR':
                bad = out.loc[mask].copy(); bad['exception_code'] = code; parts.append(bad)
    expected = rules['source_contracts']['weather']['columns']
    if out.columns[:len(frame.columns)].duplicated().any() or set(frame.columns) != set(expected) or year != rules['year']:
        bad = out.copy(); bad['exception_code'] = 'SOURCE_SCHEMA_DRIFT'
        return StageResult(out, [Finding('ERROR','weather','SOURCE_SCHEMA_DRIFT','headers/year differ from contract',source_file)], bad)
    out['station_id'] = out['지점'].astype('string')
    report('UNKNOWN_STATION', out.station_id.ne(str(rules['weather']['station_id'])).fillna(True), 'station ID')
    text = out['일시'].astype('string')
    out['date'] = pd.to_datetime(text.where(text.str.fullmatch(r'\d{4}-\d{2}-\d{2}',na=False)),format='%Y-%m-%d',errors='coerce')
    report('INVALID_DATE',out.date.isna() | out.date.dt.year.ne(year),'date')
    report('DUPLICATE_DATE',out.date.duplicated(keep=False),'duplicate date')
    if set(out.date.dropna()) != set(pd.date_range(f'{year}-01-01',f'{year}-12-31')):
        findings.append(Finding('ERROR','weather','DATE_COVERAGE','full requested year is required',source_file))
    for source, target in WEATHER_COLUMNS.items():
        values = out[source].astype('string')
        blank = values.isna() | values.str.strip().eq('').fillna(False)
        numeric = pd.to_numeric(values,errors='coerce')
        invalid = ~blank & (numeric.isna() | numeric.isin([float('inf'),float('-inf')]))
        report('INVALID_NUMERIC',invalid,source)
        report('MANDATORY_NULL' if target.startswith('temperature_') else 'OBSERVATION_MISSING',blank,source,
               'ERROR' if target.startswith('temperature_') else 'WARNING')
        out[target] = numeric.mask(blank | invalid).astype('Float64')
    return StageResult(out,findings,pd.concat(parts,ignore_index=True) if parts else pd.DataFrame())
