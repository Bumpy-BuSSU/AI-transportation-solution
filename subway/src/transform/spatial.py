"""Strict Task9 spatial preprocessing; never repair points or polygons."""
import numpy as np
import pandas as pd
import geopandas as gpd
from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding
from subway.src.transform.spatial_eligibility import ELIGIBLE_STATUSES, _validate_eligibility

MAPPING_STATUSES=('MAPPED','BOUNDARY_POINT','ZERO_MATCH','MULTIPLE_MATCH')
COMPLETION_MODE='strict_point_in_polygon_with_documented_exceptions'
MASTER_FIELDS=('canonical_station_id','line','station_name','station_code_raw_ridership',
    'spatial_status','exclusion_reason','latitude','longitude','crs','crs_status','temporal_status',
    'source_code_conflict','station_coordinate_source','evidence')
POPULATION_FIELDS=('population_total','population_65_plus','senior_population_share')


def _failure(frame,code,message):
    bad=frame.copy(deep=True);bad['exception_code']=code;bad['exception_reason']=message
    return StageResult(pd.DataFrame(),[Finding('ERROR','task9',code,message)],bad)


def build_station_master(eligibility: pd.DataFrame) -> StageResult:
    """Preserve all authoritative Task5 identities, statuses and provenance."""
    if eligibility.columns.duplicated().any() or not set(MASTER_FIELDS).issubset(eligibility):
        return _failure(eligibility,'STATION_MASTER_SCHEMA','Task5 master fields required')
    try:_validate_eligibility(eligibility)
    except ValueError as exc:return _failure(eligibility,'STATION_IDENTITY_CONTRACT',str(exc))
    if eligibility.canonical_station_id.astype(str).str.strip().eq('').any():
        return _failure(eligibility,'STATION_IDENTITY_CONTRACT','blank canonical identity')
    out=eligibility.copy(deep=True).sort_values('canonical_station_id',kind='stable').reset_index(drop=True)
    return StageResult(out,[],pd.DataFrame())


def _boundary_error(boundary,contract=None):
    if contract is None:
        from pathlib import Path
        import yaml
        contract=yaml.safe_load((Path(__file__).resolve().parents[2]/'config/study_area_2024.yaml').read_text(encoding='utf-8'))['boundary_contract']
    if not isinstance(contract,dict) or not {'row_count','crs','code_pattern','base_date'}.issubset(contract):
        return 'BOUNDARY_CONTRACT','explicit boundary profile contract required'
    required={'ADM_CD','ADM_NM','BASE_DATE','geometry'}
    if not isinstance(boundary,gpd.GeoDataFrame) or boundary.columns.duplicated().any() or not required.issubset(boundary):
        return 'BOUNDARY_SCHEMA','Q2 boundary fields and GeoDataFrame required'
    if boundary.crs is None or boundary.crs.to_string()!=contract['crs']:return 'BOUNDARY_CRS','explicit configured boundary CRS required'
    if len(boundary)!=contract['row_count']:return 'BOUNDARY_COUNT','configured administrative-dong count required'
    codes=boundary.ADM_CD.astype('string')
    if codes.duplicated().any() or not codes.str.fullmatch(contract['code_pattern'],na=False).all():
        return 'BOUNDARY_KEYS','unique configured ADM_CD required'
    if not boundary.BASE_DATE.astype('string').eq(str(contract['base_date'])).fillna(False).all():return 'BOUNDARY_DATE','configured boundary date required'
    if (boundary.geometry.isna().any() or boundary.geometry.is_empty.any()
            or not boundary.geometry.is_valid.all() or not boundary.geometry.geom_type.isin(['Polygon','MultiPolygon']).all()):
        return 'BOUNDARY_GEOMETRY','nonnull nonempty valid polygons required; no repair'
    return None


def map_stations_to_dongs(stations: pd.DataFrame, boundary: gpd.GeoDataFrame, *, boundary_contract=None) -> StageResult:
    master=build_station_master(stations)
    if master.findings:return master
    out=master.frame[master.frame.spatial_status.isin(ELIGIBLE_STATUSES)].copy().reset_index(drop=True)
    for field in ['ADM_CD','gu','dong','boundary_base_date',f'x_{boundary.crs.to_epsg() if boundary.crs else 5179}',f'y_{boundary.crs.to_epsg() if boundary.crs else 5179}']:
        out[field]=pd.NA
    out['mapping_status']='ERROR';out['candidate_ADM_CD']='';out['mapping_reason']='';out['mapping_evidence']=''
    error=_boundary_error(boundary,boundary_contract)
    if error:
        failed=_failure(boundary,*error)
        out['mapping_reason']=error[0];out['mapping_evidence']=error[1]
        failed.frame=out
        return failed
    findings=[];parts=[]
    lat=pd.to_numeric(out.latitude,errors='coerce');lon=pd.to_numeric(out.longitude,errors='coerce')
    finite=pd.Series(np.isfinite(lat.to_numpy(dtype=float,na_value=np.nan)) & np.isfinite(lon.to_numpy(dtype=float,na_value=np.nan)),index=out.index)
    booleans=out.latitude.map(lambda v:isinstance(v,(bool,np.bool_))) | out.longitude.map(lambda v:isinstance(v,(bool,np.bool_)))
    valid=finite & lat.between(-90,90).fillna(False) & lon.between(-180,180).fillna(False) & ~booleans
    policy=out.crs.eq('EPSG:4326').fillna(False) & out.crs_status.eq('ANALYTICAL_ASSUMPTION').fillna(False)
    for mask,code,message in [(~valid,'INVALID_STATION_COORDINATE','finite numeric geographic longitude/latitude required'),
                              (~policy,'STATION_CRS_POLICY','EPSG:4326 ANALYTICAL_ASSUMPTION required')]:
        if mask.any():
            findings.append(Finding('ERROR','task9',code,f'{message}: {int(mask.sum())}'))
            out.loc[mask,'mapping_reason']=code;out.loc[mask,'mapping_evidence']=message
    accepted=valid & policy
    points=gpd.GeoSeries(gpd.points_from_xy(lon.loc[accepted],lat.loc[accepted]),index=out.index[accepted],crs=4326).to_crs(boundary.crs)
    polygons=boundary.sort_values('ADM_CD',kind='stable')
    for index,point in points.items():
        out.loc[index,[f'x_{boundary.crs.to_epsg() if boundary.crs else 5179}',f'y_{boundary.crs.to_epsg() if boundary.crs else 5179}']]=[point.x,point.y]
        within=polygons[polygons.geometry.contains(point)]
        candidates=within
        if len(within)==1:status='MAPPED';reason='UNIQUE_STRICT_WITHIN'
        elif len(within)>1:status='MULTIPLE_MATCH';reason='MULTIPLE_STRICT_WITHIN'
        else:
            candidates=polygons[polygons.geometry.touches(point)]
            status='BOUNDARY_POINT' if len(candidates) else 'ZERO_MATCH'
            reason='TOUCHES_POLYGON_BOUNDARY' if len(candidates) else 'NO_STRICT_WITHIN_OR_TOUCH'
        out.loc[index,['mapping_status','mapping_reason','candidate_ADM_CD','mapping_evidence']]=[
            status,reason,'|'.join(candidates.ADM_CD.astype(str)),
            f'longitude=x latitude=y; EPSG:4326 analytical assumption -> {boundary.crs.to_string()}; strict contains; non-within touches checked; no repair/fallback']
        if status=='MAPPED':
            row=within.iloc[0]
            out.loc[index,['ADM_CD','gu','dong','boundary_base_date']]=[str(row.ADM_CD),row.get('gu',pd.NA),row.ADM_NM,str(row.BASE_DATE)]
    for field in [f'x_{boundary.crs.to_epsg() if boundary.crs else 5179}',f'y_{boundary.crs.to_epsg() if boundary.crs else 5179}']:out[field]=pd.to_numeric(out[field],errors='coerce').astype('Float64')
    exceptions=out[out.mapping_status.ne('MAPPED')].copy()
    exceptions['exception_code']=exceptions.mapping_status
    for status in MAPPING_STATUSES[1:]:
        count=int(out.mapping_status.eq(status).sum())
        if count:findings.append(Finding('WARNING','task9',status,f'{count} explicit mapping exceptions; no correction'))
    return StageResult(out,findings,exceptions)


def map_population_to_boundary(population: pd.DataFrame,boundary: gpd.GeoDataFrame, *, boundary_contract=None) -> StageResult:
    error=_boundary_error(boundary,boundary_contract)
    if error:return _failure(boundary,*error)
    required={'adm_cd','gu','dong',*POPULATION_FIELDS}
    if population.columns.duplicated().any() or not required.issubset(population) or not {'gu','dong'}.issubset(boundary):
        return _failure(population,'POPULATION_SCHEMA','verified ADM_CD/gu/dong/population fields and boundary hierarchy required')
    p=population.copy(deep=True);p['adm_cd']=p.adm_cd.astype('string')
    b=boundary.copy(deep=True);b['ADM_CD']=b.ADM_CD.astype('string')
    if len(p)!=len(b) or p.adm_cd.isna().any() or p.adm_cd.duplicated().any() or set(p.adm_cd)!=set(b.ADM_CD):
        return _failure(p,'POPULATION_BOUNDARY_BIJECTION','complete unique exact population/boundary ADM_CD set equality required')
    values={c:pd.to_numeric(p[c],errors='coerce') for c in POPULATION_FIELDS}
    for c in POPULATION_FIELDS[:2]:
        numbers=values[c]
        if (numbers.isna().any() or not np.isfinite(numbers.to_numpy(dtype=float,na_value=np.nan)).all()
                or numbers.lt(0).any() or numbers.mod(1).ne(0).any()
                or p[c].map(lambda v:isinstance(v,(bool,np.bool_))).any()):
            return _failure(p,'POPULATION_VALUES','verified nonnegative integer population required')
    total,senior,share=(values[c] for c in POPULATION_FIELDS)
    positive=total.gt(0)
    if (senior.gt(total).any() or not np.allclose(share[positive],senior[positive]/total[positive],rtol=0,atol=1e-12,equal_nan=False)
            or share[~positive].notna().any()):
        return _failure(p,'POPULATION_VALUES','verified senior<=total and population share consistency required')
    labels=p.set_index('adm_cd').loc[b.ADM_CD]
    if (labels.gu.isna().any() or labels.dong.isna().any() or b.gu.isna().any()
            or not np.array_equal(labels.gu.to_numpy(),b.gu.to_numpy())
            or not np.array_equal(labels.dong.to_numpy(),b.ADM_NM.to_numpy())
            or not b.dong.eq(b.ADM_NM).fillna(False).all()):
        return _failure(p,'POPULATION_BOUNDARY_LABEL','ADM_CD matches but gu/dong labels disagree')
    out=b.merge(p.drop(columns=['gu','dong']),left_on='ADM_CD',right_on='adm_cd',how='left',validate='one_to_one',suffixes=('_boundary','_population'))
    return StageResult(out.sort_values('ADM_CD',kind='stable').reset_index(drop=True),[],pd.DataFrame())


def enrich_station_population(mapping: pd.DataFrame,population_boundary: gpd.GeoDataFrame, *, boundary_contract=None) -> StageResult:
    """Attach verified population only after unique ADM_CD mapping."""
    if not {'ADM_CD','mapping_status','canonical_station_id'}.issubset(mapping) or not {'ADM_CD',*POPULATION_FIELDS}.issubset(population_boundary):
        return _failure(mapping,'ENRICHMENT_SCHEMA','mapping and verified population boundary fields required')
    if mapping.canonical_station_id.duplicated().any() or population_boundary.ADM_CD.duplicated().any():
        return _failure(mapping,'ENRICHMENT_KEYS','unique mapping/population keys required')
    mapped=mapping.mapping_status.eq('MAPPED')
    if (mapping.loc[mapped,'ADM_CD'].isna().any() or not mapping.loc[mapped,'ADM_CD'].isin(population_boundary.ADM_CD).all()
            or mapping.loc[~mapped,'ADM_CD'].notna().any()):
        return _failure(mapping,'ENRICHMENT_MAPPING','only successful mappings may have verified ADM_CD')
    out=mapping.copy(deep=True);lookup=population_boundary.set_index('ADM_CD')
    for field in POPULATION_FIELDS:out[field]=out.ADM_CD.map(lookup[field]).where(mapped)
    for field in population_boundary:
        if field.startswith('source_') or field in ['reference_period','reference_date','unit','hierarchy_evidence']:
            out['population_'+field]=out.ADM_CD.map(lookup[field]).where(mapped)
    return StageResult(out.sort_values('canonical_station_id',kind='stable').reset_index(drop=True),[],pd.DataFrame())


def summarize_spatial_mapping(core,master,mapping):
    """Diagnostic masks only; retain all original core observations."""
    _validate_eligibility(master)
    eligible=master[master.spatial_status.isin(ELIGIBLE_STATUSES)]
    if (set(core.canonical_station_id)!=set(master.canonical_station_id)
            or mapping.canonical_station_id.duplicated().any()
            or set(mapping.canonical_station_id)!=set(eligible.canonical_station_id)
            or not mapping.mapping_status.isin(MAPPING_STATUSES).all()):
        raise ValueError('Complete unique original/eligible/mapping identity accounting required')
    if mapping.loc[mapping.mapping_status.eq('MAPPED'),'ADM_CD'].isna().any():raise ValueError('MAPPED requires ADM_CD')
    failures=mapping.mapping_status.ne('MAPPED')
    for field in ['mapping_reason','mapping_evidence']:
        if field not in mapping or mapping.loc[failures,field].isna().any() or mapping.loc[failures,field].astype(str).str.strip().eq('').any():
            raise ValueError('Every non-MAPPED identity requires reason and evidence')
    matched=core.join_status.eq('matched')
    def counts(ids):
        ids=set(ids);mask=core.canonical_station_id.isin(ids)
        return dict(station_identities=len(ids),integrated_rows=int(mask.sum()),matched_rows=int((mask&matched).sum()),
            total_only_rows=int((mask&core.join_status.eq('total_only')).sum()),
            total_ridership_all_observations=int(core.loc[mask,'total'].sum()),
            total_ridership_matched_observations=int(core.loc[mask&matched,'total'].sum()),
            senior_ridership_all_observations=int(core.loc[mask,'senior'].sum()),
            senior_ridership_matched_observations=int(core.loc[mask&matched,'senior'].sum()))
    original=counts(master.canonical_station_id);task5=counts(eligible.canonical_station_id)
    success=mapping[mapping.mapping_status.eq('MAPPED')];mapped=counts(success.canonical_station_id)
    excluded5=counts(master.loc[~master.spatial_status.isin(ELIGIBLE_STATUSES),'canonical_station_id'])
    excluded9=counts(mapping.loc[mapping.mapping_status.ne('MAPPED'),'canonical_station_id'])
    cumulative={k:original[k]-mapped[k] for k in original}
    def ratios(n,d):return {k:n[k]/d[k] if d[k] else None for k in d}
    distribution=success.groupby('ADM_CD',observed=True).size()
    return dict(completion_mode=COMPLETION_MODE,core_preserved=True,
        denominators=dict(original=original,task5_eligible=task5,task9_mapped=mapped),
        by_mapping_status={s:counts(mapping.loc[mapping.mapping_status.eq(s),'canonical_station_id']) for s in MAPPING_STATUSES},
        task5_exclusions=excluded5,task9_additional_exclusions=excluded9,cumulative_exclusions=cumulative,
        task5_exclusion_shares=ratios(excluded5,original),task9_incremental_shares_of_original=ratios(excluded9,original),
        task9_incremental_shares_of_eligible=ratios(excluded9,task5),cumulative_exclusion_shares=ratios(cumulative,original),
        cumulative_coverage_shares=ratios(mapped,original),
        population_coverage=dict(distinct_ADM_CD=int(len(distribution)),
            stations_per_ADM_CD={str(k):int(v) for k,v in distribution.sort_index().items()},
            station_count_distribution={str(k):int(v) for k,v in distribution.value_counts().sort_index().items()}))
