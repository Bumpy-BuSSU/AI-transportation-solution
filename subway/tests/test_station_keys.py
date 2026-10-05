import io
import unittest

import pandas as pd

from subway.src.transform.station_keys import (
    normalize_station_name, build_senior_crosswalk, assign_station_ids,
)

ALIAS_COLUMNS=['dataset_id','line','station_name_raw','station_name','evidence','verified']


def stations(rows, dataset):
    return pd.DataFrame([{'station_code_raw':code,'station_name_raw':name,'station_name':name,
                          'line':line,'source_dataset_id':dataset,'source_file':f'subway/{dataset}.csv',
                          'source_row_id':i+1} for i,(code,name,line) in enumerate(rows)])


class StationKeysTests(unittest.TestCase):
    def empty_aliases(self): return pd.DataFrame(columns=ALIAS_COLUMNS)

    def test_header_only_csv_aliases(self):
        aliases=pd.read_csv(io.StringIO(','.join(ALIAS_COLUMNS)+'\n'),dtype=str,keep_default_na=False)
        senior=stations([('1','A',None)],'senior_ridership')
        total=stations([('1','A','2')],'total_ridership')
        self.assertEqual(build_senior_crosswalk(senior,total,aliases).frame.line.iloc[0],'2')

    def test_conservative_normalization(self):
        self.assertEqual(normalize_station_name(' 교대(법원·검찰청) '),'교대(법원·검찰청)')
        self.assertEqual(normalize_station_name('가'),'가')
        self.assertEqual(normalize_station_name('서울역'),'서울역')

    def test_missing_or_blank_identifiers_never_match(self):
        for code, name in [(pd.NA,'A'), ('','A'), ('1',pd.NA), ('1',' '), (' ','A')]:
            with self.subTest(code=code,name=name):
                senior=stations([(code,name,None)],'senior_ridership')
                total=stations([('1','A','2'),(code,name,'3')],'total_ridership')
                before=senior.copy(deep=True)
                result=build_senior_crosswalk(senior,total,self.empty_aliases())
                self.assertEqual(len(result.frame),1)
                self.assertTrue(result.frame.line.isna().all())
                self.assertTrue(result.frame.canonical_station_id.isna().all())
                self.assertEqual(len(result.exceptions),1)
                self.assertIn('UNRESOLVED_CROSSWALK',{f.code for f in result.findings})
                pd.testing.assert_frame_equal(senior,before)

    def test_unique_pair_and_code_only_rejected_unmatched_preserved(self):
        senior=stations([('001','A',None),('002','Different',None)],'senior_ridership')
        total=stations([('001','A','2'),('002','B','3')],'total_ridership')
        before=senior.copy(deep=True)
        result=build_senior_crosswalk(senior,total,self.empty_aliases())
        self.assertEqual(len(result.frame),2)
        self.assertEqual(result.frame.loc[0,'line'],'2')
        self.assertTrue(pd.isna(result.frame.loc[1,'line']))
        self.assertEqual(result.frame.loc[1,'crosswalk_status'],'unmatched')
        self.assertIn('UNRESOLVED_CROSSWALK',{f.code for f in result.findings})
        self.assertEqual(result.frame.loc[0,'station_code_raw'],'001')
        self.assertEqual(result.frame.loc[1,'station_name_raw'],'Different')
        self.assertEqual(result.exceptions.loc[0,'candidate_lines'],'["3"]')
        pd.testing.assert_frame_equal(senior,before)

    def test_multiple_line_ambiguity_blocks_without_row_expansion(self):
        senior=stations([('1','A',None)],'senior_ridership')
        total=stations([('1','A','1'),('1','A','2')],'total_ridership')
        result=build_senior_crosswalk(senior,total,self.empty_aliases())
        self.assertEqual(len(result.frame),1)
        self.assertTrue(result.frame.line.isna().all())
        self.assertIn('AMBIGUOUS_CROSSWALK',{f.code for f in result.findings})

    def test_verified_alias_only_and_no_implicit_alias(self):
        senior=stations([('1','A(old)',None)],'senior_ridership')
        total=stations([('1','A','2')],'total_ridership')
        for verified,evidence,matched in [('false','source',False),('true','',False),('true','official/source evidence',True)]:
            with self.subTest(verified=verified,evidence=evidence):
                aliases=pd.DataFrame([['senior_ridership','2','A(old)','A',evidence,verified]],columns=ALIAS_COLUMNS)
                before=aliases.copy(deep=True)
                result=build_senior_crosswalk(senior,total,aliases)
                self.assertEqual(bool(result.frame.line.notna().iloc[0]),matched)
                if matched:
                    self.assertEqual(result.frame.crosswalk_status.iloc[0],'alias_matched')
                    self.assertEqual(result.frame.station_name_raw.iloc[0],'A(old)')
                    self.assertEqual(result.frame.line.iloc[0],'2')
                pd.testing.assert_frame_equal(aliases,before)
        self.assertTrue(build_senior_crosswalk(senior,total,self.empty_aliases()).frame.line.isna().all())

    def test_alias_ambiguity_and_code_line_contradictions_block(self):
        senior=stations([('1','A(old)',None)],'senior_ridership')
        total=stations([('1','A','2')],'total_ridership')
        aliases=pd.DataFrame([['senior_ridership','2','A(old)','A','source','true'],
                              ['senior_ridership','3','A(old)','B','source','true']],columns=ALIAS_COLUMNS)
        result=build_senior_crosswalk(senior,total,aliases)
        self.assertIn('ALIAS_AMBIGUITY',{f.code for f in result.findings})
        self.assertTrue(result.frame.line.isna().all())
        aliases=aliases.iloc[[1]].copy(); aliases['station_name']='A'
        result=build_senior_crosswalk(senior,total,aliases)
        self.assertIn('CODE_LINE_CONTRADICTION',{f.code for f in result.findings})
        self.assertTrue(result.frame.line.isna().all())

    def test_stable_order_independent_line_sensitive_ids_and_collision(self):
        frame=stations([('001','Same','1'),('002','Same','2'),('003','B:C','A'),('004','C','A:B'),('005','Missing',None)],'total_ridership')
        before=frame.copy(deep=True)
        result=assign_station_ids(frame)
        self.assertEqual(result.frame.canonical_station_id.dropna().nunique(),4)
        self.assertTrue(pd.isna(result.frame.canonical_station_id.iloc[4]))
        shuffled=assign_station_ids(frame.iloc[::-1])
        self.assertEqual(dict(zip(result.frame.station_code_raw,result.frame.canonical_station_id.fillna(''))),
                         dict(zip(shuffled.frame.station_code_raw,shuffled.frame.canonical_station_id.fillna(''))))
        pd.testing.assert_frame_equal(frame,before)

    def test_total_and_senior_input_unchanged_and_raw_row_diagnostics(self):
        senior=stations([('1','A',None),('1','A',None),('2','B(old)',None)],'senior_ridership')
        total=stations([('1','A','2'),('1','A','2'),('2','B','3')],'total_ridership')
        before=total.copy(deep=True)
        result=build_senior_crosswalk(senior,total,self.empty_aliases())
        self.assertEqual(len(result.frame),3)
        self.assertEqual(result.frame.crosswalk_status.tolist(),['exact_matched','exact_matched','unmatched'])
        self.assertEqual(len(result.exceptions),1)
        self.assertEqual(result.exceptions.source_row_id.iloc[0],3)
        pd.testing.assert_frame_equal(total,before)


if __name__=='__main__': unittest.main()
