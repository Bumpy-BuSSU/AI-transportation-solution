import unittest
from pathlib import Path
import pandas as pd
from subway.src.clean.station import clean_stations
from subway.src.clean.ridership import load_ridership_rules
from subway.src.transform.station_keys import match_stations, ALIAS_COLUMNS

class StationTests(unittest.TestCase):
    def setUp(self):
        self.rules=load_ridership_rules(Path(__file__).resolve().parents[1]/'config')
        self.raw=pd.DataFrame([{'연번':'1','호선':'1','고유역번호(외부역코드)':'150','역명':'서울역','위도':'37.5','경도':'127','작성일자':'1974-02-28','작성기준일':'2025-08-14'}])
    def test_dates_unknown_crs_and_input_preserved(self):
        before=self.raw.copy(); r=clean_stations(self.raw,self.rules,'station.csv')
        self.assertTrue(r.frame.station_crs.isna().all());self.assertEqual(r.frame.reference_date_raw.iloc[0],'2025-08-14')
        self.assertEqual(r.frame.writing_date_raw.iloc[0],'1974-02-28');self.assertEqual(r.frame.source_row_id.iloc[0],1)
        self.assertFalse(any(f.severity=='ERROR' for f in r.findings));pd.testing.assert_frame_equal(before,self.raw)
    def test_invalid_values_duplicate_identity_and_coordinates(self):
        for col,value in [('호선','9'),('위도','x'),('경도','181')]:
            raw=self.raw.copy();raw.loc[0,col]=value
            self.assertFalse(clean_stations(raw,self.rules,'s').exceptions.empty)
        raw=pd.concat([self.raw,self.raw],ignore_index=True)
        self.assertFalse(clean_stations(raw,self.rules,'s').exceptions.empty)
    def test_code_only_rejected_both_sides_retained_alias_verified_only(self):
        station=clean_stations(self.raw,self.rules,'s').frame
        ridership=pd.DataFrame({'line':['1','2'],'station_name':['서울','다른역'],'station_code_raw':['150','150']})
        aliases=pd.DataFrame(columns=ALIAS_COLUMNS)
        r=match_stations(ridership,station,aliases)
        self.assertEqual(set(r.frame.match_status),{'ridership_only','station_only'})
        self.assertEqual(len(r.frame),3)
        aliases=pd.DataFrame([['station','','서울역','서울','reviewed fixture','false']],columns=ALIAS_COLUMNS)
        self.assertNotIn('alias_matched',set(match_stations(ridership,station,aliases).frame.match_status))
        aliases.loc[0,'verified']='true'
        after=match_stations(ridership,station,aliases)
        self.assertEqual(after.frame.match_status.tolist().count('alias_matched'),1)
        aliases.loc[0,'line']='2'
        self.assertNotIn('alias_matched',set(match_stations(ridership,station,aliases).frame.match_status))

    def test_duplicate_station_identity_preserves_unmatched_both_sides(self):
        stations=clean_stations(pd.concat([self.raw,self.raw],ignore_index=True),self.rules,'s').frame
        ridership=pd.DataFrame({'line':['1','2'],'station_name':['서울역','없는역'],'station_code_raw':['150','200']})
        result=match_stations(ridership,stations,pd.DataFrame(columns=ALIAS_COLUMNS))
        self.assertIn('match_status',result.frame)
        self.assertEqual(len(result.frame),4)
        self.assertTrue(result.frame.station_name.eq('없는역').any())
        self.assertFalse(result.frame.match_status.isin(['exact_matched','alias_matched']).any())

    def transfer_fixture(self):
        raw=pd.concat([self.raw,self.raw],ignore_index=True)
        raw.loc[1,['호선','고유역번호(외부역코드)']]=['4','426']
        group={'members':[['1','150','서울역'],['4','426','서울역']],
               'evidence':'official transfer fixture', 'verified':True}
        rules=dict(self.rules,station_coordinate_review={'verified_transfer_groups':[group]})
        return raw,rules

    def test_verified_transfer_coordinates_are_info_only(self):
        raw,rules=self.transfer_fixture()
        result=clean_stations(raw,rules,'s')
        self.assertFalse(any(f.code=='DUPLICATE_COORDINATE' for f in result.findings))
        self.assertTrue(any(f.code=='VERIFIED_TRANSFER_COORDINATE' and f.severity=='INFO' for f in result.findings))
        self.assertTrue(result.exceptions.empty)

    def test_transfer_evidence_cannot_clear_unrelated_or_same_identity_duplicates(self):
        raw,rules=self.transfer_fixture()
        cases=[]
        unrelated=raw.copy();unrelated.loc[1,'역명']='다른역';cases.append((unrelated,rules))
        cases.append((pd.concat([raw,raw.iloc[[0]]],ignore_index=True),rules))
        cases.append((raw,self.rules))
        for verified,evidence in [(False,'official'),(True,''),(True,None),(True,float('nan')),(True,False),(True,0)]:
            bad_rules=__import__('copy').deepcopy(rules)
            bad_rules['station_coordinate_review']['verified_transfer_groups'][0].update(verified=verified,evidence=evidence)
            cases.append((raw,bad_rules))
        for frame,configuration in cases:
            with self.subTest(frame=frame[['호선','역명']].values.tolist()):
                result=clean_stations(frame,configuration,'s')
                self.assertTrue(any(f.code=='DUPLICATE_COORDINATE' and f.severity=='ERROR' for f in result.findings))

    def test_station_alias_rejects_code_contradiction_and_competing_code_identity(self):
        station=clean_stations(self.raw,self.rules,'s').frame
        aliases=pd.DataFrame([['station','1','서울역','서울','reviewed fixture','true']],columns=ALIAS_COLUMNS)
        for keys in [pd.DataFrame({'line':['1'],'station_name':['서울'],'station_code_raw':['999']}),
                     pd.DataFrame({'line':['1','1'],'station_name':['서울','다른역'],'station_code_raw':['150','150']})]:
            result=match_stations(keys,station,aliases)
            self.assertNotIn('alias_matched',set(result.frame.match_status))
            self.assertTrue(any(f.code=='STATION_ALIAS_CODE_CONTRADICTION' for f in result.findings))

if __name__=='__main__': unittest.main()
