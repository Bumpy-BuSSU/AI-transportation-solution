from pathlib import Path
import unittest

import pandas as pd

from subway.src.clean.ridership import clean_ridership, load_ridership_rules


class CleanRidershipTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_ridership_rules(Path(__file__).resolve().parents[1] / 'config')

    def fixture(self, dataset='senior_ridership', dates=None):
        dates = dates or pd.date_range('2024-01-01','2024-12-31').strftime('%Y-%m-%d').tolist()
        columns = self.rules['source_contracts'][dataset]['columns']
        rows = []
        for i, date in enumerate(dates):
            row = {c:'1' for c in columns}
            row.update({'연번':str(i+1), '수송일자':date, '역번호':'001', '역명':' 교대(법원·검찰청) ', '승하차구분':'승차' if i%2==0 else '하차'})
            if '호선' in columns: row['호선'] = '2호선'
            rows.append(row)
        return pd.DataFrame(rows, columns=columns)

    def clean(self, frame, dataset='senior_ridership'):
        return clean_ridership(frame, dataset, 2024, self.rules, f'subway/data/raw/2024/{dataset}/fixture.csv')

    def test_explicit_hour_mapping_and_sum_preservation(self):
        for dataset in ['senior_ridership','total_ridership']:
            with self.subTest(dataset=dataset):
                raw = self.fixture(dataset); before = raw.copy(deep=True)
                result = self.clean(raw, dataset)
                self.assertEqual(result.findings, [])
                self.assertEqual(len(result.frame),len(raw)*20)
                self.assertEqual(set(result.frame.hour_bin), {'before_06','after_24'} | {f'{h:02d}_{h+1:02d}' for h in range(6,24)})
                self.assertEqual(result.frame.ridership.sum(),len(raw)*20)
                self.assertEqual(result.frame.source_hour_column.nunique(),20)
                first = result.frame.query("hour_bin == 'before_06'")
                last = result.frame.query("hour_bin == 'after_24'")
                self.assertTrue(first.hour_start.isna().all()); self.assertTrue((first.hour_end==6).all())
                self.assertTrue((last.hour_start==24).all()); self.assertTrue(last.hour_end.isna().all())
                pd.testing.assert_frame_equal(raw,before)

    def test_dates_boarding_raw_identifiers_and_senior_null_line(self):
        result = self.clean(self.fixture())
        self.assertEqual(result.frame.date.nunique(),366)
        self.assertEqual(set(result.frame.boarding_type),{'boarding','alighting'})
        self.assertEqual(result.frame.station_code_raw.iloc[0],'001')
        self.assertEqual(result.frame.station_name_raw.iloc[0],' 교대(법원·검찰청) ')
        self.assertTrue(result.frame.line.isna().all())
        self.assertEqual(result.frame.source_row_id.nunique(),366)
        self.assertEqual(set(result.frame.source_dataset_id),{'senior_ridership'})
        self.assertNotIn('non_senior',result.frame); self.assertNotIn('senior_share',result.frame)
        self.assertEqual(set(self.clean(self.fixture('total_ridership'),'total_ridership').frame.line),{'2'})

    def test_invalid_missing_negative_and_duplicate_preserved(self):
        mutations = [('INVALID_DATE','수송일자','2024-02-30'),('INVALID_DATE','수송일자','2024/01/01'),
                     ('MANDATORY_NULL','역번호',''),('MANDATORY_NULL','06시간대이전',None),
                     ('NEGATIVE_VALUE','06시간대이전','-1'),('INVALID_NUMERIC','06시간대이전','broken'),
                     ('INVALID_NUMERIC','06시간대이전','1.5'),('UNKNOWN_BOARDING','승하차구분','other')]
        for code, column, value in mutations:
            with self.subTest(code=code,column=column):
                raw=self.fixture(); raw.loc[0,column]=value; before=raw.copy(deep=True)
                result=self.clean(raw)
                self.assertIn(code,{f.code for f in result.findings})
                self.assertFalse(result.exceptions.empty)
                self.assertIn('source_row_id',result.exceptions)
                self.assertEqual(len(result.frame),len(raw)*20)
                pd.testing.assert_frame_equal(raw,before)
        raw=self.fixture(); raw=pd.concat([raw,raw.iloc[[0]]],ignore_index=True)
        result=self.clean(raw)
        self.assertIn('LOGICAL_DUPLICATE',{f.code for f in result.findings})
        self.assertEqual(len(result.frame),len(raw)*20)

    def test_unknown_hour_header_and_missing_required_header(self):
        for raw in [self.fixture().assign(unexpected_hour='1'),self.fixture().drop(columns='역명')]:
            result=self.clean(raw)
            self.assertIn('SOURCE_SCHEMA_DRIFT',{f.code for f in result.findings})
            self.assertFalse(result.exceptions.empty)

    def test_date_coverage_is_global_not_per_station(self):
        raw=self.fixture(); raw.loc[0,'역번호']='999'; raw.loc[0,'역명']='new station'
        self.assertEqual(self.clean(raw).findings,[])
        result=self.clean(raw.iloc[1:])
        self.assertIn('DATE_COVERAGE',{f.code for f in result.findings})

    def test_unknown_line_and_wrong_year_block(self):
        raw=self.fixture('total_ridership'); raw.loc[0,'호선']='9호선'
        self.assertIn('UNKNOWN_LINE',{f.code for f in self.clean(raw,'total_ridership').findings})
        result=clean_ridership(self.fixture(),'senior_ridership',2025,self.rules,'subway/input.csv')
        self.assertTrue(any(f.severity=='ERROR' for f in result.findings))


if __name__=='__main__': unittest.main()
