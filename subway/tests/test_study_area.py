import unittest
from pathlib import Path
import tempfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point,box
from subway.src.transform.study_area import classify_study_area,load_study_area
from subway.src.transform.spatial import map_stations_to_dongs,map_population_to_boundary
from subway.tests.test_transform_spatial import stations


class StudyAreaTests(unittest.TestCase):
    def fixture(self):
        p=gpd.GeoSeries([Point(127,37)],crs=4326).to_crs(5179).iloc[0]
        b=gpd.GeoDataFrame(dict(ADM_CD=['99000001','99000002'],ADM_NM=['a','b'],dong=['a','b'],gu=['g','g'],BASE_DATE=['20240630']*2),
            geometry=[box(p.x-10,p.y-10,p.x,p.y+10),box(p.x,p.y-10,p.x+10,p.y+10)],crs=5179)
        profile=dict(study_area_id='synthetic',study_area_label='Synthetic area',boundary_contract=dict(row_count=2,crs='EPSG:5179',code_pattern=r'99\d{6}',base_date='20240630'))
        return p,b,profile

    def test_replaceable_profile_and_internal_boundary_is_inside_union(self):
        _,b,p=self.fixture();s=stations()
        m=map_stations_to_dongs(s,b,boundary_contract=p['boundary_contract'])
        self.assertEqual(m.frame.mapping_status.iloc[0],'BOUNDARY_POINT')
        r=classify_study_area(s,b,p)
        self.assertFalse(r.findings);self.assertEqual(r.frame.study_area_status.iloc[0],'IN_CURRENT_STUDY_AREA')
        self.assertEqual(r.frame.study_area_id.iloc[0],'synthetic')

    def test_union_classification_independent_of_mapping_status_and_names(self):
        _,b,p=self.fixture();s=stations();s['station_name']='anything'
        self.assertEqual(classify_study_area(s,b,p).frame.study_area_status.iloc[0],'IN_CURRENT_STUDY_AREA')
        s['longitude']=128.
        self.assertEqual(classify_study_area(s,b,p).frame.study_area_status.iloc[0],'OUTSIDE_CURRENT_STUDY_AREA')

    def test_excluded_and_external_boundary_touch_are_unresolved(self):
        point,b,p=self.fixture();s=stations('EXCLUDED_COORDINATE');s['exclusion_reason']='missing';s['latitude']=None
        self.assertEqual(classify_study_area(s,b,p).frame.study_area_status.iloc[0],'UNRESOLVED_STUDY_AREA_STATUS')
        b.geometry=[box(point.x,point.y-10,point.x+10,point.y+10),box(point.x+20,point.y-10,point.x+30,point.y+10)]
        r=classify_study_area(stations(),b,p)
        self.assertEqual(r.frame.study_area_status.iloc[0],'UNRESOLVED_STUDY_AREA_STATUS')

    def test_profile_population_join_no_universal_426_or_11_prefix(self):
        _,b,p=self.fixture();pop=pd.DataFrame(dict(adm_cd=b.ADM_CD,gu=b.gu,dong=b.dong,population_total=[10,20],population_65_plus=[2,4],senior_population_share=[.2,.2]))
        result=map_population_to_boundary(pop,b,boundary_contract=p['boundary_contract'])
        self.assertFalse(result.findings);self.assertEqual(len(result.frame),2)

    def test_no_input_mutation_and_wrong_profile_is_error(self):
        _,b,p=self.fixture();s=stations();before=s.copy(deep=True);bb=b.copy(deep=True)
        classify_study_area(s,b,p);pd.testing.assert_frame_equal(s,before);pd.testing.assert_frame_equal(b,bb)
        p['boundary_contract']['row_count']=3
        self.assertTrue(any(f.severity=='ERROR' for f in classify_study_area(s,b,p).findings))

    def test_profile_year_and_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):load_study_area(Path(temp),2025)


if __name__=='__main__':unittest.main()
