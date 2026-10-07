import json
from pathlib import Path, PurePosixPath, PureWindowsPath

import pandas as pd
import numpy as np
from geopandas import GeoDataFrame

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


def _ordering_column(series):
    if hasattr(series, 'to_wkb'):
        return series.to_wkb(hex=True)
    if series.dtype == object and pd.api.types.infer_dtype(series, skipna=True) not in {'string', 'bytes', 'empty'}:
        # Exceptional mixed object keys need type-aware tokens. Typed large tables
        # use the native path; callers can select typed keys to avoid this fallback.
        return series.map(lambda v: type(v).__module__ + '.' + type(v).__qualname__ + ':' + repr(v), na_action='ignore')
    return series


def write_artifacts(output_dir: Path, frames: dict[str, pd.DataFrame], summary: dict,
                    *, sort_columns: dict[str, list[str]] | None = None) -> dict[str, str]:
    """Byte-stable only in the same declared writer/library environment.

    Sort ascending with nulls last. Default keys are all columns in declared
    schema order; explicit per-artifact keys must be unique to prevent input-order
    ties. For large ridership tables, declare typed provenance/hour keys.
    Serialization retains declared columns, nullable dtypes and GeoDataFrame CRS.
    """
    _check_metadata(summary)
    sort_columns = sort_columns or {}
    if set(sort_columns) - set(frames):
        raise ValueError('sort contract references an unknown artifact')
    output_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in sorted(frames):
        if Path(name).name != name or PureWindowsPath(name).name != name or Path(name).suffix not in {'.csv', '.parquet'}:
            raise ValueError('artifact filename must be a CSV/Parquet basename')
        frame = frames[name].copy()
        if frame.columns.duplicated().any():
            raise ValueError('duplicate artifact columns')
        columns = sort_columns.get(name, list(frame.columns))
        if not columns or len(set(columns)) != len(columns) or any(c not in frame for c in columns):
            raise ValueError('sort columns must be a nonempty unique subset of the schema')
        if name in sort_columns and frame.duplicated(columns, keep=False).any():
            raise ValueError('declared sort columns must uniquely identify rows')
        for col in frame.select_dtypes(include=['object', 'string']).columns:
            for value in frame[col].dropna().unique():
                _check_metadata(value)
        if not frame.empty:
            # Only selected columns participate; no Python row/cell tuple matrix.
            keys = {}
            for c in columns:
                series = frame[c].reset_index(drop=True)
                keys[len(keys)] = _ordering_column(series)
                if pd.api.types.is_float_dtype(series.dtype):
                    # Native numeric sorting ties +0/-0; serialized bytes do not.
                    # Preserve values and resolve the tie with a vectorized bit.
                    keys[len(keys)] = np.signbit(series.to_numpy(dtype=np.float64, na_value=np.nan))
            ordering = pd.DataFrame(keys)
            positions = ordering.sort_values(list(ordering.columns), kind='stable', na_position='last').index
            frame = frame.iloc[positions]
        frame = frame.reset_index(drop=True)
        path = output_dir / name
        if name.endswith('.csv'):
            frame.to_csv(path, index=False, encoding='utf-8', lineterminator='\n')
        else:
            options = dict(compression='snappy', version='2.6', use_dictionary=False, write_statistics=True, row_group_size=65536)
            if isinstance(frame, GeoDataFrame):
                frame.to_parquet(path, index=False, schema_version='1.0.0', **options)
            else:
                frame.to_parquet(path, index=False, engine='pyarrow', **options)
        hashes[name] = sha256_file(path)
    payload = dict(summary, output_hashes=hashes)
    path = output_dir / 'pipeline_summary.json'
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    return dict(hashes, **{'pipeline_summary.json': sha256_file(path)})
