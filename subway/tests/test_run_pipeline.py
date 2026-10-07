import json
import shutil
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import pandas as pd
import yaml
from subway.run_pipeline import run_pipeline,main,_build_products
from subway.src.ingest.schema_inspector import inspect_primary_file
from subway.src.validate.raw_validation import Finding

REPO=Path(__file__).resolve().parents[2]


def fixture(root):
    """Real Tasks1–9 on two transport identities; existing reference inputs retained."""
    shutil.copytree(REPO/'subway/config',root/'subway/config')
    shutil.copytree(REPO/'subway/data/validation',root/'subway/data/validation',ignore=shutil.ignore_patterns('pipeline_*','data_quality_report.csv','join_report.csv','exceptions_*.csv'))
    manifest=pd.read_csv(REPO/'subway/data_manifest.csv',dtype=str,keep_default_na=False)
    contracts=yaml.safe_load((root/'subway/config/source_contracts_2024.yaml').read_text(encoding='utf-8'))
    for row in manifest.itertuples():
        folder=REPO/row.raw_path
        for source in folder.parent.iterdir():
            if source.is_file():
                target=root/source.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for dataset in ['senior_ridership','total_ridership','station']:
        row=manifest[manifest.dataset_id.eq(dataset)].iloc[0];path=root/row.raw_path
        raw=pd.read_csv(path,encoding='cp949',dtype=str,keep_default_na=False)
        raw=raw[raw['역명'].isin(['종각','지축'])].copy()
        if dataset!='station':
            for column in yaml.safe_load((root/'subway/config/validation_rules.yaml').read_text(encoding='utf-8'))['ridership']['time_bins'][dataset]:
                raw[column]='1' if dataset=='senior_ridership' else '2'
        raw.to_csv(path,index=False,encoding='cp949',lineterminator='\n')
        contracts['contracts'][dataset]['row_count']=len(raw)
    (root/'subway/config/source_contracts_2024.yaml').write_text(yaml.safe_dump(contracts,allow_unicode=True),encoding='utf-8')
    inventory=pd.read_csv(root/'subway/data/validation/raw_inventory.csv',dtype=str)
    for index,row in inventory.iterrows():
        path=root/'subway/data/raw/2024'/row.dataset_id/row.relative_path
        inventory.loc[index,'sha256']=hashlib.sha256(path.read_bytes()).hexdigest();inventory.loc[index,'size_bytes']=str(path.stat().st_size)
    inventory.to_csv(root/'subway/data/validation/raw_inventory.csv',index=False)
    snapshot={}
    for index,row in manifest.iterrows():
        path=root/row.raw_path;manifest.loc[index,'sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot[row.dataset_id+'/'+path.name]=inspect_primary_file(path)
    manifest.to_csv(root/'subway/data_manifest.csv',index=False)
    (root/'subway/data/validation/raw_schema_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
    baseline=yaml.safe_load((root/'subway/config/pipeline_baseline_2024.yaml').read_text(encoding='utf-8'))
    baseline['accepted_hashes']={}
    baseline['task5']=dict(station_identities=2,status_counts=dict(ELIGIBLE=2,ELIGIBLE_CODE_WARNING=0,EXCLUDED_IDENTITY=0,EXCLUDED_COORDINATE=0,EXCLUDED_TEMPORAL=0))
    baseline['task8']=dict(integrated_rows=29280,matched=29280,total_only=0,senior_only=0,ambiguous_rejected=0,senior_excess=0)
    baseline['task9']=dict(eligible=2,MAPPED=1,ZERO_MATCH=1,BOUNDARY_POINT=0,MULTIPLE_MATCH=0)
    (root/'subway/config/pipeline_baseline_2024.yaml').write_text(yaml.safe_dump(baseline),encoding='utf-8')
    return root


class RunPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=TemporaryDirectory();cls.template=fixture(Path(cls.base.name)/'template')
    @classmethod
    def tearDownClass(cls):cls.base.cleanup()
    def setUp(self):
        self.temp=TemporaryDirectory();self.repo=Path(self.temp.name)/'repo';shutil.copytree(self.template,self.repo)
    def tearDown(self):self.temp.cleanup()
    def summary(self):return json.loads((self.repo/'subway/data/validation/pipeline_summary.json').read_text(encoding='utf-8'))
    def raw_hashes(self):return {p.relative_to(self.repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.repo/'subway/data/raw').rglob('*') if p.is_file()}

    def test_one_command_real_flow_outputs_core_scope_and_primary_population(self):
        before=self.raw_hashes();self.assertEqual(run_pipeline(self.repo,2024),0);s=self.summary()
        self.assertEqual(len(s['clean_outputs']),7);self.assertEqual(len(s['processed_outputs']),4)
        self.assertEqual(len(s['validation_outputs']),6);self.assertEqual(s['finding_counts']['ERROR'],0)
        self.assertEqual(before,self.raw_hashes());self.assertEqual(s['task8']['integrated_rows'],29280)
        core=pd.read_parquet(self.repo/'subway/data/processed/ridership_2024.parquet')
        self.assertEqual(core.canonical_station_id.nunique(),2)
        master=pd.read_parquet(self.repo/'subway/data/processed/station_master.parquet');self.assertEqual(len(master),2)
        m=pd.read_parquet(self.repo/'subway/data/processed/station_dong_map.parquet')
        self.assertEqual(m.mapping_status.value_counts().to_dict(),{'MAPPED':1,'ZERO_MATCH':1})
        self.assertEqual(m.study_area_status.value_counts().to_dict(),{'IN_CURRENT_STUDY_AREA':1,'OUTSIDE_CURRENT_STUDY_AREA':1})
        self.assertTrue(m.loc[m.mapping_status.ne('MAPPED'),'ADM_CD'].isna().all())
        population=pd.read_parquet(self.repo/'subway/data/clean/population_2024q2.parquet')
        self.assertEqual(population.source_dataset_id.unique().tolist(),['population_direct_65_plus'])
        self.assertNotIn(str(self.repo),json.dumps(s));self.assertTrue(s['publication']['used_staging'])
        quality=pd.read_csv(self.repo/'subway/data/validation/data_quality_report.csv')
        self.assertFalse(quality.message.str.contains('Task 9 blocked',regex=False).any())
        self.assertIn('supplementary_population_diagnostics',s)

    def test_repeat_and_reversed_frame_order_same_hashes_no_network(self):
        self.assertEqual(run_pipeline(self.repo,2024),0);before=self.summary()['output_hashes']
        def reverse(*args):
            products,summary,findings=_build_products(*args)
            return {k:v.iloc[::-1] for k,v in products.items()},summary,findings
        with patch('subway.run_pipeline._build_products',side_effect=reverse),patch('socket.socket',side_effect=AssertionError('no network')):
            self.assertEqual(run_pipeline(self.repo,2024),0)
        self.assertEqual(before,self.summary()['output_hashes'])

    def test_missing_raw_after_success_no_stale_success_or_partial_publication(self):
        self.assertEqual(run_pipeline(self.repo,2024),0);before={p:p.read_bytes() for p in (self.repo/'subway/data/processed').iterdir()}
        raw=next((self.repo/'subway/data/raw/2024/weather').glob('*.csv'));raw.unlink()
        self.assertNotEqual(run_pipeline(self.repo,2024),0);s=self.summary()
        self.assertEqual(s['status'],'PIPELINE FAILED');self.assertEqual(s['output_hashes'],{})
        self.assertFalse(s['publication']['published']);self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertTrue((self.repo/'subway/data/validation/pipeline_failure/data_quality_report.csv').exists())

    def test_missing_schema_failure_diagnostics_are_portable(self):
        self.assertEqual(run_pipeline(self.repo,2024),0)
        (self.repo/'subway/data/validation/raw_schema_snapshot.json').unlink()
        self.assertNotEqual(run_pipeline(self.repo,2024),0)
        self.assertEqual(self.summary()['output_hashes'],{})
        diagnostic=self.repo/'subway/data/validation/pipeline_failure/data_quality_report.csv'
        quality=pd.read_csv(diagnostic)
        self.assertIn('CONFIGURATION_ERROR',set(quality.code))
        for path in [diagnostic,self.repo/'subway/data/validation/pipeline_summary.json']:
            text=path.read_text(encoding='utf-8')
            self.assertNotIn(str(self.repo),text)
            self.assertNotIn(str(self.repo).replace('\\','\\\\'),text)
            self.assertNotRegex(text,r'[A-Za-z]:[\\/]')
        self.assertIn('subway/data/validation/raw_schema_snapshot.json',diagnostic.read_text(encoding='utf-8'))

    def test_unknown_year_fails_safely(self):
        self.assertNotEqual(run_pipeline(self.repo,2025),0);self.assertEqual(self.summary()['output_hashes'],{})
        self.assertFalse((self.repo/'subway/data/processed').exists())

    def test_baseline_drift_blocks_publish(self):
        path=self.repo/'subway/config/pipeline_baseline_2024.yaml';b=yaml.safe_load(path.read_text());b['task8']['integrated_rows']+=1;path.write_text(yaml.safe_dump(b))
        self.assertNotEqual(run_pipeline(self.repo,2024),0)
        self.assertIn('BASELINE_REGRESSION',set(pd.read_csv(self.repo/'subway/data/validation/pipeline_failure/data_quality_report.csv').code))
        self.assertFalse((self.repo/'subway/data/processed').exists())

    def test_blocking_stage_result_prevents_all_publication(self):
        with patch('subway.run_pipeline.preflight',return_value=[Finding('ERROR','fixture','BLOCK','block')]):
            self.assertNotEqual(run_pipeline(self.repo,2024),0)
        self.assertFalse((self.repo/'subway/data/clean').exists());self.assertEqual(self.summary()['output_hashes'],{})

    def test_publish_io_failure_rolls_back_previous_complete_generation(self):
        import os
        self.assertEqual(run_pipeline(self.repo,2024),0)
        prior={p:p.read_bytes() for directory in ['clean','processed'] for p in (self.repo/'subway/data'/directory).iterdir()}
        real=os.replace;count=[0]
        def fail_once(source,destination):
            if str(source).endswith('.parquet') and '.pipeline-staging-' in str(source) and Path(source).parent.name!='serialize':
                count[0]+=1
                if count[0]==2:raise OSError('fixture publication failure')
            return real(source,destination)
        with patch('subway.run_pipeline.os.replace',side_effect=fail_once):self.assertNotEqual(run_pipeline(self.repo,2024),0)
        self.assertEqual(prior,{p:p.read_bytes() for p in prior});self.assertEqual(self.summary()['output_hashes'],{})

    def test_main_cli_defaults_to_configured_profile(self):
        with patch('subway.run_pipeline.run_pipeline',return_value=0) as run:
            self.assertEqual(main(['--year','2024']),0);self.assertEqual(run.call_args.args[1],2024)

    def test_late_file_exists_error_is_failed_run_not_previous_success(self):
        self.assertEqual(run_pipeline(self.repo,2024),0)
        with patch('subway.run_pipeline._publish',side_effect=FileExistsError('late publication failure')):
            self.assertNotEqual(run_pipeline(self.repo,2024),0)
        self.assertEqual(self.summary()['status'],'PIPELINE FAILED');self.assertEqual(self.summary()['output_hashes'],{})

    def test_existing_writer_lock_leaves_its_summary_untouched(self):
        self.assertEqual(run_pipeline(self.repo,2024),0);path=self.repo/'subway/data/validation/pipeline_summary.json';before=path.read_bytes()
        (self.repo/'subway/data/.pipeline.lock').write_text('other writer')
        self.assertNotEqual(run_pipeline(self.repo,2024),0);self.assertEqual(path.read_bytes(),before)


class ArtifactCRSTests(unittest.TestCase):
    def test_plain_crs_column_is_not_a_geodataframe(self):
        from subway.src.utils.artifacts import write_artifacts
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            f=pd.DataFrame(dict(id=['a'],crs=['EPSG:4326']))
            write_artifacts(Path(tmp),{'master.parquet':f},{},sort_columns={'master.parquet':['id']})
            pd.testing.assert_frame_equal(pd.read_parquet(Path(tmp)/'master.parquet'),f)


if __name__=='__main__':unittest.main()
