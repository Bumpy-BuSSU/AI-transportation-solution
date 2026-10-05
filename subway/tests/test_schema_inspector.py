from pathlib import Path
import tempfile
import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from subway.src.ingest.schema_inspector import inspect_primary_file


class SchemaInspectorTests(unittest.TestCase):
    def test_csv_encodings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [("utf8.csv", "utf-8-sig", "utf-8-sig"), ("cp949.csv", "cp949", "cp949")]
            for name, write_encoding, expected in cases:
                path = root / name
                pd.DataFrame({"역명": ["서울"]}).to_csv(path, index=False, encoding=write_encoding)
                result = inspect_primary_file(path)
                self.assertTrue(result["loadable"])
                self.assertEqual(result["encoding"], expected)
                self.assertEqual(result["columns"], ["역명"])

    def test_excel_records_all_sheets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.xlsx"
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                pd.DataFrame({"a": [1, 2]}).to_excel(writer, sheet_name="첫째", index=False)
                pd.DataFrame({"b": [3]}).to_excel(writer, sheet_name="둘째", index=False)
            result = inspect_primary_file(path)
            self.assertEqual(list(result["sheets"]), ["첫째", "둘째"])
            self.assertEqual(result["sheets"]["첫째"]["row_count"], 2)

    def test_shapefile_records_crs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dong.shp"
            gpd.GeoDataFrame({"ADM_CD": ["1"]}, geometry=[Point(200000, 500000)], crs="EPSG:5179").to_file(path)
            result = inspect_primary_file(path)
            self.assertTrue(result["loadable"])
            self.assertIn("EPSG:5179", result["crs"])
            self.assertEqual(result["geometry_types"], ["Point"])
            self.assertEqual(len(result["bounds"]), 4)


if __name__ == "__main__":
    unittest.main()
