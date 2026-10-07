import hashlib,json,shutil,socket
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from subway.src.analysis.eda import build_eda,temperature_bins


def inputs():
    hours={'before_06':(None,6),**{f'{h:02}_{h+1:02}':(h,h+1) for h in range(6,24)},'after_24':(24,None)}
    rows=[]
    for date in pd.date_range('2024-01-01',periods=2):
        for station in ['in','out','excluded']:
            for hour,(start,end) in hours.items():
                for kind in ['boarding','alighting']:
                    rows.append(dict(date=date,canonical_station_id=station,hour_bin=hour,boarding_type=kind,hour_start=start,hour_end=end,
                        senior=2,total=10,non_senior=8,senior_share=.2,join_status='matched',exception_code=''))
    core=pd.DataFrame(rows)
    first=(core.canonical_station_id.eq('in') & core.date.eq(pd.Timestamp('2024-01-01')) & core.boarding_type.eq('boarding'))
    i=core.index[first & core.hour_bin.eq('before_06')][0]
    core.loc[i,['senior','non_senior','senior_share']]=np.nan;core.loc[i,'join_status']='total_only'
    i=core.index[first & core.hour_bin.eq('10_11')][0]
    core.loc[i,['senior','total']]=[12,10];core.loc[i,['non_senior','senior_share']]=np.nan;core.loc[i,'exception_code']='SENIOR_EXCEEDS_TOTAL'
    i=core.index[core.canonical_station_id.eq('in') & core.date.eq(pd.Timestamp('2024-01-02')) & core.hour_bin.eq('11_12') & core.boarding_type.eq('boarding')][0]
    core.loc[i,['senior','total','non_senior']]=0;core.loc[i,'senior_share']=np.nan
    master=pd.DataFrame(dict(canonical_station_id=['in','out','excluded'],study_area_status=['IN_CURRENT_STUDY_AREA','OUTSIDE_CURRENT_STUDY_AREA','UNRESOLVED_STUDY_AREA_STATUS'],spatial_status=['ELIGIBLE','ELIGIBLE','EXCLUDED_IDENTITY']))
    mapping=pd.DataFrame(dict(canonical_station_id=['in','out'],study_area_status=['IN_CURRENT_STUDY_AREA','OUTSIDE_CURRENT_STUDY_AREA'],mapping_status=['MAPPED','ZERO_MATCH'],ADM_CD=['11111111',None]))
    weather=pd.DataFrame(dict(date=pd.date_range('2024-01-01',periods=2),station_id=['108','108'],temperature_mean=[1.,3.],temperature_max=[4.,6.],temperature_min=[-2.,0.],precipitation=[np.nan,0.],wind_max=[1.,2.],wind_mean=[1.,1.],humidity_mean=[50.,60.],snow_new_max=[np.nan,np.nan],snow_depth_max=[np.nan,np.nan]))
    return core,master,mapping,weather


class AnalysisEDATests(unittest.TestCase):
    def test_membership_accounting_and_core_immutable(self):
        args=inputs();before=[x.copy(deep=True) for x in args]
        base,tables,summary=build_eda(*args,2024)
        for a,b in zip(args,before):pd.testing.assert_frame_equal(a,b)
        self.assertEqual(len(base),80);self.assertEqual(base.canonical_station_id.unique().tolist(),['in'])
        self.assertEqual(summary['sample']['original_core_rows'],240)
        self.assertEqual(summary['sample']['current_study_area_rows'],80)
        self.assertEqual(summary['sample']['matched_rows'],79)
        self.assertEqual(summary['sample']['valid_age_comparison_rows'],78)
        self.assertEqual(summary['sample']['senior_exceeds_total_rows'],1)
        self.assertTrue(base.temperature_mean.notna().all())

    def test_exclusion_reasons_are_separate_and_exhaustive(self):
        _,tables,s=build_eda(*inputs(),2024)
        reasons=tables['eda_exclusions.csv'].set_index('reason')
        self.assertEqual(int(reasons.loc['OUTSIDE_CURRENT_STUDY_AREA','rows']),80)
        self.assertEqual(int(reasons.loc['UNRESOLVED_STUDY_AREA_STATUS','rows']),80)
        self.assertEqual(int(reasons.loc['total_only','rows']),1)
        self.assertEqual(int(reasons.loc['SENIOR_EXCEEDS_TOTAL','rows']),1)

    def test_date_and_station_join_cardinality_and_coverage(self):
        for position in [1,2,3]:
            args=list(inputs());args[position]=pd.concat([args[position],args[position].iloc[[0]]])
            with self.subTest(position=position),self.assertRaises(ValueError):build_eda(*args,2024)
        args=list(inputs());args[3]=args[3].iloc[:1]
        with self.assertRaises(ValueError):build_eda(*args,2024)
        args=list(inputs());args[1].loc[0,'study_area_status']='OUTSIDE_CURRENT_STUDY_AREA'
        with self.assertRaises(ValueError):build_eda(*args,2024)

    def test_daytime_exact_six_intervals(self):
        base,_,s=build_eda(*inputs(),2024)
        self.assertEqual(sorted(base.loc[base.daytime_10_16,'hour_bin'].unique()),['10_11','11_12','12_13','13_14','14_15','15_16'])
        self.assertEqual(int(base.daytime_10_16.sum()),24)
        categorical=list(inputs());categorical[0]['hour_bin']=categorical[0].hour_bin.astype('category')
        _,tables,_=build_eda(*categorical,2024)
        for _,frame in tables['eda_hourly_profile.csv'].groupby('boarding_type'):
            self.assertEqual(frame.iloc[0].hour_bin,'before_06')
            self.assertEqual(frame.iloc[-1].hour_bin,'after_24')
        args=list(inputs());args[0].loc[args[0].hour_bin.eq('10_11'),'hour_end']=12
        with self.assertRaises(ValueError):build_eda(*args,2024)

    def test_null_and_excess_policy_daily_common_denominator(self):
        base,tables,_=build_eda(*inputs(),2024)
        excess=base.loc[base.exception_code.eq('SENIOR_EXCEEDS_TOTAL')]
        self.assertEqual(excess.senior.iloc[0],12);self.assertTrue(excess.non_senior.isna().all())
        self.assertFalse(excess.age_comparison_valid.any())
        daily=tables['eda_daily_age_weather.csv']
        self.assertEqual(int(daily.valid_age_comparison_rows.sum()),78)
        self.assertEqual(int(daily.senior_daily.sum()),154)
        self.assertEqual(int(daily.non_senior_daily.sum()),616)
        self.assertEqual(int(daily.total_daily.sum()),770)
        self.assertEqual(int(daily.total_all_current.sum()),790)
        stats=tables['eda_count_diagnostics.csv'].set_index('age_group')
        self.assertEqual(int(stats.loc['senior','zero_count']),1)
        self.assertEqual(int(stats.loc['non_senior','zero_count']),1)
        self.assertEqual(int(stats.loc['senior','observation_count']),78)

    def test_weather_only_bins_ties_and_missing(self):
        values=pd.Series([1.,1.,1.,3.,5.,np.nan])
        first,edges=temperature_bins(values)
        other,edges2=temperature_bins(values.iloc[::-1])
        self.assertEqual(edges,edges2);self.assertEqual(first.dropna().nunique(),other.dropna().nunique())
        pd.testing.assert_series_equal(first.sort_index(),other.sort_index())
        same,edges=temperature_bins(pd.Series([2.,2.,np.nan]));self.assertEqual(same.dropna().nunique(),1)
        args=list(inputs());_,t,s=build_eda(*args,2024)
        args[0].loc[args[0].canonical_station_id.ne('in'),'total']=999999
        _,u,r=build_eda(*args,2024)
        pd.testing.assert_frame_equal(t['eda_temperature_quantiles.csv'],u['eda_temperature_quantiles.csv'])
        self.assertEqual(s['temperature_bin_edges'],r['temperature_bin_edges'])

    def test_reversed_inputs_deterministic_offline_and_portable(self):
        args=inputs()
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            base,t,s=build_eda(*args,2024)
            reverse,u,r=build_eda(*(a.iloc[::-1] for a in args),2024)
        pd.testing.assert_frame_equal(base,reverse)
        self.assertEqual(json.dumps(s,sort_keys=True,allow_nan=False),json.dumps(r,sort_keys=True,allow_nan=False))
        for name in t:pd.testing.assert_frame_equal(t[name],u[name])
        self.assertNotRegex(json.dumps(s),r'[A-Za-z]:[\\/]')
        self.assertNotIn('timestamp',json.dumps(s))


if __name__=='__main__':unittest.main()


class EDARunnerTests(unittest.TestCase):
    def make_repo(self,root):
        paths=['processed/ridership_2024.parquet','processed/station_master.parquet','processed/station_dong_map.parquet','clean/weather_2024.parquet']
        for path,frame in zip(paths,inputs()):
            p=root/'subway/data'/path;p.parent.mkdir(parents=True,exist_ok=True);frame.to_parquet(p,index=False)
        hashes={p:hashlib.sha256((root/'subway/data'/p).read_bytes()).hexdigest() for p in paths}
        v=root/'subway/data/validation';v.mkdir(parents=True)
        (v/'pipeline_summary.json').write_text(json.dumps(dict(status='PIPELINE PASSED WITH WARNINGS',year=2024,output_hashes=hashes)),encoding='utf-8')
        return hashes

    def test_real_runner_serialization_repeat_offline_and_input_immutable(self):
        from subway.run_eda import run_eda
        with TemporaryDirectory() as tmp:
            repo=Path(tmp);hashes=self.make_repo(repo)
            with patch('socket.socket',side_effect=AssertionError('network forbidden')):
                self.assertEqual(run_eda(repo,2024),0)
                before={p.relative_to(repo).as_posix():p.read_bytes() for folder in ['subway/results/tables','subway/results/figures'] for p in (repo/folder).iterdir()}
                self.assertEqual(run_eda(repo,2024),0)
            self.assertEqual(before,{name:(repo/name).read_bytes() for name in before})
            self.assertEqual(hashes,{p:hashlib.sha256((repo/'subway/data'/p).read_bytes()).hexdigest() for p in hashes})
            s=json.loads((repo/'subway/results/tables/eda_summary.json').read_text(encoding='utf-8'))
            self.assertEqual(s['sample']['valid_age_comparison_rows'],78)
            self.assertEqual(len(list((repo/'subway/results/figures').glob('*.png'))),5)
            self.assertNotIn(str(repo),json.dumps(s))

    def test_changed_input_hash_blocks_before_outputs(self):
        from subway.run_eda import run_eda
        with TemporaryDirectory() as tmp:
            repo=Path(tmp);self.make_repo(repo)
            with (repo/'subway/data/clean/weather_2024.parquet').open('ab') as f:f.write(b'changed')
            self.assertNotEqual(run_eda(repo,2024),0)
            self.assertFalse((repo/'subway/results/tables/eda_summary.json').exists())
