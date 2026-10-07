import copy
from pathlib import Path
import unittest
import pandas as pd
from subway.src.clean.weather import clean_weather, WEATHER_COLUMNS
from subway.src.clean.ridership import load_ridership_rules

class WeatherTests(unittest.TestCase):
    def setUp(self): self.rules=load_ridership_rules(Path(__file__).resolve().parents[1]/'config')
    def fixture(self):
        rows=pd.DataFrame({'지점':'108','지점명':'서울','일시':pd.date_range('2024-01-01','2024-12-31').strftime('%Y-%m-%d')})
        for name in WEATHER_COLUMNS: rows[name]='1'
        return rows
    def test_full_coverage_variables_provenance_and_unchanged(self):
        raw=self.fixture(); before=raw.copy(deep=True); result=clean_weather(raw,2024,self.rules,'subway/weather.csv')
        self.assertEqual(result.findings,[]);self.assertEqual(result.frame.date.nunique(),366)
        self.assertEqual(set(result.frame.station_id),{'108'})
        self.assertTrue(set(WEATHER_COLUMNS.values()).issubset(result.frame))
        self.assertEqual(result.frame.source_row_id.tolist(),list(range(1,367)))
        self.assertEqual(set(result.frame.source_file),{'subway/weather.csv'})
        self.assertFalse({'heatwave','cold_wave','extreme_temperature'}&set(result.frame))
        pd.testing.assert_frame_equal(raw,before)
    def test_blank_is_missing_literal_zero_preserved(self):
        raw=self.fixture()
        for name in ['일강수량(mm)','일 최심신적설(cm)','일 최심적설(cm)']: raw.loc[0,name]='';raw.loc[1,name]='0'
        result=clean_weather(raw,2024,self.rules,'subway/weather.csv')
        for name in ['precipitation','snow_new_max','snow_depth_max']:
            self.assertTrue(pd.isna(result.frame.loc[0,name])); self.assertEqual(result.frame.loc[1,name],0)
        self.assertTrue(all(f.severity=='WARNING' for f in result.findings));self.assertTrue(result.exceptions.empty)
    def test_blocking_dates_station_temperature_and_numeric(self):
        for column,value in [('지점','109'),('일시','2024/01/01'),('일시','2025-01-01'),('평균기온(°C)',''),('평균기온(°C)','x'),('일강수량(mm)','inf')]:
            with self.subTest(column=column,value=value):
                raw=self.fixture();raw.loc[0,column]=value
                result=clean_weather(raw,2024,self.rules,'subway/weather.csv')
                self.assertTrue(any(f.severity=='ERROR' for f in result.findings));self.assertFalse(result.exceptions.empty)
                self.assertEqual(len(result.frame),366)
        for raw in [self.fixture().iloc[1:],pd.concat([self.fixture(),self.fixture().iloc[[0]]],ignore_index=True)]:
            self.assertTrue(any(f.severity=='ERROR' for f in clean_weather(raw,2024,self.rules,'subway/weather.csv').findings))

if __name__=='__main__':unittest.main()
