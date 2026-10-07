from __future__ import annotations

import pandas as pd

from subway.src.ingest.discovery import RawFileRecord

MANIFEST_COLUMNS = [
    "dataset_id",
    "year",
    "dataset_name",
    "provider",
    "source_url",
    "raw_path",
    "reference_date",
    "download_date",
    "file_format",
    "sha256",
    "license",
    "notes",
]

MANUAL_COLUMNS = [
    "dataset_name",
    "provider",
    "source_url",
    "reference_date",
    "download_date",
    "license",
    "notes",
]


def _blank_row() -> dict[str, object]:
    return {column: "" for column in MANIFEST_COLUMNS}


def merge_manifest(
    existing: pd.DataFrame,
    inventory: list[RawFileRecord],
    year: int,
) -> pd.DataFrame:
    current = existing.copy()
    for column in MANIFEST_COLUMNS:
        if column not in current.columns:
            current[column] = ""
    current = current[MANIFEST_COLUMNS]

    lookup: dict[tuple[str, int, str], dict[str, object]] = {}
    for _, row in current.iterrows():
        try:
            row_year = int(row["year"])
        except (TypeError, ValueError):
            continue
        key = (str(row["dataset_id"]), row_year, str(row["raw_path"]))
        lookup[key] = row.to_dict()

    rows: list[dict[str, object]] = []
    for record in inventory:
        if record.role != "primary":
            continue
        raw_path = f"subway/data/raw/{year}/{record.dataset_id}/{record.relative_path}"
        key = (record.dataset_id, int(year), raw_path)
        old = lookup.get(key, {})
        row = _blank_row()
        for column in MANUAL_COLUMNS:
            value = old.get(column, "")
            row[column] = "" if pd.isna(value) else value
        row.update(
            {
                "dataset_id": record.dataset_id,
                "year": int(year),
                "raw_path": raw_path,
                "file_format": record.extension.lstrip("."),
                "sha256": record.sha256,
            }
        )
        rows.append(row)

    result = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    if not result.empty:
        result = result.sort_values(["dataset_id", "raw_path"], kind="stable").reset_index(drop=True)
    return result
