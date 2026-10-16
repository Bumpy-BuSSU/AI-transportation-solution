from pathlib import Path
import unittest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from subway.src.clean.spatial import clean_boundary,clean_shelters
from subway.src.clean.ridership import load_ridership_rules

class SpatialTests(unittest.TestCase):
    def setUp(self):self.rules=load_ridership_rules(Path(__file__).resolve().parents[1]/'config')
    def boundary(self):
        return gpd.GeoDataFrame({'BASE_DATE':['20240630']*426,'ADM_NM':[f'동{i}' for i in range(426)],'ADM_CD':[f'11010{i:03}' for i in range(426)]},geometry=[Polygon([(0,0),(0,1),(1,1),(1,0)])]*426,crs=5179)
    def test_boundary_contract_and_no_unproven_gu(self):
        raw=self.boundary();before=raw.copy();r=clean_boundary(raw,self.rules,'b.shp')
        self.assertFalse(any(f.severity=='ERROR' for f in r.findings));self.assertEqual(r.frame.crs.to_epsg(),5179)
        self.assertTrue(r.frame.gu.isna().all());self.assertEqual(r.frame.base_date.iloc[0],'20240630')
        pd.testing.assert_frame_equal(before,raw)
    def test_invalid_empty_null_duplicate_unknown_crs_no_repair(self):
        variants=[self.boundary().set_crs(None,allow_override=True),self.boundary().iloc[1:]]
        for value in [Polygon([(0,0),(1,1),(0,1),(1,0)]),Polygon(),None]:
            raw=self.boundary();raw.loc[0,'geometry']=value;variants.append(raw)
        duplicate=self.boundary();duplicate.loc[0,'ADM_CD']=duplicate.loc[1,'ADM_CD'];variants.append(duplicate)
        for raw in variants:
            r=clean_boundary(raw,self.rules,'b');self.assertTrue(any(f.severity=='ERROR' for f in r.findings))
            self.assertFalse(r.exceptions.empty)
            if raw.geometry.iloc[0] is not None:self.assertEqual(r.frame.geometry.iloc[0].wkb,raw.geometry.iloc[0].wkb)
    def shelter(self):
        return pd.DataFrame({'순번':['1','2'],'쉼터_구분':['a']*2,'쉼터명':['s','t'],'구이름':['구']*2,'도로명주소':['주소']*2,'X좌표(EPSG:5186)':['200000','200100'],'Y좌표(EPSG:5186)':['450000','450100'],'운영시간':['시간']*2})
    def test_shelter_explicit_crs_stable_ids_provenance_and_time(self):
        raw=self.shelter();before=raw.copy();r=clean_shelters(raw,self.rules,'s.csv')
        self.assertEqual(r.frame.crs.to_epsg(),5186);self.assertEqual(r.frame.source_row_id.tolist(),[1,2])
        self.assertTrue(any(f.code=='TEMPORAL_UNCERTAINTY' for f in r.findings))
        after=clean_shelters(raw.iloc[::-1],self.rules,'s.csv')
        self.assertEqual(dict(zip(r.frame['순번'],r.frame.shelter_id)),dict(zip(after.frame['순번'],after.frame.shelter_id)))
        pd.testing.assert_frame_equal(before,raw)
    def test_shelter_coordinate_errors_retained_and_duplicate_id_blocks(self):
        for value in ['','x','inf']:
            raw=self.shelter();raw.loc[0,'X좌표(EPSG:5186)']=value;r=clean_shelters(raw,self.rules,'s')
            self.assertEqual(len(r.frame),2);self.assertTrue(pd.isna(r.frame.geometry.iloc[0]));self.assertFalse(r.exceptions.empty)
        raw=self.shelter();raw.loc[0,'순번']='2'
        self.assertTrue(any(f.severity=='ERROR' for f in clean_shelters(raw,self.rules,'s').findings))

if __name__=='__main__':unittest.main()
