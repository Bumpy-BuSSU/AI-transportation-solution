"""Reproduce approved-input, descriptive subway Stage3A artifacts."""
from pathlib import Path
import argparse,gc,hashlib,json,os,platform,sys,tempfile,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import pyarrow
import matplotlib
from subway.src.analysis.eda import build_eda
from subway.src.analysis.figures import render_figures
from subway.src.utils.artifacts import write_artifacts,_check_metadata
from subway.src.utils.paths import resolve_repo_relative
from subway.src.transform.ridership import KEYS

INPUTS=['processed/ridership_2024.parquet','processed/station_master.parquet','processed/station_dong_map.parquet','clean/weather_2024.parquet']
SORTS={'eda_sample_accounting.csv':['stage'],'eda_weather_summary.csv':['variable'],
    'eda_exclusions.csv':['stage','reason'],
    'eda_temperature_quantiles.csv':['variable','percentile'],'eda_count_diagnostics.csv':['age_group'],
    'eda_daily_age_weather.csv':['date'],'eda_calendar_profile.csv':['weekend'],
    'eda_hourly_profile.csv':['hour_order','boarding_type'],'eda_station_summary.csv':['canonical_station_id'],
    'eda_station_distribution.csv':['variable'],'eda_temperature_profiles.csv':['weather_variable','temperature_bin']}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run_eda(repo_root: Path,year: int) -> int:
    repo=Path(repo_root).resolve();data=repo/'subway/data'
    try:
        if year!=2024:raise ValueError('only approved2024 baseline currently implemented')
        if any(not (data/p).exists() for p in INPUTS):
            from subway.run_pipeline import run_pipeline
            if run_pipeline(repo,year):raise ValueError('Stage2 regeneration blocked')
        summary_path=data/'validation/pipeline_summary.json';baseline=json.loads(summary_path.read_text(encoding='utf-8'))
        baseline_hash=sha(summary_path)
        if baseline.get('year')!=year or baseline.get('status') not in ['PIPELINE PASSED','PIPELINE PASSED WITH WARNINGS']:raise ValueError('Stage2 success required')
        for path in INPUTS:
            if baseline['output_hashes'].get(path)!=sha(data/path):raise ValueError('Stage2 input hash mismatch: '+path)
        input_hashes={'subway/data/'+p:baseline['output_hashes'][p] for p in INPUTS}
        columns=KEYS+['hour_start','hour_end','senior','total','non_senior','senior_share','join_status','exception_code']
        core=pd.read_parquet(data/INPUTS[0],columns=columns)
        master=pd.read_parquet(data/INPUTS[1],columns=['canonical_station_id','study_area_status','spatial_status'])
        mapping=pd.read_parquet(data/INPUTS[2],columns=['canonical_station_id','study_area_status','mapping_status','ADM_CD'])
        weather=pd.read_parquet(data/INPUTS[3])
        base,tables,summary=build_eda(core,master,mapping,weather,year)
        del core,master,mapping,weather;gc.collect()
        summary.update(input_hashes=input_hashes,stage2_summary_sha256=baseline_hash,
            code_hashes={p:sha(ROOT/p) for p in ['subway/run_eda.py','subway/src/analysis/eda.py','subway/src/analysis/figures.py']},
            stage2_reference='subway/data/validation/pipeline_summary.json',
            environment=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,pyarrow=pyarrow.__version__,matplotlib=matplotlib.__version__),
            analysis_base='subway/data/analysis/analysis_base_2024.parquet',analysis_base_rows=len(base),
            table_rows={name:len(frame) for name,frame in tables.items()})
        _check_metadata(summary)
        data.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.eda-staging-',dir=data) as temporary:
            stage=Path(temporary)
            write_artifacts(stage/'tables',tables,{},sort_columns=SORTS)
            (stage/'tables/pipeline_summary.json').unlink()
            write_artifacts(stage/'analysis',{'analysis_base_2024.parquet':base},{},sort_columns={'analysis_base_2024.parquet':KEYS})
            (stage/'analysis/pipeline_summary.json').unlink();del base;gc.collect()
            figures=render_figures(tables,stage/'figures')
            staged={**{'subway/results/tables/'+n:stage/'tables'/n for n in tables},
                **{'subway/results/figures/'+n:stage/'figures'/n for n in figures},
                summary['analysis_base']:stage/'analysis/analysis_base_2024.parquet'}
            summary['output_hashes']={relative:sha(path) for relative,path in sorted(staged.items())}
            for relative,digest in input_hashes.items():
                if sha(resolve_repo_relative(repo,relative))!=digest:raise ValueError('Stage2 input changed during EDA')
            if sha(summary_path)!=baseline_hash:raise ValueError('Stage2 summary changed during EDA')
            _check_metadata(summary)
            candidate=stage/'eda_summary.json';candidate.write_text(json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
            for relative,path in staged.items():
                target=resolve_repo_relative(repo,relative);target.parent.mkdir(parents=True,exist_ok=True);os.replace(path,target)
            target=repo/'subway/results/tables/eda_summary.json';os.replace(candidate,target)
        print('Stage3A EDA COMPLETE; descriptive only; threshold/model review PENDING')
        return 0
    except Exception as exc:
        logs=repo/'subway/logs';logs.mkdir(parents=True,exist_ok=True)
        with (logs/'run_eda.log').open('a',encoding='utf-8') as log:log.write(traceback.format_exc()+'\n')
        print(f'EDA BLOCKED: {type(exc).__name__}; inspect runtime log',file=sys.stderr)
        return 1


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--year',type=int,required=True)
    return run_eda(ROOT,parser.parse_args(argv).year)


if __name__=='__main__':raise SystemExit(main())
