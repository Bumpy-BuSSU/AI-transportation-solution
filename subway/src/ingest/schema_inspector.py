from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

CSV_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]


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


def _inspect_excel(path: Path) -> dict[str, object]:
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
