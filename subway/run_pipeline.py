"""Reproducible preprocessing; full transport core and configured study scope."""
from pathlib import Path
import argparse
import gc
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
from dataclasses import asdict
import numpy as np
import pandas as pd
import geopandas as gpd
import pyarrow
import shapely
import pyproj
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from subway.src.validate.pipeline_validation import preflight,pipeline_status
from subway.src.validate.raw_validation import Finding
from subway.src.clean.ridership import load_ridership_rules,clean_ridership
from subway.src.clean.weather import clean_weather
from subway.src.clean.station import clean_stations
from subway.src.clean.spatial import clean_boundary,clean_shelters
from subway.src.clean.population import verify_population_hierarchy,clean_population
from subway.src.clean.population_direct import clean_direct_population,compare_population_sources
from subway.src.ingest.population_direct import read_direct_population
from subway.src.ingest.spreadsheetml import read_spreadsheetml
from subway.src.transform.station_keys import assign_station_ids,build_senior_crosswalk,normalize_station_name,match_stations
from subway.src.transform.ridership import integrate_ridership,KEYS
from subway.src.transform.spatial_eligibility import build_spatial_eligibility,summarize_spatial_eligibility,ELIGIBLE_STATUSES
from subway.src.transform.spatial import build_station_master,map_stations_to_dongs,map_population_to_boundary,enrich_station_population,summarize_spatial_mapping,MAPPING_STATUSES
from subway.src.transform.study_area import load_study_area,classify_study_area,SCOPE_STATUSES
from subway.src.utils.artifacts import write_artifacts,_check_metadata
from subway.src.utils.paths import resolve_repo_relative

QUALITY_COLUMNS=['severity','dataset_id','code','message','relative_path']
VALIDATION_NAMES=['data_quality_report.csv','join_report.csv','exceptions_ridership.csv','exceptions_station.csv','exceptions_spatial.csv','pipeline_summary.json']


def _sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def _environment():
    return dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,pyarrow=pyarrow.__version__,
        geopandas=gpd.__version__,shapely=shapely.__version__,pyproj=pyproj.__version__,proj=pyproj.proj_version_str)


def _quality(findings):
    return pd.DataFrame([asdict(f) for f in findings],columns=QUALITY_COLUMNS).drop_duplicates().sort_values(QUALITY_COLUMNS,kind='stable').reset_index(drop=True)


def _build_products(repo,year,profile):
    """Reuse approved Tasks1–9. No weather exposure is joined to transport core."""
    rules=load_ridership_rules(repo/'subway/config')
    manifest=pd.read_csv(repo/'subway/data_manifest.csv',dtype=str,keep_default_na=False).set_index('dataset_id')
    findings=[]
    def source(dataset):return manifest.loc[dataset,'raw_path']
    def read(dataset):return pd.read_csv(resolve_repo_relative(repo,source(dataset)),encoding=rules['source_contracts'][dataset]['encoding'],dtype=str,keep_default_na=False)
    def checked(result):
        findings.extend(result.findings)
        if any(f.severity=='ERROR' for f in result.findings):raise PipelineBlocked(findings)
        return result.frame
    aliases=pd.read_csv(repo/'subway/config/station_aliases.csv',dtype=str,keep_default_na=False)
    raw={d:read(d) for d in ['senior_ridership','total_ridership']}
    def wide(frame,dataset):
        out=pd.DataFrame(dict(station_code_raw=frame['역번호'],station_name_raw=frame['역명'],station_name=frame['역명'].map(normalize_station_name),
            source_row_id=range(1,len(frame)+1),source_file=source(dataset),source_dataset_id=dataset))
        if dataset=='total_ridership':out['line']=frame['호선'].map(rules['ridership']['line_map'])
        return out
    total_ids=checked(assign_station_ids(wide(raw['total_ridership'],'total_ridership')))
    senior_ids=checked(build_senior_crosswalk(wide(raw['senior_ridership'],'senior_ridership'),total_ids,aliases))
    products={};clean=[];accounting={}
    for dataset,identity in [('senior_ridership',senior_ids),('total_ridership',total_ids)]:
        frame=checked(clean_ridership(raw[dataset],dataset,year,rules,source(dataset)))
        ids=identity.set_index('source_row_id')
        for col in ['line','station_name','canonical_station_id','crosswalk_status','crosswalk_evidence','alias_applied','alias_evidence']:
            if col in ids:frame[col]=frame.source_row_id.map(ids[col])
        for col in frame.select_dtypes(include=['object','string']):
            if frame[col].nunique(dropna=False)<1000:frame[col]=frame[col].astype('category')
        accounting[dataset]=dict(raw_rows=len(raw[dataset]),long_rows=len(frame),ridership_sum=int(frame.ridership.sum()),duplicate_keys=int(frame.duplicated(KEYS,keep=False).sum()))
        products[f'clean/{dataset}_{year}.parquet']=frame;clean.append(frame)
    del raw;gc.collect()
    integration=integrate_ridership(*clean,rules);core=checked(integration)
    for label,dataset in [('senior','senior_ridership'),('total','total_ridership')]:
        sums={status:int(core.loc[core.join_status.eq(status),label].sum()) for status in ['matched','total_only','senior_only','ambiguous_rejected']}
        if sum(sums.values())!=accounting[dataset]['ridership_sum']:raise ValueError('ridership accounting does not conserve source observations')
        accounting[dataset]['integrated_sums_by_join_status']=sums
    products[f'processed/ridership_{year}.parquet']=core
    products['validation/exceptions_ridership.csv']=integration.exceptions.copy()
    products['validation/join_report.csv']=core.loc[core.join_status.ne('matched'),KEYS+['line','station_name','join_status','total','senior']].copy()
    weather_id=profile['weather_dataset_id'];weather=checked(clean_weather(read(weather_id),year,rules,source(weather_id)))
    products[f'clean/weather_{year}.parquet']=weather
    station=clean_stations(read('station'),rules,source('station'))
    products['clean/stations.parquet']=station.frame
    identities=core[['canonical_station_id','line','station_name','total_station_code_raw']].drop_duplicates().rename(columns={'total_station_code_raw':'station_code_raw_ridership'})
    matches=match_stations(identities[['line','station_name','station_code_raw_ridership']].rename(columns={'station_code_raw_ridership':'station_code_raw'}),station.frame,aliases)
    policy=yaml.safe_load((repo/f'subway/config/spatial_eligibility_{year}.yaml').read_text(encoding='utf-8'))
    support=pd.read_csv(repo/'subway/data/validation/batch2rc_station_candidate_mapping.csv',dtype=str,keep_default_na=False)
    eligibility=checked(build_spatial_eligibility(identities,matches.frame,station,support,policy))
    # Earlier source-level ERRORs have exact, approved per-row dispositions.
    # Never disposition a new code/identity/geometry error by a broad rule.
    approved=pd.read_csv(repo/'subway/data/validation/task5_spatial_eligibility.csv',dtype=str,keep_default_na=False)
    allowed=approved[approved.exclusion_reason.eq('UNRESOLVED_SOURCE_COORDINATE_COLLISION')]
    allowed_ids=set(pd.to_numeric(allowed.station_coordinate_source_row_id))
    collision=station.exceptions[station.exceptions.exception_code.eq('DUPLICATE_COORDINATE')] if 'exception_code' in station.exceptions else pd.DataFrame()
    allowed_rows=station.frame[station.frame.source_row_id.isin(allowed_ids)]
    approved_pairs=set(zip(allowed.line,allowed.station_code_raw_coordinate,allowed.latitude,allowed.longitude))
    actual_pairs={(str(r.line),str(r.station_code_raw),str(r.latitude),str(r.longitude)) for r in allowed_rows.itertuples()}
    for f in station.findings:
        if f.code=='CRS_UNVERIFIED':
            findings.append(Finding('WARNING','station',f.code,'source-specific CRS unverified; Task5-approved EPSG:4326 ANALYTICAL_ASSUMPTION used without rewriting source metadata',f.relative_path));continue
        if f.severity=='ERROR' and f.code=='DUPLICATE_COORDINATE' and not collision.empty and set(collision.source_row_id).issubset(allowed_ids) and actual_pairs==approved_pairs:
            findings.append(Finding('WARNING','station','APPROVED_COORDINATE_EXCLUSION','source DUPLICATE_COORDINATE retained in exceptions; exact Task5-approved collision excluded from spatial use',f.relative_path))
        else:findings.append(f)
    for f in matches.findings:
        if f.severity=='ERROR' and f.code=='SOURCE_CODE_CONFLICT':
            conflict_ids=matches.frame[matches.frame.source_code_conflict][['line','station_name']]
            valid=eligibility[eligibility.spatial_status.eq('ELIGIBLE_CODE_WARNING')]
            if set(map(tuple,conflict_ids.astype(str).to_numpy())).issubset(set(map(tuple,valid[['line','station_name']].astype(str).to_numpy()))):
                findings.append(Finding('WARNING','station','SOURCE_CODE_CONFLICT','external codes unreconciled; per-row Task5 corroboration permits spatial use with warnings'));continue
        if f.severity=='ERROR' and f.code=='UNRESOLVED_STATION_IDENTITY':
            unmapped=matches.frame[matches.frame.match_status.eq('ridership_only')]
            excluded=eligibility[~eligibility.spatial_status.isin(ELIGIBLE_STATUSES)]
            if set(map(tuple,unmapped[['line','station_name']].astype(str).to_numpy())).issubset(set(map(tuple,excluded[['line','station_name']].astype(str).to_numpy()))):
                findings.append(Finding('WARNING','station','DOCUMENTED_IDENTITY_EXCLUSIONS','unmatched core identities explicitly excluded by Task5; coordinate-only source rows remain audit evidence'));continue
        findings.append(f)
    if any(f.severity=='ERROR' for f in findings):raise PipelineBlocked(findings)
    master=checked(build_station_master(eligibility))
    excluded=master[~master.spatial_status.isin(ELIGIBLE_STATUSES)]
    if len(excluded):findings.append(Finding('WARNING','station','TASK5_SPATIAL_EXCLUSIONS',f'{len(excluded)} core identities preserved but spatially excluded'))
    if master.identity_status.eq('alias_matched').any():findings.append(Finding('WARNING','station','APPROVED_ALIASES','explicit approved aliases retain evidence'))
    boundary_id=profile['boundary_dataset_id'];population_id=profile['population_dataset_id'];shelter_id=profile['climate_response_dataset_id']
    raw_boundary=gpd.read_file(resolve_repo_relative(repo,source(boundary_id)))
    old=read_spreadsheetml(resolve_repo_relative(repo,source('population')),'데이터','euc-kr',1)
    hierarchy=verify_population_hierarchy(old,raw_boundary,rules)
    boundary=checked(clean_boundary(raw_boundary,dict(rules,boundary_hierarchy=hierarchy),source(boundary_id)))
    direct=read_direct_population(resolve_repo_relative(repo,source(population_id)),rules['source_contracts'][population_id])
    population=checked(clean_direct_population(direct,raw_boundary,rules,source(population_id)))
    supplementary=clean_population(old,hierarchy,rules,source('population'))
    if supplementary.findings:
        findings.append(Finding('WARNING','population','SUPPLEMENTARY_SOURCE_LIMITS','old age-band rejected rows retained in diagnostics; valid groups independently compared; direct official source remains primary'))
    # Partial old age bands are not primary input; compare their fully valid rows.
    comparison=checked(compare_population_sources(population,supplementary.frame,expected_overlap=len(supplementary.frame)))
    boundary_population=checked(map_population_to_boundary(population,boundary,boundary_contract=profile['boundary_contract']))
    mapping=map_stations_to_dongs(master,boundary,boundary_contract=profile['boundary_contract']);mapped=checked(mapping)
    enriched=checked(enrich_station_population(mapped,boundary_population))
    scoped=checked(classify_study_area(master,boundary,profile))
    fields=['canonical_station_id','study_area_id','study_area_status','study_area_reason','study_area_evidence']
    enriched=enriched.merge(scoped[fields],on='canonical_station_id',how='left',validate='one_to_one')
    outside=enriched.mapping_status.eq('ZERO_MATCH') & enriched.study_area_status.eq('OUTSIDE_CURRENT_STUDY_AREA')
    disagreement=enriched.mapping_status.eq('ZERO_MATCH') & ~outside
    if disagreement.any():
        findings.append(Finding('WARNING','study_area','UNRESOLVED_ZERO_MATCH_SCOPE','ZERO_MATCH does not establish outside-union membership; discrepancy retained as unresolved'))
        enriched.loc[disagreement,'study_area_status']='UNRESOLVED_STUDY_AREA_STATUS'
        enriched.loc[disagreement,'study_area_reason']='MAPPING_SCOPE_DISCREPANCY'
        ids=enriched.loc[disagreement,'canonical_station_id']
        scoped.loc[scoped.canonical_station_id.isin(ids),['study_area_status','study_area_reason']]=['UNRESOLVED_STUDY_AREA_STATUS','MAPPING_SCOPE_DISCREPANCY']
    scope_counts={s:int(enriched.study_area_status.eq(s).sum()) for s in SCOPE_STATUSES}
    if outside.any():findings.append(Finding('INFO','study_area','OUTSIDE_CURRENT_STUDY_AREA',f'{int(outside.sum())} eligible points independently outside configured boundary union; core preserved'))
    products['processed/station_master.parquet']=scoped
    products['processed/station_dong_map.parquet']=enriched
    products[f'processed/dong_population_{year}q2.parquet']=boundary_population
    products[f'clean/population_{year}q2.parquet']=population
    products[f'clean/dong_boundary_{year}q2.parquet']=boundary
    products['clean/climate_shelters.parquet']=checked(clean_shelters(read(shelter_id),rules,source(shelter_id)))
    station_parts=[station.exceptions,matches.exceptions,excluded.assign(exception_code='TASK5_SPATIAL_EXCLUSION')]
    records=[]
    for kind,frame in zip(['source','match','eligibility'],station_parts):
        for i,row in enumerate(frame.to_dict('records')):
            records.append(dict(exception_id=f'{kind}:{i:06}',exception_code=row.get('exception_code',''),
                canonical_station_id=row.get('canonical_station_id',''),line=row.get('line',''),station_name=row.get('station_name',''),
                source_row_id=row.get('source_row_id',row.get('station_coordinate_source_row_id',None)),
                station_code_raw=row.get('station_code_raw',row.get('station_code_raw_ridership','')),
                latitude=row.get('latitude',None),longitude=row.get('longitude',None),
                reason=row.get('exclusion_reason','source/match diagnostics retained; see eligibility provenance')))
    products['validation/exceptions_station.csv']=pd.DataFrame(records,columns=['exception_id','exception_code','canonical_station_id','line','station_name','source_row_id','station_code_raw','latitude','longitude','reason'])
    products['validation/exceptions_spatial.csv']=enriched[enriched.mapping_status.ne('MAPPED')].copy()
    summary=dict(year=year,study_area=dict(id=profile['study_area_id'],label=profile['study_area_label'],boundary_source=source(boundary_id),
        current_empirical_scope=profile['current_empirical_scope'],weather_scope=profile['weather_scope'],future_extension=profile['future_extension']),
        task8=dict(integrated_rows=len(core),**{s:int(core.join_status.eq(s).sum()) for s in ['matched','total_only','senior_only','ambiguous_rejected']},
            senior_excess=int(integration.exceptions.exception_code.eq('SENIOR_EXCEEDS_TOTAL').sum()),input_accounting=accounting),
        task5=dict(station_identities=len(master),status_counts={s:int(master.spatial_status.eq(s).sum()) for s in ['ELIGIBLE','ELIGIBLE_CODE_WARNING','EXCLUDED_IDENTITY','EXCLUDED_COORDINATE','EXCLUDED_TEMPORAL']},
            coverage=summarize_spatial_eligibility(core,master)),
        task6=dict(dongs=len(population),population_total=int(population.population_total.sum()),population_65_plus=int(population.population_65_plus.sum()),old_source_comparison=len(comparison),ADM_CD_bijection='PASS'),
        task9=dict(eligible=len(enriched),**{s:int(enriched.mapping_status.eq(s).sum()) for s in MAPPING_STATUSES},human_approved_on='2026-10-07'),
        study_area_counts=scope_counts,station_master_scope_counts={s:int(scoped.study_area_status.eq(s).sum()) for s in SCOPE_STATUSES},
        zero_match_union_check=dict(zero_match=int(enriched.mapping_status.eq('ZERO_MATCH').sum()),outside_union=int(outside.sum()),unresolved=int(disagreement.sum()),method='independent configured validated boundary union contains/touches; longitude=x latitude=y'),
        spatial_coverage=summarize_spatial_mapping(core,master,enriched),task10_human_review='PENDING',task11_status='NOT STARTED',
        source_station_diagnostics=dict(original_findings=[asdict(f) for f in station.findings],
            approved_disposition='only exact pinned Task5 collision rows are excluded spatially; original ERROR and coordinates remain in source exception evidence'),
        supplementary_population_diagnostics=dict(role='validation/supplementary only; no competing primary population output',
            valid_dongs=len(supplementary.frame),original_findings=[asdict(f) for f in supplementary.findings],
            rejected_rows=len(supplementary.exceptions),primary_source=population_id))
    summary['task5']['coverage'].pop('task9_status',None)
    return products,summary,findings


class PipelineBlocked(Exception):
    def __init__(self,findings):self.findings=findings;super().__init__('blocking validation findings')


def _baseline_check(summary,baseline):
    for task in ['task5','task6','task8','task9']:
        for key,value in baseline[task].items():
            if summary[task].get(key)!=value:raise ValueError(f'BASELINE_REGRESSION {task}.{key}: actual differs from accepted configuration')


def _sort_keys(path,frame):
    name=Path(path).name
    if name.startswith(('senior_ridership','total_ridership','ridership_')) or name=='join_report.csv':return KEYS
    if name=='exceptions_ridership.csv':return KEYS+['exception_code']
    if name=='data_quality_report.csv':return QUALITY_COLUMNS
    if name=='exceptions_station.csv':return ['exception_id']
    for keys in [['canonical_station_id'],['shelter_id'],['ADM_CD'],['adm_cd'],['date','station_id'],['source_row_id']]:
        if set(keys).issubset(frame):return keys
    raise ValueError(f'No explicit unique sort contract: {path}')


def _publish(repo,stage,paths):
    """Single writer, complete staging, rollback on I/O failure; summary last."""
    changed=[];backups=stage/'backup'
    try:
        for relative in sorted(paths,key=lambda p:(p.endswith('pipeline_summary.json'),p)):
            target=repo/'subway/data'/relative;candidate=stage/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            backup=backups/relative
            existed=target.exists()
            if existed:
                backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(target,backup)
            os.replace(candidate,target);changed.append((target,backup,existed))
    except OSError:
        for target,backup,existed in reversed(changed):
            if existed:os.replace(backup,target)
            else:target.unlink(missing_ok=True)
        raise


def _failed(repo,year,findings):
    validation=repo/'subway/data/validation';failure=validation/'pipeline_failure';failure.mkdir(parents=True,exist_ok=True)
    # OSError repr may escape Windows separators; normalize before publication.
    def portable(value):
        value=value.replace('\\\\','/').replace('\\','/')
        return value.replace(repo.as_posix()+'/', '').replace(repo.as_posix(), '.')
    original=findings
    findings=[Finding(f.severity,f.dataset_id,f.code,portable(f.message),portable(f.relative_path)) for f in original]
    if findings!=original:
        logdir=repo/'subway/logs';logdir.mkdir(parents=True,exist_ok=True)
        with (logdir/f'pipeline_{year}.log').open('a',encoding='utf-8') as log:
            log.write(json.dumps([asdict(f) for f in original],ensure_ascii=False)+'\n')
    _quality(findings).to_csv(failure/'data_quality_report.csv',index=False,encoding='utf-8',lineterminator='\n')
    payload=dict(year=year,status='PIPELINE FAILED',output_hashes={},clean_outputs={},processed_outputs={},validation_outputs=[],
        publication=dict(published=False,used_staging=True,prior_data_files='may remain from last successful generation; not results of this failed run'),
        failure_diagnostics='subway/data/validation/pipeline_failure/data_quality_report.csv',
        finding_counts={s:sum(f.severity==s for f in findings) for s in ['ERROR','WARNING','INFO']},environment=_environment(),task10_status='BLOCKED',task11_status='NOT STARTED')
    temp=validation/'pipeline_summary.failed.tmp';temp.write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    os.replace(temp,validation/'pipeline_summary.json')
    return 1


def run_pipeline(repo_root: Path,year: int) -> int:
    repo=Path(repo_root).resolve();data=repo/'subway/data';data.mkdir(parents=True,exist_ok=True)
    lock=data/'.pipeline.lock';fd=None
    findings=[]
    try:
        try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:return 1
        profile=load_study_area(repo,year)
        findings=preflight(repo,year)
        if any(f.severity=='ERROR' for f in findings):return _failed(repo,year,findings)
        inventory=pd.read_csv(data/'validation/raw_inventory.csv',dtype=str)
        inputs={f'subway/data/raw/{year}/{r.dataset_id}/{r.relative_path}':r.sha256 for r in inventory.itertuples()}
        config_hashes={p.relative_to(repo).as_posix():_sha(p) for p in sorted((repo/'subway/config').iterdir()) if p.suffix in ['.csv','.yaml']}
        baseline=yaml.safe_load((repo/f'subway/config/pipeline_baseline_{year}.yaml').read_text(encoding='utf-8'))
        if baseline.get('year')!=year or baseline.get('schema_version')!=1:raise ValueError('baseline configuration year/version')
        for path,digest in baseline.get('accepted_hashes',{}).items():
            if _sha(resolve_repo_relative(repo,path))!=digest:raise ValueError(f'BASELINE_REGRESSION approved input/evidence {path}')
        products,summary,stage_findings=_build_products(repo,year,profile);findings+=stage_findings
        _baseline_check(summary,baseline)
        status,exit_code=pipeline_status(findings)
        if exit_code:return _failed(repo,year,findings)
        products['validation/data_quality_report.csv']=_quality(findings)
        summary.update(status=status,task10_status='COMPLETE',input_dataset_count=int(inventory.dataset_id.nunique()),raw_file_count=len(inputs),input_hashes=inputs,
            config_hashes=config_hashes,environment=_environment(),finding_counts={s:int(_quality(findings).severity.eq(s).sum()) for s in ['ERROR','WARNING','INFO']},
            clean_outputs={p:dict(rows=len(f)) for p,f in products.items() if p.startswith('clean/')},
            processed_outputs={p:dict(rows=len(f)) for p,f in products.items() if p.startswith('processed/')},
            validation_outputs=['validation/'+n for n in VALIDATION_NAMES],
            publication=dict(published=True,used_staging=True,method='all gates before publication; single writer lock; rollback on replace failure; summary committed last'),
            determinism='same Raw/config/code/recorded environment; explicit unique sorts and writer settings; summary self-hash excluded')
        with tempfile.TemporaryDirectory(prefix='.pipeline-staging-',dir=data) as temporary:
            stage=Path(temporary);flat=stage/'serialize'
            hashes=write_artifacts(flat,{Path(p).name:f for p,f in products.items()},{},sort_columns={Path(p).name:_sort_keys(p,f) for p,f in products.items()})
            summary['output_hashes']={p:hashes[Path(p).name] for p in products}
            for kind in ['clean_outputs','processed_outputs']:
                for p in summary[kind]:summary[kind][p]['sha256']=summary['output_hashes'][p]
            _check_metadata(summary)
            for p in products:
                target=stage/p;target.parent.mkdir(parents=True,exist_ok=True);os.replace(flat/Path(p).name,target)
            summary_path=stage/'validation/pipeline_summary.json'
            summary_path.write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
            for path,digest in inputs.items():
                if _sha(resolve_repo_relative(repo,path))!=digest:raise ValueError('Raw changed during pipeline')
            for path,digest in config_hashes.items():
                if _sha(repo/path)!=digest:raise ValueError('configuration changed during pipeline')
            _publish(repo,stage,list(products)+['validation/pipeline_summary.json'])
        return 0
    except PipelineBlocked as exc:return _failed(repo,year,exc.findings)
    except Exception as exc:
        code='BASELINE_REGRESSION' if 'BASELINE_REGRESSION' in str(exc) else 'PIPELINE_ERROR'
        # Do not leak local filesystem paths into deterministic diagnostics.
        detail=str(exc) if code=='BASELINE_REGRESSION' else 'preprocessing or publication failed; see runtime log'
        logdir=repo/'subway/logs';logdir.mkdir(parents=True,exist_ok=True)
        import traceback
        with (logdir/f'pipeline_{year}.log').open('a',encoding='utf-8') as log:log.write(traceback.format_exc()+'\n')
        findings.append(Finding('ERROR','pipeline',code,f'{type(exc).__name__}: {detail}'))
        return _failed(repo,year,findings)
    finally:
        if fd is not None:os.close(fd);lock.unlink(missing_ok=True)


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--year',type=int,required=True)
    args=parser.parse_args(argv)
    return run_pipeline(ROOT,args.year)


if __name__=='__main__':raise SystemExit(main())
