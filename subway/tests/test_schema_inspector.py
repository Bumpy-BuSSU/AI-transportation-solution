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

    def test_spreadsheetml_xls_reads_data_sheet_when_metadata_sheet_is_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "population.xls"
            xml = """\t<?xml version="1.0" encoding="EUC-KR" ?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Worksheet ss:Name="데이터"><Table ss:ExpandedColumnCount="3" ss:ExpandedRowCount="4">
<Row><Cell><Data ss:Type="String">제목</Data></Cell></Row>
<Row><Cell><Data ss:Type="String">동별</Data></Cell><Cell><Data ss:Type="String">연령별</Data></Cell><Cell><Data ss:Type="String">2024. 2/4</Data></Cell></Row>
<Row><Cell><Data ss:Type="String">합계</Data></Cell><Cell><Data ss:Type="String">합계</Data></Cell><Cell><Data ss:Type="Number">100</Data></Cell></Row>
<Row><Cell><Data ss:Type="String">둔촌2동</Data></Cell><Cell><Data ss:Type="String">100세 이상</Data></Cell><Cell><Data ss:Type="Number">4</Data></Cell></Row>
</Table></Worksheet>
<Worksheet ss:Name="메타정보"><Table><Row><Cell><Data ss:Type="String">< 통계표 메타자료 ></Data></Cell></Row></Table></Worksheet>
</Workbook>"""
            path.write_bytes(xml.encode("euc-kr"))

            result = inspect_primary_file(path)

            self.assertTrue(result["loadable"])
            self.assertEqual(result["format"], "spreadsheetml")
            self.assertEqual(result["encoding"], "euc-kr")
            self.assertEqual(result["worksheet_names"], ["데이터", "메타정보"])
            self.assertEqual(
                result["sheets"]["데이터"]["columns"],
                ["동별", "연령별", "2024. 2/4"],
            )
            self.assertEqual(result["sheets"]["데이터"]["row_count"], 2)
            self.assertEqual(result["sheets"]["데이터"]["title_row_count"], 1)

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
