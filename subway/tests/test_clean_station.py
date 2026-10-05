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

if __name__=='__main__': unittest.main()
