"""Direct Q2 aggregate contract, including independent old-source validation."""
import csv
import hashlib
import importlib
from pathlib import Path
import tempfile
import unittest
import geopandas as gpd
import pandas as pd
from subway.src.clean.ridership import load_ridership_rules
from subway.src.clean.population import clean_population, verify_population_hierarchy
from subway.src.ingest.spreadsheetml import read_spreadsheetml
from subway.src.utils.artifacts import write_artifacts

ROOT=Path(__file__).resolve().parents[2]

class DirectPopulationTests(unittest.TestCase):
    def setUp(self):
        self.rules=load_ridership_rules(ROOT/'subway/config')
        self.contract=self.rules['source_contracts']['population_direct_65_plus']
        self.path=ROOT/'subway/data/raw/2024/population_direct_65_plus'/self.contract['primary_file']
        self.source=self.path.relative_to(ROOT).as_posix()
        self.boundary=gpd.read_file(ROOT/'subway/data/raw/2024/boundary/bnd_dong_11_2024_2Q.shp')
        try:
            self.reader=importlib.import_module('subway.src.ingest.population_direct').read_direct_population
            module=importlib.import_module('subway.src.clean.population_direct')
            self.cleaner=module.clean_direct_population
            self.compare=module.compare_population_sources
        except (ModuleNotFoundError,AttributeError):
            self.fail('direct population contract reader/cleaner/comparison not implemented')

    def clean(self, frame=None, boundary=None):
        if frame is None:frame=self.reader(self.path,self.contract)
        return self.cleaner(frame,self.boundary if boundary is None else boundary,self.rules,self.source)

    def old(self):
        c=self.rules['source_contracts']['population']
        path=ROOT/'subway/data/raw/2024/population'/c['primary_file']
        f=read_spreadsheetml(path,'데이터','euc-kr',1)
        h=verify_population_hierarchy(f,self.boundary,self.rules)
        return clean_population(f,h,self.rules,path.relative_to(ROOT).as_posix()),h

    def test_exact_schema_and_q2_only(self):
        rows=list(csv.reader(self.path.read_text(encoding='utf-8-sig').splitlines()))
        variants=[]
        for row,column,value in [(0,2,'Q202403 2024 3/4'),(1,2,'002 계 (wrong unit)'),(1,8,'003 한국인'),(1,0,'A 이름')]:
            bad=[r.copy() for r in rows];bad[row][column]=value;variants.append(bad)
        variants.append([r[:-1] for r in rows])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p.csv'
            for bad in variants:
                with p.open('w',encoding='utf-8-sig',newline='') as stream:csv.writer(stream).writerows(bad)
                with self.assertRaises(ValueError):self.reader(p,self.contract)

    def test_426_exact_boundary_keys_totals_sinsa_and_input_unchanged(self):
        f=self.reader(self.path,self.contract);before=f.copy(deep=True);raw=self.path.read_bytes()
        r=self.clean(f.sample(frac=1,random_state=12))
        self.assertEqual(r.findings,[])
        out=r.frame
        self.assertEqual(len(out),426);self.assertEqual(out.gu.nunique(),25)
        self.assertFalse(out.duplicated(['gu','dong']).any())
        self.assertEqual(set(out.adm_cd),set(self.boundary.ADM_CD))
        self.assertEqual(set(out.loc[out.dong.eq('신사동'),'gu']),{'강남구','관악구'})
        self.assertEqual(int(out.population_total.sum()),9619861)
        self.assertEqual(int(out.population_65_plus.sum()),1785286)
        self.assertTrue(out.reference_period.eq('2024 Q2').all())
        self.assertTrue(out.reference_date.eq('2024-06-30').all())
        self.assertTrue(out.source_sha256.eq(self.contract['sha256']).all())
        self.assertTrue(out[['population_total','population_65_plus','senior_population_share']].notna().all().all())
        pd.testing.assert_frame_equal(f,before);self.assertEqual(self.path.read_bytes(),raw)

    def test_required_values_reject_symbols_booleans_negative_noninteger_and_overflow(self):
        f=self.reader(self.path,self.contract)
        index=f.index[f[self.contract['geography_column']].str.startswith('001001020 ')][0]
        for col in [self.contract['total_column'],self.contract['senior_column']]:
            for value in ['',None,'-','...','x','-1','1.5','inf','9223372036854775808',True]:
                with self.subTest(column=col,value=value):
                    bad=f.copy();bad.loc[index,col]=value;r=self.clean(bad)
                    self.assertTrue(any(x.code=='INVALID_DIRECT_POPULATION' and x.severity=='ERROR' for x in r.findings))
                    self.assertNotEqual(len(r.frame),426)

    def test_excess_has_null_share_and_zero_denominator_not_filled(self):
        f=self.reader(self.path,self.contract);index=2
        bad=f.copy();bad.loc[index,self.contract['senior_column']]='9999999'
        r=self.clean(bad)
        self.assertTrue(any(x.code=='SENIOR_EXCEEDS_TOTAL' for x in r.findings))
        self.assertTrue(r.frame.loc[r.frame.source_row_id.eq(index+1),'senior_population_share'].isna().all())
        zero=f.copy();zero.loc[index,[self.contract['total_column'],self.contract['senior_column']]]=['0','0']
        r=self.clean(zero)
        self.assertTrue(r.frame.loc[r.frame.source_row_id.eq(index+1),'senior_population_share'].isna().all())
        self.assertFalse(any(x.severity=='ERROR' for x in r.findings))

    def test_hierarchy_orphans_duplicates_codes_names_and_boundary_fail_closed(self):
        f=self.reader(self.path,self.contract);geo=self.contract['geography_column']
        variants=[pd.concat([f,f.iloc[[2]]],ignore_index=True),f.iloc[1:].copy(),f.drop(index=1),f.drop(index=2)]
        for value in ['999001020 청운효자동','001099020 청운효자동','001001020 알수없는동','not a code']:
            bad=f.copy();bad.loc[2,geo]=value;variants.append(bad)
        for bad in variants:
            self.assertTrue(any(x.severity=='ERROR' for x in self.clean(bad).findings))
        self.assertTrue(any(x.severity=='ERROR' for x in self.clean(f,self.boundary.iloc[:-1]).findings))

    def test_cleaner_rechecks_period_unit_required_headers_and_provenance(self):
        f=self.reader(self.path,self.contract)
        cases=[f.drop(columns=self.contract['senior_column'])]
        for col,value in [('reference_period','2024 Q4'),('reference_date','2024-12-31'),('unit','세대'),('source_sha256','different')]:
            bad=f.copy();bad.loc[2,col]=value;cases.append(bad)
        for bad in cases:
            self.assertTrue(any(x.severity=='ERROR' for x in self.clean(bad).findings))

    def test_400_old_overlap_exact_and_26_direct_aggregates(self):
        primary=self.clean().frame;old,h=self.old()
        self.assertEqual(len(old.frame),400)
        comparison=self.compare(primary,old.frame,expected_overlap=400)
        self.assertEqual(comparison.findings,[])
        self.assertEqual(len(comparison.frame),400)
        self.assertTrue(comparison.frame[['population_total_difference','population_65_plus_difference']].eq(0).all().all())
        missing=set(h.loc[h.level.eq('dong'),'adm_cd'])-set(old.frame.adm_cd)
        recovered=primary[primary.adm_cd.isin(missing)]
        self.assertEqual(len(recovered),26)
        self.assertTrue(recovered[['population_total','population_65_plus','senior_population_share']].notna().all().all())
        self.assertTrue(any(x.code=='INVALID_POPULATION' for x in old.findings))

    def test_cross_validation_mismatch_missing_identity_and_duplicate_block(self):
        primary=self.clean().frame;old,_=self.old()
        mismatch=old.frame.copy();mismatch.loc[0,'population_65_plus']+=1
        wrong_identity=old.frame.copy();wrong_identity.loc[0,'gu']='wrong'
        for bad in [mismatch,old.frame.iloc[:-1],pd.concat([old.frame,old.frame.iloc[[0]]]),wrong_identity]:
            comparison=self.compare(primary,bad,expected_overlap=400)
            self.assertTrue(any(x.severity=='ERROR' for x in comparison.findings))

    def test_population_artifact_deterministic_under_input_reordering(self):
        out=self.clean().frame
        with tempfile.TemporaryDirectory() as tmp:
            frames={'population.csv':out,'population.parquet':out}
            keys={k:['adm_cd'] for k in frames}
            first=write_artifacts(Path(tmp),frames,{'reference_period':'2024 Q2'},sort_columns=keys)
            second=write_artifacts(Path(tmp),{k:f.iloc[::-1] for k,f in frames.items()},{'reference_period':'2024 Q2'},sort_columns=keys)
            self.assertEqual(first,second)

if __name__=='__main__':unittest.main()
