from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_DATASET_IDS = {
    "senior_ridership",
    "total_ridership",
    "weather",
    "station",
    "population",
    "population_direct_65_plus",
    "boundary",
    "shelter",
}


def resolve_repo_relative(repo_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError(f"absolute paths are not allowed: {relative_path}")

    root = repo_root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {relative_path}") from exc
    return resolved


def load_dataset_config(config_path: Path, year: int) -> dict[str, dict[str, object]]:
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    datasets = raw.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("datasets.yaml must contain a 'datasets' mapping")

    actual = set(datasets)
    missing = sorted(REQUIRED_DATASET_IDS - actual)
    unexpected = sorted(actual - REQUIRED_DATASET_IDS)
    if missing:
        raise ValueError(f"missing dataset ids: {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"unexpected dataset ids: {', '.join(unexpected)}")

    result: dict[str, dict[str, object]] = {}
    for dataset_id in sorted(REQUIRED_DATASET_IDS):
        entry = datasets[dataset_id]
        if not isinstance(entry, dict):
            raise ValueError(f"dataset '{dataset_id}' must be a mapping")
        raw_dir = entry.get("raw_dir")
        if not isinstance(raw_dir, str) or not raw_dir.strip():
            raise ValueError(f"dataset '{dataset_id}' requires raw_dir")
        materialized = raw_dir.format(year=year)
        if Path(materialized).is_absolute() or ".." in Path(materialized).parts:
            raise ValueError(f"dataset '{dataset_id}' raw_dir must be repository-relative")
        result[dataset_id] = {**entry, "raw_dir": materialized}
    return result
