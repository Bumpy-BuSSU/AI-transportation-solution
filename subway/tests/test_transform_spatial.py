import unittest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from subway.src.transform.spatial import (build_station_master, map_stations_to_dongs,
    map_population_to_boundary, enrich_station_population, summarize_spatial_mapping)


def stations(status='ELIGIBLE'):
    return pd.DataFrame([dict(canonical_station_id='station:1:A', line='1', station_name='A',
        station_code_raw_ridership='1', spatial_status=status, exclusion_reason='',
        latitude=37., longitude=127., crs='EPSG:4326', crs_status='ANALYTICAL_ASSUMPTION',
        temporal_status='SNAPSHOT_STABILITY_ASSUMPTION', source_code_conflict=status=='ELIGIBLE_CODE_WARNING',
        station_coordinate_source='source.csv', evidence='approved mapping')])


def boundary(mode='inside'):
    p=gpd.GeoSeries([Point(127,37)],crs=4326).to_crs(5179).iloc[0]
    first=box(p.x-10,p.y-10,p.x+10,p.y+10)
    if mode=='touch':first=box(p.x,p.y-10,p.x+10,p.y+10)
    if mode=='outside':first=box(p.x+10,p.y+10,p.x+20,p.y+20)
    geometries=[first]+[box(p.x+1000+i*30,p.y+1000,p.x+1010+i*30,p.y+1010) for i in range(425)]
    if mode=='overlap':geometries[1]=box(p.x-5,p.y-5,p.x+5,p.y+5)
    return gpd.GeoDataFrame(dict(ADM_CD=[f'1101{i:04}' for i in range(426)],
        ADM_NM=['동']*426,BASE_DATE=['20240630']*426,gu=[f'구{i}' for i in range(426)],dong=['동']*426),geometry=geometries,crs=5179)


def population(b):
    return pd.DataFrame(dict(adm_cd=b.ADM_CD,gu=b.gu,dong=b.dong,
        population_total=[10]*426,population_65_plus=[2]*426,senior_population_share=[.2]*426,
        source_file=['population.csv']*426,reference_date=['2024-06-30']*426))


class TransformSpatialTests(unittest.TestCase):
    def error(self,r):
        self.assertTrue(any(f.severity=='ERROR' for f in r.findings))
        self.assertFalse(r.exceptions.empty)

    def test_master_preserves_all_statuses_and_provenance(self):
        a=stations();x=stations('EXCLUDED_IDENTITY');x['canonical_station_id']='station:1:B'
        x['exclusion_reason']='no identity';raw=pd.concat([a,x],ignore_index=True);before=raw.copy(deep=True)
        r=build_station_master(raw)
        self.assertEqual(len(r.frame),2);self.assertFalse(r.findings)
        pd.testing.assert_frame_equal(raw,before)
        self.assertEqual(r.frame.set_index('canonical_station_id').loc['station:1:B','spatial_status'],'EXCLUDED_IDENTITY')

    def test_inside_is_mapped_with_projected_xy_and_original_coordinates(self):
        r=map_stations_to_dongs(stations(),boundary())
        self.assertFalse(r.findings);self.assertEqual(r.frame.mapping_status.tolist(),['MAPPED'])
        self.assertEqual(r.frame.ADM_CD.iloc[0],'11010000');self.assertEqual(r.frame.longitude.iloc[0],127)
        self.assertGreater(r.frame.x_5179.iloc[0],100000)

    def test_touch_is_explicit_and_has_no_arbitrary_adm_cd(self):
        r=map_stations_to_dongs(stations(),boundary('touch'))
        self.assertEqual(r.frame.mapping_status.iloc[0],'BOUNDARY_POINT');self.assertTrue(pd.isna(r.frame.ADM_CD.iloc[0]))
        self.assertEqual(r.frame.candidate_ADM_CD.iloc[0],'11010000');self.assertFalse(r.exceptions.empty)

    def test_zero_and_multiple_matches_preserve_exceptions(self):
        for mode,status in [('outside','ZERO_MATCH'),('overlap','MULTIPLE_MATCH')]:
            r=map_stations_to_dongs(stations(),boundary(mode))
            self.assertEqual(r.frame.mapping_status.iloc[0],status);self.assertFalse(r.exceptions.empty)
            self.assertTrue(pd.isna(r.frame.ADM_CD.iloc[0]));self.assertTrue(r.frame.mapping_reason.iloc[0])
        self.assertEqual(map_stations_to_dongs(stations(),boundary('overlap')).frame.candidate_ADM_CD.iloc[0],'11010000|11010001')

    def test_excluded_never_enters_mapping_even_with_invalid_coordinates(self):
        a=stations();x=stations('EXCLUDED_COORDINATE');x['canonical_station_id']='station:1:B'
        x['exclusion_reason']='missing';x['latitude']=pd.NA
        r=map_stations_to_dongs(pd.concat([a,x]),boundary())
        self.assertEqual(r.frame.canonical_station_id.tolist(),['station:1:A']);self.assertFalse(r.findings)

    def test_code_warning_is_allowed_and_preserved(self):
        r=map_stations_to_dongs(stations('ELIGIBLE_CODE_WARNING'),boundary())
        self.assertEqual(r.frame.mapping_status.iloc[0],'MAPPED');self.assertTrue(r.frame.source_code_conflict.iloc[0])

    def test_invalid_coordinates_error_without_geometry(self):
        for column,value in [('latitude',None),('latitude','x'),('longitude',181),('latitude',91),('latitude',float('inf'))]:
            raw=stations().astype(object);raw.loc[0,column]=value;r=map_stations_to_dongs(raw,boundary())
            self.error(r);self.assertTrue(pd.isna(r.frame.x_5179.iloc[0]));self.assertNotEqual(r.frame.mapping_status.iloc[0],'MAPPED')

    def test_wrong_station_crs_policy_errors(self):
        for column,value in [('crs','EPSG:5179'),('crs_status','VERIFIED_SOURCE')]:
            raw=stations();raw.loc[0,column]=value;self.error(map_stations_to_dongs(raw,boundary()))

    def test_duplicate_identity_errors_before_mapping(self):
        self.error(build_station_master(pd.concat([stations(),stations()])))
        r=map_stations_to_dongs(pd.concat([stations(),stations()]),boundary());self.error(r)
        self.assertFalse(r.frame.get('mapping_status',pd.Series(dtype=str)).eq('MAPPED').any())

    def test_boundary_contract_errors_block_all_mapping(self):
        variants=[boundary().set_crs(4326,allow_override=True),boundary().iloc[:425]]
        for v in [None,Polygon(),Polygon([(0,0),(1,1),(0,1),(1,0)])]:
            b=boundary();b.loc[0,'geometry']=v;variants.append(b)
        for col,v in [('ADM_CD','11010001'),('BASE_DATE',None),('BASE_DATE','20241231')]:
            b=boundary();b.loc[0,col]=v;variants.append(b)
        for b in variants:
            r=map_stations_to_dongs(stations(),b);self.error(r)
            self.assertFalse(r.frame.get('mapping_status',pd.Series(dtype=str)).eq('MAPPED').any())

    def test_population_uses_codes_for_same_dong_different_gu(self):
        b=boundary();p=population(b);p.loc[1,'population_total']=20;p.loc[1,'senior_population_share']=.1
        r=map_population_to_boundary(p,b)
        self.assertFalse(r.findings);self.assertEqual(len(r.frame),426)
        self.assertEqual(r.frame.set_index('ADM_CD').loc['11010001','population_total'],20)
        self.assertEqual(r.frame.crs.to_epsg(),5179)

    def test_population_duplicates_sets_and_label_disagreement_error(self):
        b=boundary();p=population(b)
        variants=[p.iloc[:-1],pd.concat([p.iloc[:-1],p.iloc[[0]]])]
        for col,v in [('adm_cd','99999999'),('gu','wrong'),('dong','wrong')]:
            q=p.copy();q.loc[0,col]=v;variants.append(q)
        for q in variants:self.error(map_population_to_boundary(q,b))

    def test_population_values_must_remain_verified(self):
        b=boundary();p=population(b)
        for column,value in [('population_total',None),('population_total',-1),('population_total',10.5),
                             ('population_65_plus',11),('senior_population_share',.9)]:
            q=p.astype(object);q.loc[0,column]=value
            self.error(map_population_to_boundary(q,b))

    def test_nonmapped_population_and_reason_contracts_fail_closed(self):
        b=boundary();m=map_stations_to_dongs(stations(),boundary('outside')).frame
        corrupt=m.copy();corrupt['ADM_CD']='11010000'
        self.error(enrich_station_population(corrupt,map_population_to_boundary(population(b),b).frame))
        corrupt=m.copy();corrupt['mapping_reason']=''
        core=pd.DataFrame(dict(canonical_station_id=['station:1:A'],join_status=['matched'],total=[100],senior=[10]))
        with self.assertRaises(ValueError):summarize_spatial_mapping(core,stations(),corrupt)

    def test_enrichment_only_mapped_and_inputs_unchanged(self):
        b=boundary();p=population(b);s=stations();sb=s.copy(deep=True);bb=b.copy(deep=True);pb=p.copy(deep=True)
        pop=map_population_to_boundary(p,b)
        for mode in ['inside','touch','outside','overlap']:
            mapped=map_stations_to_dongs(s,boundary(mode));before=mapped.frame.copy(deep=True)
            r=enrich_station_population(mapped.frame,pop.frame)
            self.assertFalse(r.findings)
            if mode=='inside':self.assertEqual(r.frame.population_total.iloc[0],10)
            else:self.assertTrue(r.frame[['population_total','population_65_plus','senior_population_share']].isna().all().all())
            pd.testing.assert_frame_equal(mapped.frame,before)
        pd.testing.assert_frame_equal(s,sb);pd.testing.assert_frame_equal(p,pb);pd.testing.assert_frame_equal(b,bb)

    def test_summary_incremental_cumulative_all_and_matched_denominators(self):
        a=stations();x=stations('EXCLUDED_IDENTITY');x['canonical_station_id']='station:1:B';x['exclusion_reason']='missing'
        master=pd.concat([a,x],ignore_index=True)
        core=pd.DataFrame(dict(canonical_station_id=['station:1:A','station:1:B','station:1:B'],
            join_status=['matched','matched','total_only'],total=[100,20,5],senior=[10,2,None]))
        before=core.copy(deep=True);mapped=map_stations_to_dongs(a,boundary('outside')).frame
        summary=summarize_spatial_mapping(core,master,mapped)
        self.assertEqual(summary['denominators']['original']['station_identities'],2)
        self.assertEqual(summary['denominators']['task5_eligible']['station_identities'],1)
        self.assertEqual(summary['task9_incremental_shares_of_eligible']['total_ridership_all_observations'],1)
        self.assertEqual(summary['task9_incremental_shares_of_original']['total_ridership_all_observations'],.8)
        self.assertEqual(summary['cumulative_exclusion_shares']['total_ridership_all_observations'],1)
        self.assertEqual(summary['task5_exclusion_shares']['total_ridership_all_observations'],.2)
        self.assertEqual(summary['task5_exclusion_shares']['total_ridership_matched_observations'],20/120)
        self.assertEqual(summary['by_mapping_status']['ZERO_MATCH']['station_identities'],1)
        self.assertEqual(summary['denominators']['original']['total_only_rows'],1)
        pd.testing.assert_frame_equal(core,before)

    def test_reversed_inputs_are_deterministic(self):
        b=boundary();a=stations();x=stations('ELIGIBLE_CODE_WARNING');x['canonical_station_id']='station:1:B'
        raw=pd.concat([a,x],ignore_index=True)
        pd.testing.assert_frame_equal(map_stations_to_dongs(raw,b).frame,map_stations_to_dongs(raw.iloc[::-1],b.iloc[::-1]).frame)
        pd.testing.assert_frame_equal(map_population_to_boundary(population(b),b).frame,map_population_to_boundary(population(b).iloc[::-1],b.iloc[::-1]).frame)

    def test_audit_output_cannot_target_raw(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from subway.tools.generate_task9_audit import validate_output_directory
        with TemporaryDirectory() as root:
            repo=Path(root)
            for output in [repo/'subway/data/raw',repo/'subway/data/raw/2024/nested']:
                with self.assertRaises(ValueError):validate_output_directory(repo,output)
            self.assertEqual(validate_output_directory(repo,repo/'reports'),repo/'reports')


if __name__=='__main__':unittest.main()
