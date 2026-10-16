"""Validate spatial inputs without geometry repair or historical inference."""
import pandas as pd
import geopandas as gpd
from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding


def clean_boundary(frame,rules,source_file):
    out=frame.copy(deep=True).reset_index(drop=True)
    out['source_row_id']=range(1,len(out)+1);out['source_file']=source_file;out['source_dataset_id']='boundary'
    findings,parts=[],[]
    def report(code,mask,message,severity='ERROR'):
        if mask.any():
            findings.append(Finding(severity,'boundary',code,f'{message}: {int(mask.sum())}',source_file))
            if severity=='ERROR':
                bad=out.loc[mask].copy();bad['exception_code']=code;parts.append(bad)
    all_rows=pd.Series(True,index=out.index)
    contract=rules['source_contracts']['boundary']
    if set(frame.columns)!=set(contract['columns']) or frame.columns.duplicated().any():
        report('SOURCE_SCHEMA_DRIFT',all_rows,'headers differ from contract')
        return StageResult(out,findings,pd.concat(parts,ignore_index=True) if parts else pd.DataFrame())
    out['admin_name_raw']=out.ADM_NM;out['dong']=out.ADM_NM;out['adm_cd']=out.ADM_CD.astype('string');out['base_date']=out.BASE_DATE
    out['gu']=pd.Series(pd.NA,index=out.index,dtype='string')
    if frame.crs is None or frame.crs.to_epsg()!=5179:
        report('CRS_CONTRACT',all_rows,'explicit EPSG:5179 required')
    if len(out)!=contract['row_count']:
        findings.append(Finding('ERROR','boundary','ROW_COUNT','426 boundary rows required',source_file))
        bad=out.copy();bad['exception_code']='ROW_COUNT';parts.append(bad)
    report('BASE_DATE_CONTRACT',out.base_date.astype('string').ne('20240630').fillna(True),'2024-06-30 baseline required')
    report('INVALID_ADMIN_CODE',~out.adm_cd.str.fullmatch(r'11\d{6}',na=False),'SGIS Seoul 8-digit code')
    report('DUPLICATE_ADMIN_CODE',out.adm_cd.duplicated(keep=False),'ADM_CD must be unique')
    report('NULL_GEOMETRY',out.geometry.isna(),'geometry missing')
    report('EMPTY_GEOMETRY',out.geometry.is_empty,'geometry empty')
    report('INVALID_GEOMETRY',~out.geometry.isna() & ~out.geometry.is_valid,'geometry invalid; no repair')
    report('GEOMETRY_TYPE',~out.geometry.isna() & ~out.geometry.geom_type.isin(contract['geometry_types']),'geometry type')
    # Verified Task 6 hierarchy may supply an explicit ADM_CD -> gu/dong map.
    hierarchy=rules.get('boundary_hierarchy')
    if hierarchy is None:
        report('GU_UNVERIFIED',all_rows,'ADM_NM contains dong only; no gu inferred without verified hierarchy','WARNING')
    else:
        h=hierarchy[hierarchy.level.eq('dong')]
        if h.adm_cd.duplicated().any() or h.evidence.fillna('').str.strip().eq('').any():
            report('HIERARCHY_UNVERIFIED',all_rows,'hierarchy conflicts or lacks evidence')
        else:
            mapping=h.set_index('adm_cd')
            out['gu']=out.adm_cd.map(mapping.gu).astype('string')
            names=out.adm_cd.map(mapping.dong)
            report('HIERARCHY_MISMATCH',out.gu.isna() | names.ne(out.dong),'verified population/boundary name mismatch')
    return StageResult(out,findings,pd.concat(parts,ignore_index=True) if parts else pd.DataFrame())


def clean_shelters(frame,rules,source_file):
    out=frame.copy(deep=True).reset_index(drop=True)
    out['source_row_id']=range(1,len(out)+1);out['source_file']=source_file;out['source_dataset_id']='shelter'
    findings,parts=[],[]
    def report(code,mask,message):
        if mask.any():
            findings.append(Finding('ERROR','shelter',code,f'{message}: {int(mask.sum())}',source_file))
            bad=out.loc[mask].copy();bad['exception_code']=code;parts.append(bad)
    if frame.columns.duplicated().any() or set(frame.columns)!=set(rules['source_contracts']['shelter']['columns']):
        bad=out.copy();bad['exception_code']='SOURCE_SCHEMA_DRIFT'
        return StageResult(out,[Finding('ERROR','shelter','SOURCE_SCHEMA_DRIFT','explicit EPSG:5186 coordinate headers required',source_file)],bad)
    sequence=out['순번'].astype('string')
    report('INVALID_SHELTER_ID',~sequence.str.fullmatch(r'\d+',na=False),'source sequence must be numeric')
    out['shelter_id']='shelter:'+sequence
    report('DUPLICATE_SHELTER_ID',out.shelter_id.duplicated(keep=False),'source sequence duplicate')
    valid=pd.Series(True,index=out.index)
    for source,target in [('X좌표(EPSG:5186)','x'),('Y좌표(EPSG:5186)','y')]:
        out[target]=pd.to_numeric(out[source],errors='coerce').astype('Float64')
        bad=out[target].isna() | out[target].isin([float('inf'),float('-inf')])
        report('INVALID_COORDINATE',bad,source);valid &= ~bad
    geometry=gpd.GeoSeries([None]*len(out),index=out.index,crs=5186)
    geometry.loc[valid]=gpd.points_from_xy(out.loc[valid,'x'],out.loc[valid,'y'],crs=5186)
    out=gpd.GeoDataFrame(out,geometry=geometry,crs=5186)
    out['reference_date']=pd.NA;out['temporal_applicability']='snapshot reference date and 2024 applicability unresolved'
    findings.append(Finding('WARNING','shelter','TEMPORAL_UNCERTAINTY','downloaded rows do not establish a 2024 shelter census',source_file))
    return StageResult(out,findings,pd.concat(parts,ignore_index=True) if parts else pd.DataFrame())
