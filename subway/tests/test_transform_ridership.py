from pathlib import Path
import unittest
import pandas as pd
from subway.src.transform.ridership import integrate_ridership
from subway.src.transform.station_keys import assign_station_ids,build_senior_crosswalk

def fixture(values,dataset):
    f=pd.DataFrame({'date':pd.to_datetime(['2024-01-01']*len(values)),'line':'2','station_name':'A',
                    'station_name_raw':'A','station_code_raw':'1' if dataset=='senior_ridership' else '999',
                    'hour_bin':[f'{6+i:02}_{7+i:02}' for i in range(len(values))],
                    'hour_start':range(6,6+len(values)),'hour_end':range(7,7+len(values)),
                    'boarding_type':'boarding','ridership':pd.Series(values,dtype='Int64'),
                    'source_row_id':1,'source_file':f'subway/{dataset}.csv','source_dataset_id':dataset})
    if dataset=='senior_ridership':f['crosswalk_status']='exact_matched'
    return assign_station_ids(f).frame

def policy(**changes):
    p=dict(status='adopted',count_threshold=20,rate_threshold=1.0,profile_hour_threshold=2,recurrence_date_threshold=3)
    p.update(changes);return {'senior_excess_policy':p}

class IntegrationTests(unittest.TestCase):
    def test_safe_difference_share_zero_zero_and_unchanged(self):
        s=fixture([3,0],'senior_ridership');t=fixture([10,0],'total_ridership');bs=s.copy();bt=t.copy()
        r=integrate_ridership(s,t,policy())
        self.assertEqual(r.findings,[]);self.assertEqual(r.frame.non_senior.tolist(),[7,0])
        self.assertEqual(r.frame.senior_share.iloc[0],.3);self.assertTrue(pd.isna(r.frame.senior_share.iloc[1]))
        self.assertEqual(r.frame.senior_station_code_raw.iloc[0],'1');self.assertEqual(r.frame.total_station_code_raw.iloc[0],'999')
        self.assertIn('senior_crosswalk_status',r.frame);self.assertEqual(r.frame.join_status.tolist(),['matched']*2)
        pd.testing.assert_frame_equal(s,bs);pd.testing.assert_frame_equal(t,bt)
    def test_excess_exception_original_values_and_policy_pending(self):
        s=fixture([11,3],'senior_ridership');t=fixture([10,10],'total_ridership')
        r=integrate_ridership(s,t,policy())
        self.assertEqual(r.frame.senior.iloc[0],11);self.assertEqual(r.frame.total.iloc[0],10)
        self.assertTrue(r.frame.loc[[0],['non_senior','senior_share']].isna().all().all())
        self.assertEqual(r.exceptions.difference.iloc[0],1);self.assertEqual(r.findings[0].severity,'WARNING')
        self.assertTrue(any(f.severity=='ERROR' for f in integrate_ridership(s,t).findings))
    def test_full_outer_unmatched_and_deterministic_accounting(self):
        s=fixture([3,2],'senior_ridership');t=fixture([10,4],'total_ridership');t.loc[1,'date']=pd.Timestamp('2024-01-02')
        r=integrate_ridership(s,t,policy());self.assertEqual(len(r.frame),3)
        self.assertEqual(set(r.frame.join_status),{'matched','senior_only','total_only'})
        self.assertTrue(r.frame.loc[r.frame.join_status!='matched',['non_senior','senior_share']].isna().all().all())
        reverse=integrate_ridership(s.iloc[::-1],t.iloc[::-1],policy())
        pd.testing.assert_frame_equal(r.frame,reverse.frame)
    def test_duplicates_either_side_and_many_to_many_retained_no_expansion(self):
        s=fixture([3],'senior_ridership');t=fixture([10],'total_ridership')
        for left,right in [(pd.concat([s,s]),t),(s,pd.concat([t,t])),(pd.concat([s,s]),pd.concat([t,t]))]:
            r=integrate_ridership(left,right,policy())
            self.assertEqual(len(r.frame),len(left)+len(right));self.assertTrue(r.frame.join_status.eq('ambiguous_rejected').all())
            self.assertTrue(any(f.severity=='ERROR' for f in r.findings));self.assertEqual(len(r.exceptions),len(r.frame))
            self.assertTrue(r.frame.non_senior.isna().all())
    def test_invalid_counts_keys_identity_and_hour_contract_block(self):
        for column,value in [('ridership',None),('ridership',-1),('date',pd.NaT),('line','3'),('hour_end',99),('crosswalk_status','unmatched')]:
            s=fixture([3],'senior_ridership');s.loc[0,column]=value
            r=integrate_ridership(s,fixture([10],'total_ridership'),policy())
            self.assertTrue(any(f.severity=='ERROR' for f in r.findings))
            self.assertTrue(r.frame.non_senior.isna().all());self.assertFalse(r.exceptions.empty)
    def test_severity_count_rate_profile_and_recurrence(self):
        s=fixture([11],'senior_ridership');t=fixture([10],'total_ridership')
        for rule in [policy(count_threshold=1),policy(rate_threshold=.5)]:
            self.assertTrue(any(f.severity=='ERROR' for f in integrate_ridership(s,t,rule).findings))
        s=fixture([11,11],'senior_ridership');t=fixture([10,10],'total_ridership')
        self.assertTrue(any(f.severity=='ERROR' for f in integrate_ridership(s,t,policy()).findings))
        s=pd.concat([fixture([11],'senior_ridership').assign(date=pd.Timestamp(f'2024-01-0{i}')) for i in range(1,4)],ignore_index=True)
        t=s.drop(columns='crosswalk_status').assign(ridership=10,source_dataset_id='total_ridership')
        self.assertTrue(any(f.severity=='ERROR' for f in integrate_ridership(s,t,policy()).findings))
    def test_verified_alias_and_exact_use_same_identity_order_independent(self):
        aliases=pd.read_csv(Path(__file__).resolve().parents[1]/'config/station_aliases.csv',dtype=str,keep_default_na=False)
        s=fixture([3,2],'senior_ridership').assign(station_code_raw='409',station_name_raw=['당고개','불암산'])
        t=fixture([10,10],'total_ridership').assign(station_code_raw='409',station_name_raw='당고개',station_name='당고개',line='4')
        s=build_senior_crosswalk(s,t,aliases).frame;t=assign_station_ids(t).frame
        result=integrate_ridership(s,t,policy())
        self.assertEqual(result.frame.join_status.tolist(),['matched','matched'])
        self.assertEqual(set(result.frame.senior_crosswalk_status),{'exact_matched','alias_matched'})
        pd.testing.assert_frame_equal(result.frame,integrate_ridership(s.iloc[::-1],t.iloc[::-1],policy()).frame)

    def test_different_category_dictionaries_preserve_outer_join(self):
        s=fixture([3],'senior_ridership');t=fixture([10,5],'total_ridership')
        t.loc[1,'station_name']='B';t=assign_station_ids(t).frame
        for f in [s,t]:
            for c in ['canonical_station_id','line','station_name','hour_bin','boarding_type']:f[c]=f[c].astype('category')
        r=integrate_ridership(s,t,policy())
        self.assertEqual(r.frame.join_status.tolist().count('matched'),1)
        self.assertEqual(r.frame.join_status.tolist().count('total_only'),1)

    def test_conflicting_duplicate_payload_order_independent(self):
        s=fixture([3],'senior_ridership');s=pd.concat([s,s.assign(ridership=4)],ignore_index=True)
        t=fixture([10],'total_ridership')
        a=integrate_ridership(s,t,policy());b=integrate_ridership(s.iloc[::-1],t,policy())
        pd.testing.assert_frame_equal(a.frame,b.frame);pd.testing.assert_frame_equal(a.exceptions,b.exceptions)
    def test_nonfinite_policy_is_fail_closed(self):
        for value in [float('nan'),float('inf'),float('-inf')]:
            p=policy(count_threshold=value,rate_threshold=value,profile_hour_threshold=value,recurrence_date_threshold=value)
            r=integrate_ridership(fixture([11,3],'senior_ridership'),fixture([10,10],'total_ridership'),p)
            self.assertTrue(any(f.code=='EXCESS_POLICY_UNVERIFIED' for f in r.findings))
    def test_duplicate_columns_preserved_with_schema_error(self):
        s=fixture([3],'senior_ridership');bad=pd.concat([s,s[['date']]],axis=1)
        r=integrate_ridership(bad,fixture([10],'total_ridership'),policy())
        self.assertEqual(len(r.frame),2);self.assertTrue(any(f.code=='INTEGRATION_SCHEMA' for f in r.findings))
        self.assertTrue(r.frame.non_senior.isna().all())
        self.assertEqual(len([c for c in r.frame if c.startswith('senior_input_')]),len(bad.columns))
    def test_boolean_count_is_rejected_and_raw_preserved(self):
        r=integrate_ridership(fixture([3],'senior_ridership').assign(ridership=True),fixture([10],'total_ridership'),policy())
        self.assertTrue(any(f.code=='INVALID_INTEGRATION_ROW' for f in r.findings))
        self.assertTrue(r.frame.non_senior.isna().all());self.assertIn(True,r.frame.senior_ridership_raw.dropna().tolist())

if __name__=='__main__':unittest.main()
