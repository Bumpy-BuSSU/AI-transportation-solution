import tempfile
from pathlib import Path
import unittest
import pandas as pd
from subway.src.ingest.spreadsheetml import read_spreadsheetml
from subway.src.clean.population import clean_population, verify_population_hierarchy, SENIOR_BANDS

class PopulationTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for block in [1,2]:
            for age in ['합계']+SENIOR_BANDS:
                for item in ['계','한국인']:
                    rows.append({'동별':'신사동','연령별':age,'항목':item,'단위':'명','2024. 2/4':'100' if age=='합계' else '5',
                                 '2024. 3/4':'999','2024. 4/4':'888','source_block_id':block,'source_row_id':len(rows)+1})
        hierarchy=pd.DataFrame({'source_block_id':[1,2],'source_label':['신사동','신사동'],'level':['dong','dong'],
                                'gu':['관악구','강남구'],'dong':['신사동','신사동'],'adm_cd':['11210650','11230670'],'evidence':['verified fixture']*2})
        return pd.DataFrame(rows),hierarchy,{'population':{'expected_gu':2,'expected_dong':2}}
    def test_sparse_cells_and_malformed_metadata_ignored(self):
        text='<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="데이터"><Table><Row><Cell><Data>title</Data></Cell></Row><Row><Cell><Data>A</Data></Cell><Cell><Data>B</Data></Cell><Cell><Data>C</Data></Cell></Row><Row><Cell ss:Index="3"><Data>value</Data></Cell></Row></Table></Worksheet><Worksheet ss:Name="메타정보"><broken></Workbook>'
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'a.xls';p.write_text(text,encoding='utf-8')
            out=read_spreadsheetml(p,'데이터','utf-8',1)
            self.assertEqual(out.loc[0,['A','B','C']].tolist(),['','','value'])
            self.assertEqual(out.source_row_id.iloc[0],1)
    def test_duplicate_dong_gu_q2_exact_bands_and_input_unchanged(self):
        frame,hierarchy,rules=self.fixture();before=frame.copy()
        out=clean_population(frame.sample(frac=1,random_state=1),hierarchy,rules,'p.xls')
        self.assertEqual(out.findings,[]);self.assertEqual(len(out.frame),2)
        self.assertEqual(set(out.frame.population_65_plus),{40});self.assertEqual(set(out.frame.population_total),{100})
        self.assertEqual(set(out.frame.senior_population_share),{.4})
        self.assertTrue(all(len(ids.split('|'))==9 for ids in out.frame.source_row_ids));pd.testing.assert_frame_equal(frame,before)
    def test_orphan_unverified_missing_duplicate_negative_and_share(self):
        frame,hierarchy,rules=self.fixture()
        variants=[(frame,hierarchy.iloc[:1]),(frame,hierarchy.assign(evidence='')),
                  (frame.drop(index=2),hierarchy),(pd.concat([frame,frame.iloc[[2]]]),hierarchy)]
        for index,value in [(0,'-1'),(2,'101'),(0,'0'),(0,'x')]:
            bad=frame.copy();bad.loc[index,'2024. 2/4']=value;variants.append((bad,hierarchy))
        for bad,h in variants:
            self.assertTrue(clean_population(bad,h,rules,'p').findings)
        zero=frame.copy();zero.loc[(zero.source_block_id==1)&zero['항목'].eq('계'),'2024. 2/4']='0'
        result=clean_population(zero,hierarchy,rules,'p');self.assertTrue(result.frame.loc[result.frame.gu=='관악구','senior_population_share'].isna().all())
    def test_full_hierarchy_requires_boundary_and_reviewed_names(self):
        f,h,rules=self.fixture()
        with self.assertRaises(ValueError):verify_population_hierarchy(f,pd.DataFrame(),rules)

    def test_blank_unit_requires_metadata_evidence(self):
        f,h,rules=self.fixture();f['단위']=''
        self.assertTrue(clean_population(f,h,rules,'p').findings)
        rules['population'].update(unit='명',unit_evidence='fixture metadata')
        self.assertEqual(clean_population(f,h,rules,'p').findings,[])

    def test_null_unit_without_metadata_is_blocking(self):
        for value in [None,pd.NA]:
            f,h,rules=self.fixture();f['단위']=value
            result=clean_population(f,h,rules,'p')
            self.assertTrue(any(x.code=='INVALID_POPULATION' for x in result.findings))
            rules['population'].update(unit='명',unit_evidence='fixture metadata')
            self.assertEqual(clean_population(f,h,rules,'p').findings,[])

    def test_full_groups_not_just_forward_fill_and_reordered_source(self):
        labels=['합계','관악구','신사동','낙성대동','강남구','신사동','압구정동']
        f=pd.DataFrame({'동별':labels,'source_row_id':range(1,8),'source_block_id':range(1,8)})
        b=pd.DataFrame({'ADM_NM':['신사동','낙성대동','신사동','압구정동'],'ADM_CD':['11210650','11210580','11230510','11230545']})
        rules={'population':dict(expected_gu=2,expected_dong=4,gu_names=['관악구','강남구'],hierarchy_evidence='fixture',code_evidence='fixture')}
        h=verify_population_hierarchy(f.sample(frac=1,random_state=1),b,rules)
        self.assertEqual(h[h.level=='dong'].gu.tolist(),['관악구','관악구','강남구','강남구'])
        for bad in [f.assign(동별=f['동별'].replace('낙성대동','알수없는동')),f.iloc[1:],f.assign(source_row_id=1)]:
            with self.assertRaises(ValueError):verify_population_hierarchy(bad,b,rules)

if __name__=='__main__':unittest.main()
