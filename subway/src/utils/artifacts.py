import json
from pathlib import Path, PurePosixPath, PureWindowsPath

import pandas as pd

from subway.src.utils.hashing import sha256_file

RUNTIME_KEYS = {'execution_timestamp', 'run_timestamp', 'generated_at', 'execution_time'}


def _check_metadata(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in RUNTIME_KEYS:
                raise ValueError('execution timestamp is not a versioned artifact field')
            _check_metadata(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_metadata(item)
    elif isinstance(value, str) and (PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()):
        raise ValueError('absolute local path is not allowed in versioned artifacts')


def _sort_token(value):
    if hasattr(value, 'wkb_hex'):
        return ('geometry', value.wkb_hex)
    if pd.isna(value):
        return ('null', '')
    if isinstance(value, pd.Timestamp):
        return ('timestamp', value.isoformat())
    return (type(value).__module__ + '.' + type(value).__qualname__, str(value))


def write_artifacts(output_dir: Path, frames: dict[str, pd.DataFrame], summary: dict) -> dict[str, str]:
    """Byte-stable within the same writer/library environment; retain declared columns/dtypes."""
    _check_metadata(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in sorted(frames):
        if Path(name).name != name or PureWindowsPath(name).name != name or Path(name).suffix not in {'.csv', '.parquet'}:
            raise ValueError('artifact filename must be a CSV/Parquet basename')
        frame = frames[name].copy()
        if frame.columns.duplicated().any():
            raise ValueError('duplicate artifact columns')
        for col in frame.select_dtypes(include=['object', 'string']).columns:
            for value in frame[col].dropna().unique():
                _check_metadata(value)
        if not frame.empty:
            keys = [tuple(_sort_token(v) for v in row) for row in frame.itertuples(index=False, name=None)]
            frame = frame.iloc[sorted(range(len(keys)), key=keys.__getitem__)]
        frame = frame.reset_index(drop=True)
        path = output_dir / name
        if name.endswith('.csv'):
            frame.to_csv(path, index=False, encoding='utf-8', lineterminator='\n')
        else:
            options = dict(compression='snappy', version='2.6', use_dictionary=False, write_statistics=True, row_group_size=65536)
            if hasattr(frame, 'crs'):
                frame.to_parquet(path, index=False, schema_version='1.0.0', **options)
            else:
                frame.to_parquet(path, index=False, engine='pyarrow', **options)
        hashes[name] = sha256_file(path)
    payload = dict(summary, output_hashes=hashes)
    path = output_dir / 'pipeline_summary.json'
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    return dict(hashes, **{'pipeline_summary.json': sha256_file(path)})
