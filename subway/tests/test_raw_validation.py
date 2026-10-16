import unittest

from subway.src.ingest.discovery import RawFileRecord
from subway.src.validate.raw_validation import validate_raw_stage


class RawValidationTests(unittest.TestCase):
    def test_missing_directory_and_no_primary_are_errors(self):
        config = {
            "weather": {"raw_dir": "x", "exists": False},
            "station": {"raw_dir": "y", "exists": True},
        }
        findings = validate_raw_stage(config, [], {})
        codes = {(f.dataset_id, f.code, f.severity) for f in findings}
        self.assertIn(("weather", "MISSING_DATASET_DIRECTORY", "ERROR"), codes)
        self.assertIn(("station", "NO_PRIMARY_FILE", "ERROR"), codes)

    def test_unreadable_unsupported_multi_file_and_missing_crs(self):
        inventory = [
            RawFileRecord("weather", "a.csv", "a.csv", ".csv", 1, "a" * 64, "primary"),
            RawFileRecord("weather", "b.csv", "b.csv", ".csv", 1, "b" * 64, "primary"),
            RawFileRecord("weather", "note.txt", "note.txt", ".txt", 1, "c" * 64, "unsupported"),
            RawFileRecord("boundary", "dong.shp", "dong.shp", ".shp", 1, "d" * 64, "primary"),
            RawFileRecord("boundary", "dong.dbf", "dong.dbf", ".dbf", 1, "e" * 64, "sidecar"),
        ]
        schema = {
            "weather/a.csv": {"loadable": False, "error": "bad"},
            "weather/b.csv": {"loadable": True, "format": "csv"},
            "boundary/dong.shp": {"loadable": True, "format": "shapefile", "crs": None},
        }
        config = {"weather": {"exists": True}, "boundary": {"exists": True}}
        findings = validate_raw_stage(config, inventory, schema)
        codes = {(f.dataset_id, f.code, f.severity) for f in findings}
        self.assertIn(("weather", "UNREADABLE_PRIMARY", "ERROR"), codes)
        self.assertIn(("weather", "MULTIPLE_PRIMARY_FILES", "INFO"), codes)
        self.assertIn(("weather", "UNSUPPORTED_FILE", "INFO"), codes)
        self.assertIn(("boundary", "MISSING_CRS", "ERROR"), codes)
        self.assertNotIn(("boundary", "UNREADABLE_PRIMARY", "ERROR"), codes)


if __name__ == "__main__":
    unittest.main()
