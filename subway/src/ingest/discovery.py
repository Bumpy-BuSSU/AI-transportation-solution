from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from subway.src.utils.hashing import sha256_file

PRIMARY_EXTENSIONS = {".csv", ".xls", ".xlsx", ".shp"}
SIDECAR_EXTENSIONS = {".dbf", ".shx", ".prj", ".cpg"}


@dataclass(frozen=True)
class RawFileRecord:
    dataset_id: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    sha256: str
    role: str


def _classify(extension: str) -> str:
    if extension in PRIMARY_EXTENSIONS:
        return "primary"
    if extension in SIDECAR_EXTENSIONS:
        return "sidecar"
    return "unsupported"


def discover_raw_files(dataset_id: str, dataset_dir: Path) -> list[RawFileRecord]:
    files = sorted(
        (path for path in dataset_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(dataset_dir).as_posix(),
    )
    records: list[RawFileRecord] = []
    for path in files:
        relative_path = path.relative_to(dataset_dir).as_posix()
        extension = path.suffix.lower()
        records.append(
            RawFileRecord(
                dataset_id=dataset_id,
                relative_path=relative_path,
                filename=path.name,
                extension=extension,
                size_bytes=path.stat().st_size,
                sha256=sha256_file(path),
                role=_classify(extension),
            )
        )
    return records
