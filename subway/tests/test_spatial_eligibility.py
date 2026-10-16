import copy,json,tempfile,unittest
from pathlib import Path
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.transform.station_keys import assign_station_ids
from subway.src.transform.spatial_eligibility import build_spatial_eligibility,spatial_subset,summarize_spatial_eligibility

class SpatialEligibilityTests(unittest.TestCase):
    def setUp(self):
        data=[('1','서울역','150','서울','150',37.55,126.97,'alias_matched',False),
              ('6','공덕','2627','공덕','2628',37.54,126.95,'exact_matched',True),
              ('6','고려대(종암)','2641','','',None,None,'ridership_only',False),
              ('7','까치울','2753','','',None,None,'ridership_only',False),
              ('8','암사역사공원','2810','','',None,None,'ridership_only',False),
              ('5','마곡','2515','마곡','2515',37.562182,126.82693,'exact_matched',False),
              ('5','발산','2516','발산','2516',37.562182,126.82693,'exact_matched',False)]
        self.match=pd.DataFrame(data,columns=['line','station_name','station_code_raw_ridership','station_name_raw','station_code_raw_station','latitude','longitude','match_status','source_code_conflict'])
        self.match['source_file']='station.csv';self.match['source_row_id']=range(1,8)
        self.match['alias_evidence']='previously approved scoped alias'
        self.identities=assign_station_ids(self.match[['line','station_name','station_code_raw_ridership']]).frame
        exceptions=self.match[self.match.station_name.isin(['마곡','발산'])].copy();exceptions['exception_code']='DUPLICATE_COORDINATE'
        self.station=StageResult(self.match,[],exceptions)
        self.support=pd.DataFrame([dict(line='6',canonical_station_name='공덕',support_status='exact',support_name='공덕',support_name_line_identity_verified=True,support_candidate_count=1,support_operator='서울교통공사',support_address='백범로 지하200',support_name_relation_evidence='official name/line/operator/address',support_export_reference='2026-06-30',support_reference_url='https://data.kric.go.kr/rips/M_01_01/detail.do?id=32')])
        self.policy=dict(analysis_crs='EPSG:4326',crs_status='ANALYTICAL_ASSUMPTION',crs_evidence='national official2024 WGS84 standard; source-specific datum unavailable',temporal_status='SNAPSHOT_STABILITY_ASSUMPTION',temporal_evidence='2023-10-31 /2024-10-31 /2025-08-14 equal snapshots; not continuous-observation proof',
            known_coordinate_absences=[dict(line='7',station_name='까치울',evidence='official current support; no accepted Seoul coordinate'),dict(line='8',station_name='암사역사공원',evidence='official current support; no accepted Seoul coordinate')],
            known_openings=[dict(line='8',station_name='암사역사공원',date='2024-08-10',evidence='official service notice')])
        self.core=self.identities.loc[self.identities.index.repeat(2),['canonical_station_id','line','station_name']].reset_index(drop=True)
        self.core['join_status']='matched';self.core['total']=100;self.core['senior']=20
        self.core.loc[5,['join_status','total','senior']]=['total_only',50,None]
    def run_contract(self):return build_spatial_eligibility(self.identities,self.match,self.station,self.support,self.policy)
    def test_every_identity_once_and_coordinate_only_rows_not_denominator(self):
        self.match=pd.concat([self.match,self.match.iloc[[0]].assign(line='2',station_name='까치산',match_status='station_only')],ignore_index=True)
        result=self.run_contract()
        self.assertEqual(len(result.frame),7);self.assertFalse(result.frame.canonical_station_id.duplicated().any())
        self.assertTrue(result.frame.spatial_status.notna().all())
    def test_unadopted_identity_excluded_despite_current_kric_name(self):
        row=self.run_contract().frame.set_index('station_name').loc['고려대(종암)']
        self.assertEqual(row.spatial_status,'EXCLUDED_IDENTITY')
    def test_magok_balsan_excluded_without_repair(self):
        rows=self.run_contract().frame.set_index('station_name').loc[['마곡','발산']]
        self.assertTrue(rows.spatial_status.eq('EXCLUDED_COORDINATE').all());self.assertTrue(rows.latitude.eq(37.562182).all())
    def test_corrobated_code_conflict_warning_keeps_both_original_codes(self):
        row=self.run_contract().frame.set_index('station_name').loc['공덕']
        self.assertEqual(row.spatial_status,'ELIGIBLE_CODE_WARNING');self.assertTrue(row.source_code_conflict)
        self.assertEqual(row.station_code_raw_ridership,'2627');self.assertEqual(row.station_code_raw_coordinate,'2628')
    def test_duplicate_or_false_support_fails_closed(self):
        self.support=pd.concat([self.support,self.support],ignore_index=True)
        self.assertEqual(self.run_contract().frame.set_index('station_name').loc['공덕'].spatial_status,'EXCLUDED_IDENTITY')
    def test_audited_official_kric_rename_corroborates_exact_seoul_identity(self):
        self.support=self.support.assign(support_status='reviewed_name',support_name='공덕(공식병기)',support_name_relation_evidence='official OA-22477 explicit line-scoped rename record')
        row=self.run_contract().frame.set_index('station_name').loc['공덕']
        self.assertEqual(row.spatial_status,'ELIGIBLE_CODE_WARNING')
        self.assertEqual(row.station_name_raw_coordinate,'공덕')
        self.assertTrue(row.source_code_conflict)
        self.support=self.support.iloc[[0]].assign(support_name_line_identity_verified='False')
        self.assertEqual(self.run_contract().frame.set_index('station_name').loc['공덕'].spatial_status,'EXCLUDED_IDENTITY')
    def test_core_unchanged_and_excluded_never_in_subset(self):
        original=self.core.copy(deep=True);e=self.run_contract().frame;subset=spatial_subset(self.core,e)
        pd.testing.assert_frame_equal(self.core,original);self.assertEqual(len(subset),4)
        self.assertTrue(set(subset.canonical_station_id).isdisjoint(set(e.loc[e.spatial_status.str.startswith('EXCLUDED'),'canonical_station_id'])))
    def test_all_exclusions_have_reason_and_evidence(self):
        e=self.run_contract().frame;e=e[e.spatial_status.str.startswith('EXCLUDED')]
        self.assertTrue(e.exclusion_reason.str.strip().ne('').all());self.assertTrue(e.evidence.str.strip().ne('').all())
    def test_crs_assumption_not_source_verification(self):
        e=self.run_contract().frame
        self.assertTrue(e.crs.eq('EPSG:4326').all());self.assertTrue(e.crs_status.eq('ANALYTICAL_ASSUMPTION').all())
        self.assertNotIn('VERIFIED_SOURCE',set(e.crs_status))
    def test_temporal_wording_and_opening_exception(self):
        e=self.run_contract().frame.set_index('station_name')
        self.assertEqual(e.loc['공덕'].temporal_status,'SNAPSHOT_STABILITY_ASSUMPTION')
        self.assertIn('not continuous-observation proof',e.loc['공덕'].temporal_evidence)
        self.assertEqual(e.loc['암사역사공원'].known_opening_date,'2024-08-10')
    def test_shares_include_total_only_and_use_explicit_denominators(self):
        summary=summarize_spatial_eligibility(self.core,self.run_contract().frame)
        self.assertEqual(summary['denominators']['total_ridership_all_observations'],1350)
        self.assertEqual(summary['denominators']['total_ridership_matched_observations'],1300)
        self.assertEqual(summary['exclusions']['total_ridership_all_observations'],950)
        self.assertEqual(summary['exclusions']['total_ridership_matched_observations'],900)
        self.assertEqual(summary['exclusions']['station_identities'],5)
        self.assertAlmostEqual(summary['exclusion_shares']['excluded_total_ridership_share'],950/1350)
    def test_order_independent_status_counts_and_shares(self):
        one=self.run_contract().frame
        self.identities=self.identities.iloc[::-1];self.match=self.match.iloc[::-1];self.support=self.support.iloc[::-1]
        two=self.run_contract().frame
        pd.testing.assert_frame_equal(one,two)
        self.assertEqual(summarize_spatial_eligibility(self.core,one),summarize_spatial_eligibility(self.core.iloc[::-1],two))
    def test_unknown_core_id_and_duplicate_eligibility_rejected(self):
        e=self.run_contract().frame
        with self.assertRaises(ValueError):spatial_subset(self.core.assign(canonical_station_id='unknown'),e)
        with self.assertRaises(ValueError):spatial_subset(self.core,pd.concat([e,e.iloc[[0]]]))
    def test_known_opening_cannot_be_called_full_year_stable(self):
        mask=self.match.station_name.eq('암사역사공원');self.match.loc[mask,['station_name_raw','station_code_raw_station','latitude','longitude','match_status']]=['암사역사공원','2810',37.55,127.13,'exact_matched']
        self.assertEqual(self.run_contract().frame.set_index('station_name').loc['암사역사공원'].spatial_status,'EXCLUDED_TEMPORAL')

if __name__=='__main__':unittest.main()
