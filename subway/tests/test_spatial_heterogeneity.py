"""Reconstructed Stage3C scientific contracts; expectations come from fixtures."""
from pathlib import Path
import copy
import importlib
import json
import hashlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, box
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

ROOT = Path(__file__).resolve().parents[2]


def annual_panel():
    dates = pd.date_range('2024-01-01', '2024-12-31')
    frame = pd.MultiIndex.from_product([range(8), dates], names=['canonical_station_id', 'date']).to_frame(index=False)
    frame['ADM_CD'] = (frame.canonical_station_id // 2).astype(str)
    frame['month'] = frame.date.dt.month
    frame['dow'] = frame.date.dt.dayofweek
    t = frame.date.dt.dayofyear.to_numpy()
    frame['hot_primary'] = (t % 9 == 0).astype(int)
    frame['cold_primary'] = (t % 11 == 0).astype(int)
    frame['hot_sensitivity'] = (t % 18 == 0).astype(int)
    frame['cold_sensitivity'] = (t % 22 == 0).astype(int)
    frame['z_senior_population_share'] = frame.canonical_station_id.map(dict(enumerate([-1,-1,-.2,-.2,.3,.3,1.2,1.2])))
    frame['z_shelters_per_10k'] = frame.canonical_station_id.map(dict(enumerate([.5,.5,-1,-1,1.3,1.3,-.4,-.4])))
    frame['log_ratio'] = (.03 * frame.hot_primary * frame.z_senior_population_share
                          - .02 * frame.cold_primary * frame.z_senior_population_share
                          + .04 * frame.hot_primary * frame.z_shelters_per_10k
                          + .01 * frame.cold_primary * frame.z_shelters_per_10k
                          + .2 * frame.canonical_station_id + np.sin(t / 20)
                          + np.random.default_rng(482).normal(0, .01, len(frame)))
    return frame


def spatial_fixture():
    boundary = gpd.GeoDataFrame(dict(ADM_CD=['a','b','c','d'], gu=['g']*4, dong=list('abcd'),
        population_total=[100,200,300,400], population_65_plus=[10,40,90,160],
        senior_population_share=[.1,.2,.3,.4]), geometry=[box(i*100,0,i*100+90,90) for i in range(4)], crs=5179)
    stations = pd.DataFrame(dict(canonical_station_id=['s0','s1','s2','s3','s4'],
        ADM_CD=['a','a','b','c','d'], mapping_status=['MAPPED']*5,
        study_area_status=['IN_CURRENT_STUDY_AREA']*5, x_5179=[20,30,120,220,320], y_5179=[20]*5))
    shelters = gpd.GeoDataFrame(dict(source_row_id=[1,2]), geometry=[Point(10,10),Point(110,10)],crs=5179).to_crs(5186)
    return stations,boundary,shelters


class SpatialContracts(unittest.TestCase):
    def setUp(self):
        try:
            self.m = importlib.import_module('subway.src.analysis.spatial_heterogeneity')
        except ModuleNotFoundError:
            self.fail('Stage3C reconstruction module is not implemented')

    def test_config_drift_and_stage3b_threshold_continuity(self):
        config = self.m.load_spatial_heterogeneity_config(ROOT,2024)
        old = __import__('yaml').safe_load((ROOT/'subway/config/confirmatory_analysis_2024.yaml').read_text(encoding='utf-8'))
        for name in ['hot_primary','cold_primary','hot_sensitivity','cold_sensitivity']:
            self.assertEqual(config[name],old[name])
        for key,value in [('use_correction',True),('moderators',['nearest_shelter_distance_m']),('primary_event','alighting')]:
            bad=copy.deepcopy(config);bad[key]=value
            with self.assertRaises(ValueError):self.m.validate_spatial_heterogeneity_config(bad,2024)
        bad=copy.deepcopy(config);bad['hot_primary']['threshold_c']=33
        with self.assertRaises(ValueError):self.m.validate_spatial_heterogeneity_config(bad,2024)

    def test_context_uses_unique_dongs_and_preserves_inputs(self):
        s,b,h=spatial_fixture();before=s.copy(deep=True)
        dong,station,exceptions,qa=self.m.build_spatial_context(s,b,h,{})
        self.assertEqual(dong.mapped_shelter_count.tolist(),[1,1,0,0])
        self.assertAlmostEqual(dong.shelters_per_10k.iloc[0],100)
        unique=station.drop_duplicates('ADM_CD')
        for col in ['z_senior_population_share','z_shelters_per_10k']:
            self.assertAlmostEqual(unique[col].mean(),0)
            self.assertAlmostEqual(unique[col].std(ddof=1),1)
        self.assertEqual(qa['mapped_shelters'],2);self.assertTrue(exceptions.empty)
        pd.testing.assert_frame_equal(s,before)
        again=self.m.build_spatial_context(s.iloc[::-1],b.iloc[::-1],h.iloc[::-1],{})
        pd.testing.assert_frame_equal(station,again[1])

    def test_shelter_exceptions_are_not_repaired_and_distance_uses_unmapped(self):
        s,b,h=spatial_fixture()
        h=gpd.GeoDataFrame(dict(source_row_id=[1,2,3]),geometry=[Point(0,20),Point(500,10),Point(320,10)],crs=5179).to_crs(5186)
        # Exact boundary coordinates tested in the working projected CRS, avoiding reprojection rounding.
        h=h.to_crs(5179);h.geometry=[Point(0,20),Point(500,10),Point(320,10)]
        dong,station,exceptions,qa=self.m.build_spatial_context(s,b,h,{'shelter_crs':'EPSG:5179'})
        self.assertEqual(set(exceptions.mapping_status),{'BOUNDARY_POINT','ZERO_MATCH'})
        self.assertEqual(qa['mapped_shelters'],1)
        self.assertAlmostEqual(station.loc[station.canonical_station_id.eq('s0'),'nearest_shelter_distance_m'].iloc[0],20)
        self.assertEqual(int(dong.mapped_shelter_count.sum()),1)

    def test_context_invalid_crs_population_and_constant_moderator_block(self):
        s,b,h=spatial_fixture()
        with self.assertRaises(ValueError):self.m.build_spatial_context(s,b,h.to_crs(4326),{})
        b.loc[0,'population_total']=0
        with self.assertRaises(ValueError):self.m.build_spatial_context(s,b,h,{})
        s,b,h=spatial_fixture();b['population_65_plus']=b.population_total*.2;b['senior_population_share']=.2
        with self.assertRaises(ValueError):self.m.build_spatial_context(s,b,h,{})

    def base_fixture(self):
        dates=pd.date_range('2024-01-01','2024-12-31')
        base=pd.DataFrame(dict(date=dates,canonical_station_id=['s']*366,boarding_type=['boarding']*366,
            hour_bin=['10_11']*366,senior=[2]*366,total=[10]*366,non_senior=[8]*366,
            age_comparison_valid=[True]*366,temperature_max=[33]*366,temperature_min=[-4]*366))
        bad=base.iloc[[0]].copy();bad['senior']=187;bad['total']=106;bad['non_senior']=np.nan;bad['age_comparison_valid']=False;bad['hour_bin']='21_22'
        alight=base.copy();alight['boarding_type']='alighting';alight['senior']=100
        context=pd.DataFrame(dict(canonical_station_id=['s'],ADM_CD=['a'],z_senior_population_share=[0.],z_shelters_per_10k=[0.]))
        return pd.concat([base,bad,alight],ignore_index=True),context

    def test_panel_common_support_and_boarding_only(self):
        base,context=self.base_fixture();before=base.copy(deep=True)
        cfg=self.m.load_spatial_heterogeneity_config(ROOT,2024)
        out=self.m.build_station_day_panel(base,context,cfg,2024)
        self.assertEqual(len(out),366);self.assertEqual(out.senior.sum(),732);self.assertEqual(out.non_senior.sum(),2928)
        self.assertEqual(out.support_cells.sum(),366)
        self.assertTrue(out.hot_primary.eq(1).all());self.assertTrue(out.cold_primary.eq(1).all())
        self.assertTrue(out.hot_sensitivity.eq(0).all());self.assertTrue(out.cold_sensitivity.eq(0).all())
        pd.testing.assert_frame_equal(base,before)

    def test_panel_zero_missing_duplicate_and_false_validity_block(self):
        base,context=self.base_fixture();cfg=self.m.load_spatial_heterogeneity_config(ROOT,2024)
        for kind in ['zero','missing','duplicate','invalid']:
            bad=base.copy(deep=True)
            if kind=='zero':bad.loc[0,'senior']=0;bad.loc[0,'non_senior']=10
            if kind=='missing':bad=bad.loc[~bad.date.eq(pd.Timestamp('2024-01-02'))]
            if kind=='duplicate':bad=pd.concat([bad,bad.iloc[[0]]])
            if kind=='invalid':bad.loc[366,'age_comparison_valid']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.m.build_station_day_panel(bad,context,cfg,2024)

    def test_panel_entire_invalid_station_cannot_disappear_from_required_population(self):
        base,context=self.base_fixture();cfg=self.m.load_spatial_heterogeneity_config(ROOT,2024)
        excluded=base.copy(deep=True);excluded['canonical_station_id']='excluded';excluded['age_comparison_valid']=False
        second=context.copy(deep=True);second['canonical_station_id']='excluded'
        with self.assertRaisesRegex(ValueError,'required station'):
            self.m.build_station_day_panel(pd.concat([base,excluded],ignore_index=True),pd.concat([context,second],ignore_index=True),cfg,2024)

    def test_layer_a_matches_explicit_ols_and_has_no_station_inference(self):
        panel=annual_panel();out=self.m.fit_station_heterogeneity(panel)
        sample=panel.loc[panel.canonical_station_id.eq(0)]
        x=pd.concat([pd.Series(1.,index=sample.index,name='constant'),sample[['hot_primary','cold_primary']],
            pd.get_dummies(sample.month,drop_first=True,dtype=float),pd.get_dummies(sample.dow,drop_first=True,dtype=float)],axis=1)
        expected=sm.OLS(sample.log_ratio,x).fit().params.iloc[1:3].to_numpy()
        np.testing.assert_allclose(out.iloc[0][['beta_hot','beta_cold']].to_numpy(float),expected,atol=1e-12)
        self.assertEqual(len(out),8);self.assertTrue(out.valid_days.eq(366).all())
        self.assertFalse(any('p_value' in c or 'reject' in c or 'signif' in c for c in out.columns))

    def test_absorbed_fe_matches_explicit_fe_slopes(self):
        panel=annual_panel().loc[lambda x:x.date.le('2024-03-10')].reset_index(drop=True)
        design=self.m.design_spatial_moderation(panel,hot='hot_primary',cold='cold_primary')
        f=pd.concat([panel[['canonical_station_id','date','log_ratio']],design],axis=1)
        absorbed=self.m.absorb_station_date_fe(f,['log_ratio']+list(design))
        actual=sm.OLS(absorbed.log_ratio,absorbed[design.columns]).fit().params
        explicit=pd.concat([design,pd.get_dummies(panel.canonical_station_id,prefix='station',drop_first=True,dtype=float),
            pd.get_dummies(panel.date,prefix='date',drop_first=True,dtype=float)],axis=1)
        expected=sm.OLS(panel.log_ratio,sm.add_constant(explicit)).fit().params[design.columns]
        np.testing.assert_allclose(actual,expected,atol=2e-12)

    def test_covariance_matches_frozen_two_way_library_without_correction(self):
        panel=annual_panel();table,meta=self.m.fit_spatial_moderation(panel,hot='hot_primary',cold='cold_primary',threshold_label='p90/p10')
        x=self.m.design_spatial_moderation(panel,hot='hot_primary',cold='cold_primary')
        a=self.m.absorb_station_date_fe(pd.concat([panel[['canonical_station_id','date','log_ratio']],x],axis=1),['log_ratio']+list(x))
        fit=sm.OLS(a.log_ratio,a[x.columns]).fit()
        cov=cov_cluster_2groups(fit,pd.factorize(panel.ADM_CD)[0],pd.factorize(panel.date)[0],use_correction=False)[0]
        np.testing.assert_allclose(meta['raw_target_variances'],np.diag(cov)[:4],rtol=1e-10,atol=1e-15)
        np.testing.assert_allclose(table.beta,fit.params.iloc[:4],atol=1e-12)
        np.testing.assert_allclose(table.se,np.sqrt(np.diag(cov)[:4]),rtol=1e-10)
        self.assertEqual(meta['cluster_counts'],{'ADM_CD':4,'date':366})
        self.assertFalse(meta['use_correction'])

    def test_primary_four_test_holm_family_and_row_order(self):
        panel=annual_panel();p,s,meta=self.m.fit_stage3c_models(panel)
        self.assertEqual(len(p),4);self.assertEqual(len(s),4)
        from subway.src.analysis.confirmatory import holm_adjust
        np.testing.assert_allclose(p.p_holm,holm_adjust(p.p_raw.tolist()))
        self.assertTrue((p.p_holm>=p.p_raw).all());self.assertEqual(meta['primary_test_count'],4)
        again=self.m.fit_stage3c_models(panel.iloc[::-1])[0]
        pd.testing.assert_frame_equal(p,again)

    def test_rank_deficiency_and_unbalanced_fe_block(self):
        panel=annual_panel();bad=panel.copy();bad['z_shelters_per_10k']=bad.z_senior_population_share
        with self.assertRaises(ValueError):self.m.fit_stage3c_models(bad)
        with self.assertRaises(ValueError):self.m.absorb_station_date_fe(panel.iloc[1:],['log_ratio'])

    def test_invalid_sensitivity_suppresses_entire_layer_and_retains_raw_covariance(self):
        panel=annual_panel()
        # Covariance is the scientific gate boundary; point fitting remains real OLS.
        original=self.m.cov_cluster_2groups
        calls=[]
        def invalid(fit,group1,group2,*,use_correction):
            calls.append(use_correction)
            cov=original(fit,group1,group2,use_correction=use_correction)
            raw=cov[0].copy();raw[np.arange(4),np.arange(4)]=[-.1,-.2,-.3,.4]
            return raw,cov[1],cov[2]
        expected=self.m.fit_spatial_moderation(panel,hot='hot_sensitivity',cold='cold_sensitivity',threshold_label='p95/p05')[0].beta
        with patch.object(self.m,'cov_cluster_2groups',side_effect=invalid):
            out,meta=self.m.fit_spatial_moderation(panel,hot='hot_sensitivity',cold='cold_sensitivity',threshold_label='p95/p05')
        np.testing.assert_allclose(out.beta,expected,atol=0)
        self.assertEqual(calls,[False])
        self.assertTrue(out.inference_status.eq('NOT ESTIMABLE').all())
        self.assertTrue(out.failure_reason.eq('NOT_ESTIMABLE_INVALID_TWOWAY_COVARIANCE').all())
        self.assertTrue(out[['se','ci95_low','ci95_high','p_raw','p_holm','holm_reject']].isna().all().all())
        self.assertEqual(meta['negative_target_variance_count'],3)
        self.assertEqual(meta['raw_target_variances'],[-.1,-.2,-.3,.4])
        self.assertFalse(meta['covariance_repaired']);self.assertFalse(meta['covariance_fallback_used'])
        with tempfile.TemporaryDirectory() as td:
            from subway.run_confirmatory import _csv,_json
            _csv(Path(td)/'s.csv',out,['term']);_json(Path(td)/'s.json',meta)
            restored=pd.read_csv(Path(td)/'s.csv')
            self.assertTrue(restored.se.isna().all())
            self.assertTrue(restored.failure_reason.eq('NOT_ESTIMABLE_INVALID_TWOWAY_COVARIANCE').all())
            self.assertEqual(json.loads((Path(td)/'s.json').read_text())['negative_target_variance_count'],3)

    def test_invalid_primary_covariance_blocks_instead_of_using_sensitivity_rule(self):
        panel=annual_panel();n=38
        def invalid(fit,*args,**kwargs):
            c=np.eye(len(fit.params));c[0,0]=-1;return c,c,c
        with patch.object(self.m,'cov_cluster_2groups',side_effect=invalid),self.assertRaises(ValueError):
            self.m.fit_spatial_moderation(panel,hot='hot_primary',cold='cold_primary',threshold_label='p90/p10')


class RunnerContracts(unittest.TestCase):
    def runner(self):
        try:return importlib.import_module('subway.run_spatial_heterogeneity')
        except ModuleNotFoundError:self.fail('Stage3C staged production runner is not implemented')

    def fixture(self,repo):
        for folder in ['config','data/analysis','data/processed','data/clean','data/validation','results/models','results/tables']:
            (repo/'subway'/folder).mkdir(parents=True,exist_ok=True)
        for name in ['spatial_heterogeneity_2024.yaml','confirmatory_analysis_2024.yaml']:
            shutil.copyfile(ROOT/'subway/config'/name,repo/'subway/config'/name)
        config=__import__('yaml').safe_load((repo/'subway/config/spatial_heterogeneity_2024.yaml').read_text())
        config.update(expected_stations=8,expected_station_dongs=4,expected_seoul_dongs=4)
        panel=annual_panel();s,b,h=spatial_fixture()
        s=pd.DataFrame(dict(canonical_station_id=list(range(8)),ADM_CD=np.repeat(list('abcd'),2),mapping_status=['MAPPED']*8,
            study_area_status=['IN_CURRENT_STUDY_AREA']*8,x_5179=np.repeat([20,120,220,320],2),y_5179=[20]*8))
        s.canonical_station_id=s.canonical_station_id.astype(str)
        base=panel[['canonical_station_id','date','log_ratio']].copy();base.canonical_station_id=base.canonical_station_id.astype(str)
        base['senior']=np.rint(10000*np.exp(base.log_ratio));base['non_senior']=10000.;base['total']=base.senior+base.non_senior
        base['hour_bin']='10_11';base['boarding_type']='boarding';base['age_comparison_valid']=True
        base['temperature_max']=np.where(panel.hot_sensitivity,34,np.where(panel.hot_primary,33,20))
        base['temperature_min']=np.where(panel.cold_sensitivity,-5,np.where(panel.cold_primary,-4,10))
        paths={'processed/station_dong_map.parquet':s,'processed/dong_population_2024q2.parquet':b,'clean/climate_shelters.parquet':h,'analysis/analysis_base_2024.parquet':base}
        for path,frame in paths.items():frame.to_parquet(repo/'subway/data'/path,index=False)
        sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        def write(path,data):path.write_text(json.dumps(data),encoding='utf-8')
        write(repo/'subway/data/validation/pipeline_summary.json',{'status':'PIPELINE COMPLETE','output_hashes':{p:sha(repo/'subway/data'/p) for p in paths if not p.startswith('analysis/')}})
        base_hash=sha(repo/'subway/data/analysis/analysis_base_2024.parquet')
        write(repo/'subway/results/tables/eda_summary.json',{'status':'EDA COMPLETE','output_hashes':{'subway/data/analysis/analysis_base_2024.parquet':base_hash}})
        write(repo/'subway/results/models/confirmatory_summary.json',{'status':'CONFIRMATORY H1/H2 COMPLETE','analysis_base_sha256':base_hash,'config_sha256':sha(repo/'subway/config/confirmatory_analysis_2024.yaml')})
        return config

    def test_figures_use_three_frozen_outputs_and_full_primary_uncertainty(self):
        try:figures=importlib.import_module('subway.src.analysis.spatial_figures')
        except ModuleNotFoundError:self.fail('Stage3C three-figure contract is not implemented')
        s,b,h=spatial_fixture()
        from subway.src.analysis.spatial_heterogeneity import build_spatial_context
        dong,station,_,_=build_spatial_context(s,b,h,{})
        layer=pd.DataFrame(dict(canonical_station_id=s.canonical_station_id,beta_hot=[-.1,.2,0,.4,-.5],beta_cold=[.4,.3,.2,.1,0]))
        primary=pd.DataFrame(dict(term=['a','b','c','d'],beta=[.1,-.2,.3,-.4],ci95_low=[-.1,-.4,.1,-.6],ci95_high=[.3,0,.5,-.2]))
        geo=b[['ADM_CD','geometry']].merge(dong,on='ADM_CD',validate='one_to_one')
        with tempfile.TemporaryDirectory() as td:
            names=figures.render_spatial_figures(geo,station,layer,primary,Path(td))
            self.assertEqual(set(names),{'station_extreme_heterogeneity.png','spatial_context.png','spatial_moderation_effects.png'})
            self.assertTrue(all((Path(td)/p).stat().st_size>1000 for p in names))
            with self.assertRaises(ValueError):figures.render_spatial_figures(geo,station,layer,primary.iloc[:3],Path(td))

    def test_runner_twice_is_deterministic_and_prior_inputs_unchanged(self):
        runner=self.runner()
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td);config=self.fixture(repo)
            prior={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()}
            with patch.object(runner,'load_spatial_heterogeneity_config',return_value=config):
                self.assertEqual(runner.run_spatial_heterogeneity(repo,2024),0)
                first={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'subway/results').rglob('*') if p.is_file()}
                self.assertEqual(runner.run_spatial_heterogeneity(repo,2024),0)
            second={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'subway/results').rglob('*') if p.is_file()}
            self.assertEqual(first,second)
            for path,value in prior.items():self.assertEqual(hashlib.sha256((repo/path).read_bytes()).hexdigest(),value)
            summary=json.loads((repo/'subway/results/models/spatial_moderation_summary.json').read_text())
            self.assertEqual(summary['human_scientific_review'],'PENDING')
            self.assertNotIn(str(repo),json.dumps(summary))

    def test_runner_dependency_drift_or_failure_never_replaces_success_output(self):
        runner=self.runner()
        for changed in ['base','stage2','stage3b','late_failure']:
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as td:
                repo=Path(td);config=self.fixture(repo)
                sentinel=repo/'subway/results/models/spatial_moderation_primary.csv';sentinel.write_bytes(b'previous approved success')
                if changed in ['base','stage2']:
                    path=repo/('subway/data/analysis/analysis_base_2024.parquet' if changed=='base' else 'subway/data/clean/climate_shelters.parquet')
                    path.write_bytes(path.read_bytes()+b'drift')
                if changed=='stage3b':(repo/'subway/results/models/confirmatory_summary.json').write_text('{"status":"BLOCKED"}')
                with patch.object(runner,'load_spatial_heterogeneity_config',return_value=config):
                    if changed=='late_failure':
                        with patch.object(runner,'render_spatial_figures',side_effect=ValueError('figure gate failure')):
                            self.assertEqual(runner.run_spatial_heterogeneity(repo,2024),1)
                    else:self.assertEqual(runner.run_spatial_heterogeneity(repo,2024),1)
                self.assertEqual(sentinel.read_bytes(),b'previous approved success')


if __name__=='__main__':unittest.main()
