from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from subway.src.ingest.discovery import RawFileRecord, discover_raw_files
from subway.src.ingest.manifest import MANIFEST_COLUMNS, merge_manifest
from subway.src.ingest.schema_inspector import inspect_primary_file
from subway.src.utils.paths import load_dataset_config, resolve_repo_relative
from subway.src.validate.raw_validation import Finding, validate_raw_stage


INVENTORY_COLUMNS = [
    "dataset_id",
    "relative_path",
    "filename",
    "extension",
    "size_bytes",
    "sha256",
    "role",
]
FINDING_COLUMNS = ["severity", "dataset_id", "code", "message", "relative_path"]


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _inventory_frame(inventory: list[RawFileRecord]) -> pd.DataFrame:
    rows = [asdict(record) for record in inventory]
    frame = pd.DataFrame(rows, columns=INVENTORY_COLUMNS)
    if not frame.empty:
        frame = frame.sort_values(["dataset_id", "relative_path"], kind="stable").reset_index(drop=True)
    return frame


def _findings_frame(findings: list[Finding]) -> pd.DataFrame:
    return pd.DataFrame([asdict(finding) for finding in findings], columns=FINDING_COLUMNS)


def run_inspection(repo_root: Path, year: int) -> int:
    repo_root = repo_root.resolve()
    config_path = repo_root / "subway" / "config" / "datasets.yaml"
    dataset_config = load_dataset_config(config_path, year)

    inventory: list[RawFileRecord] = []
    schema_snapshot: dict[str, dict[str, object]] = {}
    runtime_config: dict[str, dict[str, object]] = {}

    for dataset_id in sorted(dataset_config):
        entry = dict(dataset_config[dataset_id])
        dataset_dir = resolve_repo_relative(repo_root, str(entry["raw_dir"]))
        entry["exists"] = dataset_dir.is_dir()
        runtime_config[dataset_id] = entry
        if not dataset_dir.is_dir():
            continue
        records = discover_raw_files(dataset_id, dataset_dir)
        inventory.extend(records)
        for record in records:
            if record.role != "primary":
                continue
            raw_path = dataset_dir / Path(record.relative_path)
            schema_snapshot[f"{dataset_id}/{record.relative_path}"] = inspect_primary_file(raw_path)

    inventory.sort(key=lambda record: (record.dataset_id, record.relative_path))
    findings = validate_raw_stage(runtime_config, inventory, schema_snapshot)

    validation_dir = repo_root / "subway" / "data" / "validation"
    _write_csv(validation_dir / "raw_inventory.csv", _inventory_frame(inventory))
    _write_json(validation_dir / "raw_schema_snapshot.json", schema_snapshot)
    _write_csv(validation_dir / "raw_inspection_report.csv", _findings_frame(findings))

    counts = {severity: sum(f.severity == severity for f in findings) for severity in ["ERROR", "WARNING", "INFO"]}
    summary = {
        "year": int(year),
        "dataset_count": len(dataset_config),
        "file_count": len(inventory),
        "primary_file_count": sum(record.role == "primary" for record in inventory),
        "finding_counts": counts,
        "status": "PIPELINE FAILED" if counts["ERROR"] else (
            "PIPELINE PASSED WITH WARNINGS" if counts["WARNING"] else "PIPELINE PASSED"
        ),
    }
    _write_json(validation_dir / "raw_inspection_summary.json", summary)

    manifest_path = repo_root / "subway" / "data_manifest.csv"
    if manifest_path.exists() and manifest_path.stat().st_size:
        existing = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    else:
        existing = pd.DataFrame(columns=MANIFEST_COLUMNS)
    merged = merge_manifest(existing, inventory, year)
    _write_csv(manifest_path, merged)

    return 1 if counts["ERROR"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="2024 지하철 Raw 데이터 구조와 출처 정보를 점검합니다.")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args(argv)
    return run_inspection(REPO_ROOT, args.year)


if __name__ == "__main__":
    raise SystemExit(main())
