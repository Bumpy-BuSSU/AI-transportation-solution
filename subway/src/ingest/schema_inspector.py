from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd

CSV_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
_SPREADSHEET_NS = "urn:schemas-microsoft-com:office:spreadsheet"


def _dtype_map(frame: pd.DataFrame) -> dict[str, str]:
    return {str(column): str(dtype) for column, dtype in frame.dtypes.items()}


def _inspect_csv(path: Path) -> dict[str, object]:
    last_error = ""
    for encoding in CSV_ENCODINGS:
        try:
            frame = pd.read_csv(path, encoding=encoding)
            return {
                "format": "csv",
                "encoding": encoding,
                "columns": [str(c) for c in frame.columns],
                "dtypes": _dtype_map(frame),
                "row_count": int(len(frame)),
                "loadable": True,
                "error": "",
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "format": "csv",
        "encoding": None,
        "columns": [],
        "dtypes": {},
        "row_count": None,
        "loadable": False,
        "error": last_error,
    }


def _spreadsheetml_encoding(raw: bytes) -> str:
    match = re.search(
        br'<\?xml[^>]*encoding=["\']([^"\']+)["\']',
        raw[:512],
        re.IGNORECASE,
    )
    if not match:
        return "utf-8"
    return match.group(1).decode("ascii").lower()


def _spreadsheetml_row_values(row: ET.Element) -> list[object]:
    values: list[object] = []
    column_number = 1
    cell_tag = f"{{{_SPREADSHEET_NS}}}Cell"
    data_tag = f"{{{_SPREADSHEET_NS}}}Data"
    index_key = f"{{{_SPREADSHEET_NS}}}Index"
    type_key = f"{{{_SPREADSHEET_NS}}}Type"

    for cell in row.findall(cell_tag):
        explicit_index = cell.attrib.get(index_key)
        if explicit_index is not None:
            explicit_index_int = int(explicit_index)
            while column_number < explicit_index_int:
                values.append("")
                column_number += 1

        data = cell.find(data_tag)
        value: object = "" if data is None or data.text is None else data.text
        if data is not None and value != "" and data.attrib.get(type_key) == "Number":
            number = float(str(value))
            value = int(number) if number.is_integer() else number
        values.append(value)
        column_number += 1

    return values


def _inspect_spreadsheetml(path: Path) -> dict[str, object] | None:
    raw = path.read_bytes()
    if b"mso-application" not in raw[:1024] or b"<Workbook" not in raw[:4096]:
        return None

    encoding = _spreadsheetml_encoding(raw)
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": [],
            "sheets": {},
            "loadable": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    worksheet_names = re.findall(r'<Worksheet\b[^>]*\bss:Name="([^"]+)"', text)
    if not worksheet_names:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": [],
            "sheets": {},
            "loadable": False,
            "error": "SpreadsheetML worksheet not found",
        }

    target_name = "데이터" if "데이터" in worksheet_names else worksheet_names[0]
    start_match = re.search(
        rf'<Worksheet\b[^>]*\bss:Name="{re.escape(target_name)}"[^>]*>',
        text,
    )
    if start_match is None:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": worksheet_names,
            "sheets": {},
            "loadable": False,
            "error": f"SpreadsheetML worksheet body not found: {target_name}",
        }

    end = text.find("</Worksheet>", start_match.end())
    if end < 0:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": worksheet_names,
            "sheets": {},
            "loadable": False,
            "error": f"SpreadsheetML worksheet is truncated: {target_name}",
        }

    worksheet_xml = text[start_match.start() : end + len("</Worksheet>")]
    wrapper = (
        f'<Workbook xmlns="{_SPREADSHEET_NS}" '
        f'xmlns:ss="{_SPREADSHEET_NS}" '
        'xmlns:x="urn:schemas-microsoft-com:office:excel">'
        f"{worksheet_xml}</Workbook>"
    )
    try:
        root = ET.fromstring(wrapper)
    except ET.ParseError as exc:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": worksheet_names,
            "sheets": {},
            "loadable": False,
            "error": f"ParseError: {exc}",
        }

    row_tag = f".//{{{_SPREADSHEET_NS}}}Row"
    rows = [_spreadsheetml_row_values(row) for row in root.findall(row_tag)]
    if not rows:
        return {
            "format": "spreadsheetml",
            "encoding": encoding,
            "worksheet_names": worksheet_names,
            "sheets": {},
            "loadable": False,
            "error": f"SpreadsheetML worksheet has no rows: {target_name}",
        }

    max_width = max(len(row) for row in rows)
    header_index = next(i for i, row in enumerate(rows) if len(row) == max_width)
    columns = [str(value) for value in rows[header_index]]
    data_rows = [
        row + [""] * (max_width - len(row))
        for row in rows[header_index + 1 :]
    ]
    frame = pd.DataFrame(data_rows, columns=columns)

    return {
        "format": "spreadsheetml",
        "encoding": encoding,
        "worksheet_names": worksheet_names,
        "sheets": {
            target_name: {
                "columns": columns,
                "dtypes": _dtype_map(frame),
                "row_count": int(len(frame)),
                "title_row_count": int(header_index),
            }
        },
        "loadable": True,
        "error": "",
    }


def _inspect_excel(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".xls":
        spreadsheetml = _inspect_spreadsheetml(path)
        if spreadsheetml is not None:
            return spreadsheetml

    try:
        sheets = pd.read_excel(path, sheet_name=None)
        sheet_results: dict[str, dict[str, object]] = {}
        for name, frame in sheets.items():
            sheet_results[str(name)] = {
                "columns": [str(c) for c in frame.columns],
                "dtypes": _dtype_map(frame),
                "row_count": int(len(frame)),
            }
        return {
            "format": "excel",
            "sheets": sheet_results,
            "loadable": True,
            "error": "",
        }
    except Exception as exc:
        return {
            "format": "excel",
            "sheets": {},
            "loadable": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _inspect_shapefile(path: Path) -> dict[str, object]:
    try:
        frame = gpd.read_file(path)
        geometry_types = sorted(
            str(value) for value in frame.geometry.geom_type.dropna().unique().tolist()
        )
        bounds = [float(value) for value in frame.total_bounds.tolist()]
        return {
            "format": "shapefile",
            "columns": [str(c) for c in frame.columns],
            "dtypes": _dtype_map(frame),
            "row_count": int(len(frame)),
            "crs": str(frame.crs) if frame.crs is not None else None,
            "geometry_types": geometry_types,
            "bounds": bounds,
            "loadable": True,
            "error": "",
        }
    except Exception as exc:
        return {
            "format": "shapefile",
            "columns": [],
            "dtypes": {},
            "row_count": None,
            "crs": None,
            "geometry_types": [],
            "bounds": [],
            "loadable": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def inspect_primary_file(path: Path) -> dict[str, object]:
    extension = path.suffix.lower()
    if extension == ".csv":
        return _inspect_csv(path)
    if extension in {".xls", ".xlsx"}:
        return _inspect_excel(path)
    if extension == ".shp":
        return _inspect_shapefile(path)
    return {
        "format": extension.lstrip("."),
        "loadable": False,
        "error": f"unsupported primary format: {extension}",
    }
