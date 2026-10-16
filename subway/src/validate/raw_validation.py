from __future__ import annotations

from dataclasses import dataclass

from subway.src.ingest.discovery import RawFileRecord


@dataclass(frozen=True)
class Finding:
    severity: str
    dataset_id: str
    code: str
    message: str
    relative_path: str = ""


def validate_raw_stage(
    dataset_config: dict[str, dict[str, object]],
    inventory: list[RawFileRecord],
    schema_snapshot: dict[str, dict[str, object]],
) -> list[Finding]:
    findings: list[Finding] = []
    by_dataset: dict[str, list[RawFileRecord]] = {}
    for record in inventory:
        by_dataset.setdefault(record.dataset_id, []).append(record)

    for dataset_id in sorted(dataset_config):
        entry = dataset_config[dataset_id]
        exists = bool(entry.get("exists", True))
        records = by_dataset.get(dataset_id, [])
        primary = [record for record in records if record.role == "primary"]
        unsupported = [record for record in records if record.role == "unsupported"]

        if not exists:
            findings.append(
                Finding("ERROR", dataset_id, "MISSING_DATASET_DIRECTORY", "dataset directory does not exist")
            )
            continue
        if not primary:
            findings.append(Finding("ERROR", dataset_id, "NO_PRIMARY_FILE", "no primary raw file found"))

        if len(primary) > 1:
            findings.append(
                Finding("INFO", dataset_id, "MULTIPLE_PRIMARY_FILES", f"{len(primary)} primary files found")
            )
        for record in unsupported:
            findings.append(
                Finding("INFO", dataset_id, "UNSUPPORTED_FILE", "unsupported file is inventoried", record.relative_path)
            )

        for record in primary:
            key = f"{dataset_id}/{record.relative_path}"
            schema = schema_snapshot.get(key)
            if schema is None:
                findings.append(
                    Finding("ERROR", dataset_id, "MISSING_SCHEMA", "primary file has no schema inspection", record.relative_path)
                )
                continue
            if not schema.get("loadable", False):
                findings.append(
                    Finding("ERROR", dataset_id, "UNREADABLE_PRIMARY", str(schema.get("error", "unreadable")), record.relative_path)
                )
            if record.extension == ".shp" and schema.get("loadable", False) and not schema.get("crs"):
                findings.append(
                    Finding("ERROR", dataset_id, "MISSING_CRS", "shapefile CRS is missing", record.relative_path)
                )

            if schema.get("format") == "excel":
                sheets = schema.get("sheets", {})
                if isinstance(sheets, dict) and len(sheets) > 1:
                    findings.append(
                        Finding("INFO", dataset_id, "MULTIPLE_EXCEL_SHEETS", f"{len(sheets)} sheets found", record.relative_path)
                    )

    return sorted(findings, key=lambda f: (f.dataset_id, f.severity, f.code, f.relative_path))
