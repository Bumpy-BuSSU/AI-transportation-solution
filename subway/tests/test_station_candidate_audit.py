"""Audit gates: current support must never become historical authority."""
import unittest
from subway.tools.audit_station_candidate import historical_gate,resolve_name,comparison_statistics
from subway.tools.audit_station_candidate import unapproved_display_evidence

class StationCandidateAuditTests(unittest.TestCase):
    def test_row_reference_cannot_substitute_for_export_date(self):
        result=historical_gate('2026-06-30','2024-12-31')
        self.assertFalse(result['acquired'])
        self.assertEqual(result['compared_count'],0)
        self.assertIsNone(result['sha256'])
    def test_historical_file_requires_exact_bytes(self):
        with self.assertRaises(ValueError):historical_gate('2024-12-31','2024-12-31')
        self.assertTrue(historical_gate('2024-12-31','2024-12-31',b'actual file')['acquired'])
    def test_display_relation_requires_explicit_line_evidence(self):
        relations={('6','녹사평'):('녹사평(용산구청)','official relation')}
        self.assertEqual(resolve_name('6','녹사평',relations)[0],'녹사평(용산구청)')
        self.assertEqual(resolve_name('5','녹사평',relations)[0],'녹사평')
        self.assertEqual(resolve_name('6','안암(고대병원앞)',relations)[0],'안암(고대병원앞)')
    def test_empty_comparison_is_unavailable_not_zero_difference(self):
        result=comparison_statistics([])
        self.assertEqual(result['compared_count'],0)
        self.assertIsNone(result['max_absolute_latitude_difference'])
    def test_nonexact_is_not_a_tolerance_pass(self):
        result=comparison_statistics([{'latitude_difference':0.00001,'longitude_difference':0.0}])
        self.assertEqual(result['exact_count'],0)
        self.assertEqual(result['nonexact_count'],1)
    def test_full_kric_name_does_not_verify_bare_seoul_relation(self):
        text=unapproved_display_evidence('고려대(종암)','고려대')
        self.assertIn('KRIC full ridership name=고려대(종암)',text)
        self.assertIn('Seoul bare name=고려대',text)
        self.assertIn('relationship remains unverified',text)
        self.assertIn('codes cannot prove relation',text)

if __name__=='__main__':unittest.main()
