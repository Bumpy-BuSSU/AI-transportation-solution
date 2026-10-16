import unittest

import pandas as pd

from subway.src.ingest.discovery import RawFileRecord
from subway.src.ingest.manifest import MANIFEST_COLUMNS, merge_manifest


class ManifestTests(unittest.TestCase):
    def _record(self, name="a.csv", digest="a" * 64):
        return RawFileRecord("weather", name, name, ".csv", 10, digest, "primary")

    def test_creates_one_row_per_primary_and_preserves_manual_metadata(self):
        raw_path = "subway/data/raw/2024/weather/a.csv"
        existing = pd.DataFrame([{c: "" for c in MANIFEST_COLUMNS}])
        existing.loc[0, ["dataset_id", "year", "raw_path", "provider", "source_url"]] = [
            "weather", "2024", raw_path, "기상청", "https://example.test/weather"
        ]
        merged = merge_manifest(existing, [self._record()], 2024)
        self.assertEqual(list(merged.columns), MANIFEST_COLUMNS)
        self.assertEqual(len(merged), 1)
        row = merged.iloc[0]
        self.assertEqual(row["provider"], "기상청")
        self.assertEqual(row["source_url"], "https://example.test/weather")
        self.assertEqual(row["sha256"], "a" * 64)
        self.assertEqual(row["file_format"], "csv")
        self.assertEqual(row["dataset_name"], "")

    def test_ignores_sidecars_and_sorts_deterministically(self):
        records = [
            RawFileRecord("weather", "z.csv", "z.csv", ".csv", 1, "z" * 64, "primary"),
            RawFileRecord("weather", "a.csv", "a.csv", ".csv", 1, "a" * 64, "primary"),
            RawFileRecord("boundary", "x.dbf", "x.dbf", ".dbf", 1, "d" * 64, "sidecar"),
        ]
        merged = merge_manifest(pd.DataFrame(columns=MANIFEST_COLUMNS), records, 2024)
        self.assertEqual(merged["raw_path"].tolist(), [
            "subway/data/raw/2024/weather/a.csv",
            "subway/data/raw/2024/weather/z.csv",
        ])


if __name__ == "__main__":
    unittest.main()
