"""Clean numeric station coordinates without inferring a CRS or historical validity."""
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding
from subway.src.transform.station_keys import normalize_station_name


def clean_stations(frame, rules, source_file):
    out=frame.copy(deep=True).reset_index(drop=True)
    out['source_row_id']=range(1,len(out)+1)
    out['source_file']=source_file
    out['source_dataset_id']='station'
    findings,parts=[],[]
    def report(code,mask,message):
        if mask.any():
            findings.append(Finding('ERROR','station',code,f'{message}: {int(mask.sum())}',source_file))
            bad=out.loc[mask].copy();bad['exception_code']=code;parts.append(bad)
    if frame.columns.duplicated().any() or set(frame.columns)!=set(rules['source_contracts']['station']['columns']):
        bad=out.copy();bad['exception_code']='SOURCE_SCHEMA_DRIFT'
        return StageResult(out,[Finding('ERROR','station','SOURCE_SCHEMA_DRIFT','headers differ from contract',source_file)],bad)
    out['line']=out['호선'].astype('string')
    out['station_name_raw']=out['역명'].astype('string')
    out['station_name']=out.station_name_raw.map(lambda x:normalize_station_name(x) if pd.notna(x) else '').astype('string')
    out['station_code_raw']=out['고유역번호(외부역코드)'].astype('string')
    out['reference_date_raw']=out['작성기준일']
    out['writing_date_raw']=out['작성일자']
    out['station_crs']=pd.Series(pd.NA,index=out.index,dtype='string')
    out['temporal_applicability']='unresolved for 2024; writing date is not an opening date'
    report('UNKNOWN_LINE',~out.line.isin([str(n) for n in range(1,9)]),'line')
    report('MANDATORY_NULL',out.station_name.eq('') | out.station_code_raw.isna() | out.station_code_raw.str.strip().eq(''),'identity')
    for source,target,lo,hi in [('위도','latitude',-90,90),('경도','longitude',-180,180)]:
        out[target]=pd.to_numeric(out[source],errors='coerce').astype('Float64')
        report('INVALID_COORDINATE',out[target].isna() | ~out[target].between(lo,hi).fillna(False),source)
    for source in ['작성일자','작성기준일']:
        text=out[source].astype('string')
        parsed=pd.to_datetime(text.where(text.str.fullmatch(r'\d{4}-\d{2}-\d{2}',na=False)),format='%Y-%m-%d',errors='coerce')
        report('INVALID_SOURCE_DATE',parsed.isna(),source)
    report('DUPLICATE_IDENTITY',out.duplicated(['line','station_name'],keep=False),'line/name duplicate or conflicting coordinates')
    report('DUPLICATE_COORDINATE',out.duplicated(['latitude','longitude'],keep=False),'duplicate coordinate pair; review source identities')
    findings.extend([Finding('WARNING','station','CRS_UNVERIFIED','source does not explicitly establish coordinate CRS; Task 9 blocked',source_file),
                     Finding('WARNING','station','TEMPORAL_UNCERTAINTY','coordinate reference snapshot is not proven applicable to 2024',source_file)])
    return StageResult(out,findings,pd.concat(parts,ignore_index=True) if parts else pd.DataFrame())
