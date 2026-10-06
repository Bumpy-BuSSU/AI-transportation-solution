"""Approved authority regression; proposal CSV remains immutable audit history."""
import hashlib
from pathlib import Path
import unittest
import pandas as pd
from subway.src.clean.ridership import load_ridership_rules
from subway.src.clean.station import clean_stations
from subway.src.transform.station_keys import match_stations, ALIAS_COLUMNS

ROOT = Path(__file__).resolve().parents[2]

class StationAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_ridership_rules(ROOT/'subway/config')
        self.aliases = pd.read_csv(ROOT/'subway/config/station_aliases.csv', dtype=str, keep_default_na=False)
        raw = next((ROOT/'subway/data/raw/2024/station').glob('*.csv'))
        self.raw = pd.read_csv(raw, encoding='cp949', dtype=str, keep_default_na=False)

    def proposals(self):
        p = pd.read_csv(ROOT/'subway/data/validation/batch2r_station_identity_resolution.csv', dtype=str, keep_default_na=False)
        return p[p.resolution.eq('explicit alias gates passed; authoritative adoption blocked by automatic approval review') & p.match_status.eq('station_only')]

    def test_exact_approved_55_scoped_relations_and_senior_bytes(self):
        p = self.proposals()
        a = self.aliases[self.aliases.dataset_id.eq('station')]
        expected = set(zip(p.line, p.station_name_raw, p.proposed_canonical_name))
        self.assertEqual(len(expected), 55)
        self.assertEqual(set(zip(a.line, a.station_name_raw, a.station_name)), expected)
        self.assertEqual(len(a), 55)
        self.assertTrue(a.verified.eq('true').all())
        self.assertTrue(a.evidence.str.strip().ne('').all())
        original = (ROOT/'subway/config/station_aliases.csv').read_bytes().splitlines(keepends=True)[:6]
        self.assertEqual(hashlib.sha256(b''.join(original)).hexdigest(), 'c3181cf850c8f69f5a26dca4bc27cf4f1c30b76eb67c7ff65f947dee2fd5aa98')
        rename = a[a.station_name_raw.eq('뚝섬유원지')].evidence.iloc[0]
        self.assertIn('official rename', rename)
        self.assertNotIn('not an official rename claim', rename)

    def test_all_approved_relations_work_only_on_approved_lines(self):
        p = self.proposals()
        stations = clean_stations(self.raw, self.rules, 'station.csv').frame
        keys = p[['line','proposed_canonical_name','station_code_raw_station']].rename(columns={'proposed_canonical_name':'station_name', 'station_code_raw_station':'station_code_raw'})
        matched = match_stations(keys, stations, self.aliases).frame
        self.assertEqual(int(matched.match_status.eq('alias_matched').sum()), 55)
        source = stations[stations.station_name_raw.eq('뚝섬유원지')].copy()
        source['line'] = '1'
        keys = pd.DataFrame({'line':['1'], 'station_name':['자양(뚝섬한강공원)'], 'station_code_raw':source.station_code_raw.tolist()})
        self.assertNotIn('alias_matched', set(match_stations(keys, source, self.aliases).frame.match_status))

    def test_nonapproved_display_relation_never_matches(self):
        s = clean_stations(self.raw.iloc[[0]].assign(역명='미승인(병기)'), self.rules, 's').frame
        keys = pd.DataFrame({'line':s.line, 'station_name':['미승인'], 'station_code_raw':s.station_code_raw})
        self.assertFalse(match_stations(keys, s, self.aliases).frame.match_status.isin(['exact_matched','alias_matched']).any())

    def test_exact_code_conflict_is_flagged_blocking_and_retained(self):
        s = clean_stations(self.raw.iloc[[0]], self.rules, 's').frame
        keys = pd.DataFrame({'line':s.line, 'station_name':s.station_name, 'station_code_raw':['different']})
        r = match_stations(keys, s, self.aliases)
        self.assertIn('source_code_conflict', r.frame)
        self.assertTrue(r.frame.source_code_conflict.iloc[0])
        self.assertEqual(r.frame.match_status.iloc[0], 'exact_matched')
        self.assertTrue(any(f.code=='SOURCE_CODE_CONFLICT' and f.severity=='ERROR' for f in r.findings))
        self.assertIn('SOURCE_CODE_CONFLICT', set(r.exceptions.exception_code))

    def test_exact_three_groups_info_magok_balsan_error(self):
        r = clean_stations(self.raw, self.rules, 's')
        info = [f for f in r.findings if f.code=='VERIFIED_TRANSFER_COORDINATE']
        self.assertEqual(len(info), 3)
        bad = r.exceptions[r.exceptions.exception_code.eq('DUPLICATE_COORDINATE')]
        self.assertEqual(set(bad.station_name_raw), {'마곡','발산'})
        self.assertEqual(len(bad), 2)

    def test_partial_and_extra_reviewed_groups_are_errors(self):
        members = self.raw[self.raw.역명.eq('까치산')].copy()
        for bad in [members.iloc[:1], pd.concat([members, members.iloc[:1].assign(역명='추가역', 호선='3', **{'고유역번호(외부역코드)':'999'})], ignore_index=True)]:
            r = clean_stations(bad, self.rules, 's')
            self.assertTrue(any(f.severity=='ERROR' and f.code in {'TRANSFER_GROUP_INCOMPLETE','DUPLICATE_COORDINATE'} for f in r.findings))
            self.assertFalse(any(f.code=='VERIFIED_TRANSFER_COORDINATE' for f in r.findings))

if __name__ == '__main__': unittest.main()
