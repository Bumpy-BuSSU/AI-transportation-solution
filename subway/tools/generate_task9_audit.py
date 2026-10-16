"""Reproduce Task9 validation evidence only; no production publication."""
from pathlib import Path
import argparse
import gc
import hashlib
import json
import platform
import sys
import tempfile
from dataclasses import asdict
import pandas as pd
import geopandas as gpd
import shapely
import pyproj

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from subway.src.clean.ridership import load_ridership_rules,clean_ridership
from subway.src.transform.station_keys import assign_station_ids,build_senior_crosswalk,normalize_station_name
from subway.src.transform.ridership import integrate_ridership,KEYS
from subway.src.transform.spatial import (build_station_master,map_stations_to_dongs,
    map_population_to_boundary,enrich_station_population,summarize_spatial_mapping)
from subway.src.clean.population import verify_population_hierarchy,clean_population
from subway.src.clean.population_direct import clean_direct_population,compare_population_sources
from subway.src.clean.spatial import clean_boundary
from subway.src.ingest.population_direct import read_direct_population
from subway.src.ingest.spreadsheetml import read_spreadsheetml
from subway.src.utils.artifacts import write_artifacts
from subway.src.transform.spatial_eligibility import summarize_spatial_eligibility

BASE='411374b88049bffaaaebf5d55ec51b231265f4d4'


def validate_output_directory(repo,output):
    output=Path(output).resolve();raw=(Path(repo)/'subway/data/raw').resolve()
    if output==raw or raw in output.parents:raise ValueError('Task9 cannot write in Raw')
    return output


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(result):
    if any(f.severity=='ERROR' for f in result.findings):
        raise ValueError([asdict(f) for f in result.findings])
    return result.frame


def load_core(repo,manifest,rules):
    """Use existing Task8 cleaners/identity/integration; return unfiltered core."""
    def read(dataset):return pd.read_csv(repo/manifest.loc[dataset,'raw_path'],encoding='cp949',dtype=str,keep_default_na=False)
    senior=read('senior_ridership');total=read('total_ridership')
    def wide(raw,dataset):
        out=pd.DataFrame(dict(station_code_raw=raw['역번호'],station_name_raw=raw['역명'],
            station_name=raw['역명'].map(normalize_station_name),source_row_id=range(1,len(raw)+1),
            source_file=manifest.loc[dataset,'raw_path'],source_dataset_id=dataset))
        if dataset=='total_ridership':out['line']=raw['호선'].map(rules['ridership']['line_map'])
        return out
    twide=checked(assign_station_ids(wide(total,'total_ridership')))
    aliases=pd.read_csv(repo/'subway/config/station_aliases.csv',dtype=str,keep_default_na=False)
    swide=checked(build_senior_crosswalk(wide(senior,'senior_ridership'),twide,aliases))
    frames=[];accounting={}
    for dataset,raw,identity in [('senior_ridership',senior,swide),('total_ridership',total,twide)]:
        frame=checked(clean_ridership(raw,dataset,2024,rules,manifest.loc[dataset,'raw_path']))
        ids=identity.set_index('source_row_id')
        for c in ['line','station_name','canonical_station_id','crosswalk_status','crosswalk_evidence','alias_applied','alias_evidence']:
            if c in ids:frame[c]=frame.source_row_id.map(ids[c])
        for c in frame.select_dtypes(include=['object','string']):
            if frame[c].nunique(dropna=False)<1000:frame[c]=frame[c].astype('category')
        accounting[dataset]=dict(raw_rows=len(raw),long_rows=len(frame),ridership_sum=int(frame.ridership.sum()),duplicate_keys=int(frame.duplicated(KEYS,keep=False).sum()))
        frames.append(frame)
    result=integrate_ridership(*frames,rules);core=checked(result)
    expected=json.loads((repo/'subway/data/validation/batch3_ridership_integration_summary.json').read_text(encoding='utf-8'))
    assert len(core)==expected['integrated_rows']
    assert {s:int(core.join_status.eq(s).sum()) for s in expected['join_counts']}==expected['join_counts']
    for label,dataset in [('senior','senior_ridership'),('total','total_ridership')]:
        accounting[dataset]['integrated_sums_by_join_status']={s:int(core.loc[core.join_status.eq(s),label].sum()) for s in expected['join_counts']}
    assert accounting==expected['input_accounting']
    assert int(core.non_senior.notna().sum())==expected['valid_non_senior']
    assert int(core.senior_share.notna().sum())==expected['valid_senior_share']
    assert len(result.exceptions[result.exceptions.exception_code.eq('SENIOR_EXCEEDS_TOTAL')])==expected['senior_excess']['count']
    del frames,senior,total;gc.collect()
    return core,dict(integrated_rows=len(core),join_counts=expected['join_counts'],input_accounting=accounting,
        senior_exceeds_total_exceptions=expected['senior_excess']['count'])


def generate(repo,output,*,reverse=False):
    output=validate_output_directory(repo,output)
    previous=json.loads((repo/'subway/data/validation/task5_spatial_eligibility_summary.json').read_text(encoding='utf-8'))
    frozen={name:sha(path) for path in (repo/'subway/data/validation').iterdir() if path.is_file() and not path.name.startswith('task9_') for name in [path.relative_to(repo).as_posix()]}
    frozen.update({name:sha(repo/name) for name in ['subway/data_manifest.csv','subway/config/datasets.yaml','subway/config/source_contracts_2024.yaml',
        'subway/config/validation_rules.yaml','subway/config/station_aliases.csv','subway/config/spatial_eligibility_2024.yaml']})
    for name,digest in previous['regression']['raw_hashes'].items():assert sha(repo/name)==digest,name
    for name,digest in previous['output_hashes'].items():assert sha(repo/'subway/data/validation'/name)==digest,name
    rules=load_ridership_rules(repo/'subway/config')
    manifest=pd.read_csv(repo/'subway/data_manifest.csv',dtype=str,keep_default_na=False).set_index('dataset_id')
    core,core_regression=load_core(repo,manifest,rules)
    eligibility=pd.read_csv(repo/'subway/data/validation/task5_spatial_eligibility.csv',dtype={'line':str,'station_code_raw_ridership':str,'station_code_raw_coordinate':str},keep_default_na=False)
    master=checked(build_station_master(eligibility))
    before=summarize_spatial_eligibility(core,master)
    for k in ['denominators','by_status','exclusions','exclusion_shares','exclusion_reasons']:
        assert before[k]==previous[k],k
    raw_boundary=gpd.read_file(repo/manifest.loc['boundary','raw_path'])
    old=read_spreadsheetml(repo/manifest.loc['population','raw_path'],'데이터','euc-kr',1)
    hierarchy=verify_population_hierarchy(old,raw_boundary,rules)
    boundary=checked(clean_boundary(raw_boundary,dict(rules,boundary_hierarchy=hierarchy),manifest.loc['boundary','raw_path']))
    contract=rules['source_contracts']['population_direct_65_plus']
    direct=read_direct_population(repo/manifest.loc['population_direct_65_plus','raw_path'],contract)
    population=checked(clean_direct_population(direct,raw_boundary,rules,manifest.loc['population_direct_65_plus','raw_path']))
    supplementary=clean_population(old,hierarchy,rules,manifest.loc['population','raw_path']).frame
    comparison=checked(compare_population_sources(population,supplementary))
    assert len(comparison)==400
    assert len(population)==426 and int(population.population_total.sum())==9619861 and int(population.population_65_plus.sum())==1785286
    if reverse:master=master.iloc[::-1];boundary=boundary.iloc[::-1];population=population.iloc[::-1];core=core.iloc[::-1]
    population_boundary=checked(map_population_to_boundary(population,boundary))
    mapped=map_stations_to_dongs(master,boundary);checked(mapped)
    enriched=checked(enrich_station_population(mapped.frame,population_boundary))
    exceptions=enriched[enriched.mapping_status.ne('MAPPED')].copy()
    exceptions['exception_code']=exceptions.mapping_status
    summary=summarize_spatial_mapping(core,master,enriched)
    assert summarize_spatial_eligibility(core,master)['denominators']==previous['denominators']
    summary.update(mission='P-S2-T9',starting_head=BASE,task9_status='COMPLETE',human_task9_review='PENDING',
        task5_status='HUMAN-APPROVED COMPLETE',task6_status='COMPLETE',task8_status='COMPLETE',task10_status='NOT STARTED',task11_status='NOT STARTED',
        mapping_rule='strict within exactly one polygon; touches only for non-within points; no nearest/buffer/snap/manual coordinate or ADM_CD correction',
        crs=dict(input='EPSG:4326',status='ANALYTICAL_ASSUMPTION',source_specific_verified=False,output='EPSG:5179',axis='longitude=x latitude=y',evidence=previous['assumptions']['crs_evidence']),
        temporal_status='SNAPSHOT_STABILITY_ASSUMPTION',temporal_evidence=previous['assumptions']['temporal_evidence'],
        station_master=dict(station_identities=len(master),task5_status_counts={k:int(v) for k,v in master.spatial_status.value_counts().sort_index().items()},
            authoritative_eligibility_file='subway/data/validation/task5_spatial_eligibility.csv',sha256=sha(repo/'subway/data/validation/task5_spatial_eligibility.csv')),
        boundary=dict(rows=len(boundary),crs=boundary.crs.to_string(),base_date='20240630',source=manifest.loc['boundary','raw_path']),
        population=dict(ADM_CD_bijection='426/426 PASS',population_total=int(population.population_total.sum()),population_65_plus=int(population.population_65_plus.sum()),old_source_comparison='400/400 exact PASS'),
        non_mapped_stations=exceptions[['canonical_station_id','line','station_name','latitude','longitude','mapping_status','candidate_ADM_CD','mapping_reason']].to_dict('records'),
        findings=[asdict(f) for f in mapped.findings],
        regression=dict(task5_counts_and_shares_unchanged=True,task6_direct_totals_and_400_comparison_unchanged=True,task8=core_regression,
            raw_hashes=previous['regression']['raw_hashes'],frozen_file_hashes=frozen),
        environment=dict(python=platform.python_version(),pandas=pd.__version__,geopandas=gpd.__version__,shapely=shapely.__version__,pyproj=pyproj.__version__,proj=pyproj.proj_version_str),
        limitations='approved CRS/snapshot analytical assumptions remain; strict map may exclude eligible stations; Q2 dong population is an area attribute, not station-specific population; preprocessing QA only')
    frames={'task9_station_dong_map.csv':enriched,'task9_station_dong_exceptions.csv':exceptions}
    sorts={name:['canonical_station_id'] for name in frames}
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        hashes=write_artifacts(Path(temporary),frames,summary,sort_columns=sorts)
        for name in frames:(output/name).write_bytes((Path(temporary)/name).read_bytes())
        (output/'task9_spatial_summary.json').write_bytes((Path(temporary)/'pipeline_summary.json').read_bytes())
    for name,digest in frozen.items():assert sha(repo/name)==digest,name
    for name,digest in previous['regression']['raw_hashes'].items():assert sha(repo/name)==digest,name
    print(json.dumps(dict(status_counts=enriched.mapping_status.value_counts().sort_index().to_dict(),exceptions=summary['non_mapped_stations'],
        coverage=summary['cumulative_coverage_shares'],population_coverage=summary['population_coverage'],hashes=hashes),ensure_ascii=False,indent=2))
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'subway/data/validation')
    parser.add_argument('--reverse-input-order',action='store_true')
    args=parser.parse_args(argv)
    generate(ROOT,args.output_dir,reverse=args.reverse_input_order)
    return 0


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
