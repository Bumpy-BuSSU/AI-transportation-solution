"""Reconstruct frozen Stage3C on accepted Parquets; stop for human scientific review."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import pyarrow
import statsmodels

from subway.run_confirmatory import sha256,_csv,_json
from subway.src.analysis.spatial_heterogeneity import (
    load_spatial_heterogeneity_config,build_spatial_context,build_station_day_panel,
    fit_station_heterogeneity,fit_stage3c_models,
)
from subway.src.analysis.spatial_figures import render_spatial_figures
from subway.src.utils.paths import resolve_repo_relative

BASELINE='d24830a7a4de3a41753fe53f8ccfa8ba6a8f2186'
INPUTS=['subway/data/processed/station_dong_map.parquet','subway/data/processed/dong_population_2024q2.parquet',
        'subway/data/clean/climate_shelters.parquet']


def _prior_inputs(repo,year):
    base_path=f'subway/data/analysis/analysis_base_{year}.parquet'
    if not (repo/base_path).exists():
        from subway.run_eda import run_eda
        if run_eda(repo,year):raise ValueError('approved Stage3A regeneration blocked')
    def read(path):return json.loads((repo/path).read_text(encoding='utf-8'))
    pipeline_path='subway/data/validation/pipeline_summary.json'
    eda_path='subway/results/tables/eda_summary.json'
    prior_path='subway/results/models/confirmatory_summary.json'
    pipeline,eda,prior=read(pipeline_path),read(eda_path),read(prior_path)
    if eda.get('status')!='EDA COMPLETE':raise ValueError('accepted Stage3A required')
    if prior.get('status')!='CONFIRMATORY H1/H2 COMPLETE':raise ValueError('accepted Stage3B required')
    tracked={}
    for path in INPUTS:
        expected=pipeline.get('output_hashes',{}).get(path.removeprefix('subway/data/'))
        if not expected or sha256(repo/path)!=expected:raise ValueError('Stage2 input hash mismatch: '+path)
        tracked[path]=expected
    expected=eda.get('output_hashes',{}).get(base_path)
    if not expected or sha256(repo/base_path)!=expected:raise ValueError('Stage3A analysis-base hash mismatch')
    if prior.get('analysis_base_sha256')!=expected:raise ValueError('Stage3B/3A base continuity mismatch')
    tracked[base_path]=expected
    config_path=f'subway/config/confirmatory_analysis_{year}.yaml'
    if sha256(repo/config_path)!=prior.get('config_sha256'):raise ValueError('Stage3B frozen config hash mismatch')
    for key,path in [('code_sha256','subway/src/analysis/confirmatory.py'),('runner_sha256','subway/run_confirmatory.py')]:
        if key in prior and sha256(repo/path)!=prior[key]:raise ValueError('Stage3B code integrity mismatch')
    # Protect all accepted Stage3B results and the summaries/config used for authorization.
    protect=[pipeline_path,eda_path,prior_path,config_path]
    protect += [p.relative_to(repo).as_posix() for folder in ['models','tables','figures']
        for p in (repo/'subway/results'/folder).glob('confirmatory*') if p.is_file()]
    protect += [p.relative_to(repo).as_posix() for p in (repo/'subway/results/models').glob('h[12]_primary_results.csv')]
    for path in protect:tracked[path]=sha256(repo/path)
    return tracked


def run_spatial_heterogeneity(repo_root: Path,year: int)->int:
    repo=Path(repo_root).resolve()
    try:
        config=load_spatial_heterogeneity_config(repo,year)
        hashes=_prior_inputs(repo,year)
        mapping=pd.read_parquet(repo/INPUTS[0]);boundary=gpd.read_parquet(repo/INPUTS[1]);shelters=gpd.read_parquet(repo/INPUTS[2])
        base=pd.read_parquet(repo/f'subway/data/analysis/analysis_base_{year}.parquet')
        dong,station,exceptions,context_qa=build_spatial_context(mapping,boundary,shelters,config)
        panel=build_station_day_panel(base,station,config,year)
        boarding=base.loc[base.boarding_type.eq('boarding')]
        invalid=boarding.loc[~boarding.age_comparison_valid.eq(True),['canonical_station_id','date','hour_bin','senior','total']].copy()
        if 'station_name' in station:invalid=invalid.merge(station[['canonical_station_id','station_name']],on='canonical_station_id',validate='many_to_one')
        invalid['date']=invalid.date.dt.strftime('%Y-%m-%d')
        invalid=invalid.astype(object).where(pd.notna(invalid),None)
        dates=panel.drop_duplicates('date')
        panel_qa=dict(station_days=len(panel),common_valid_boarding_cells=int(panel.support_cells.sum()),
            senior_zero_station_days=int(panel.senior.eq(0).sum()),non_senior_zero_station_days=int(panel.non_senior.eq(0).sum()),
            excluded_boarding_cells=invalid.to_dict('records'),
            extreme_day_counts={k:int(dates[k].sum()) for k in ['hot_primary','cold_primary','hot_sensitivity','cold_sensitivity']})
        layer_a=fit_station_heterogeneity(panel)
        primary,sensitivity,meta=fit_stage3c_models(panel)
        descriptives={}
        for col in ['beta_hot','beta_cold']:
            v=layer_a[col]
            descriptives[col]=dict(median=float(v.median()),q25=float(v.quantile(.25)),q75=float(v.quantile(.75)),
                minimum=float(v.min()),maximum=float(v.max()),negative_fraction=float(v.lt(0).mean()),positive_fraction=float(v.gt(0).mean()))
        code_paths=['subway/run_spatial_heterogeneity.py','subway/src/analysis/spatial_heterogeneity.py','subway/src/analysis/spatial_figures.py',f'subway/config/spatial_heterogeneity_{year}.yaml']
        summary=dict(status='STAGE3C TECHNICAL EXECUTION COMPLETE',human_scientific_review='PENDING',year=year,
            reconstruction_baseline_sha=BASELINE,provenance='controlled reconstruction; missing f002cc1 not recovered; historical 29-test claim not verified',
            sensitivity_failure_protocol=config['sensitivity_failure_protocol'],context_qa=context_qa,panel_qa=panel_qa,
            layer_a_descriptive=descriptives,model_meta=meta,primary_holm_rejections=int(primary.holm_reject.sum()),
            input_hashes=hashes,code_hashes={p:sha256(repo/p) for p in code_paths if (repo/p).exists()},
            environment=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,pyarrow=pyarrow.__version__,
                geopandas=gpd.__version__,statsmodels=statsmodels.__version__,matplotlib=matplotlib.__version__),
            production_parquet_runner_executed=True,causal_interpretation=False,station_risk_classification=False)
        root=repo/'subway'
        with tempfile.TemporaryDirectory(prefix='.spatial-staging-',dir=root/'data') as td:
            stage=Path(td)
            for folder in ['tables','models','figures']:(stage/folder).mkdir()
            for name,frame,sort in [
                ('spatial_context_2024.csv',dong,['ADM_CD']),('station_spatial_context_2024.csv',station,['canonical_station_id']),
                ('shelter_mapping_exceptions.csv',exceptions,['mapping_status','source_row_id']),('station_extreme_heterogeneity.csv',layer_a,['canonical_station_id'])]:
                _csv(stage/'tables'/name,frame,sort)
            _csv(stage/'models/spatial_moderation_primary.csv',primary,['term'])
            _csv(stage/'models/spatial_moderation_sensitivity.csv',sensitivity,['term'])
            geo=boundary[['ADM_CD','geometry']].merge(dong,on='ADM_CD',validate='one_to_one')
            render_spatial_figures(geo,station,layer_a,primary,stage/'figures')
            for path,value in hashes.items():
                if sha256(resolve_repo_relative(repo,path))!=value:raise ValueError('accepted prior-stage input changed during execution')
            summary['output_hashes']={f'subway/results/{p.relative_to(stage).as_posix()}':sha256(p)
                for p in sorted(stage.rglob('*')) if p.is_file()}
            _json(stage/'models/spatial_moderation_summary.json',summary)
            # No gate or result generation remains after publication begins.
            for source in sorted(stage.rglob('*')):
                if source.is_file():
                    target=root/'results'/source.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True)
                    os.replace(source,target)
        print('Stage3C technical execution COMPLETE; sensitivity '+meta['sensitivity']['inference_status']+'; human scientific review PENDING')
        print(json.dumps(dict(context=context_qa,panel=panel_qa),ensure_ascii=True))
        return 0
    except Exception as exc:
        logs=repo/'subway/logs';logs.mkdir(parents=True,exist_ok=True)
        with (logs/'run_spatial_heterogeneity.log').open('a',encoding='utf-8') as log:log.write(traceback.format_exc()+'\n')
        print(f'Stage3C BLOCKED: {type(exc).__name__}; inspect subway/logs/run_spatial_heterogeneity.log',file=sys.stderr)
        return 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--year',type=int,required=True)
    return run_spatial_heterogeneity(ROOT,parser.parse_args(argv).year)


if __name__=='__main__':raise SystemExit(main())
