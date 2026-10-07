"""Read the approved two-header Seoul export without coercing statistical symbols."""
import csv
import hashlib
from pathlib import Path

import pandas as pd


def read_direct_population(path: Path, contract: dict) -> pd.DataFrame:
    raw = path.read_bytes()
    rows = list(csv.reader(raw.decode(contract['encoding']).splitlines()))
    columns = contract['columns']
    if (len(rows) < 2 or rows[0] != contract['reference_period_header']
            or rows[1] != columns or len(set(columns)) != len(columns)
            or any(len(row) != len(columns) for row in rows[2:])
            or len(rows) - 2 != contract['row_count']):
        raise ValueError('direct population schema/quarter differs from approved contract')
    sha = hashlib.sha256(raw).hexdigest()
    if sha != contract['sha256']:
        raise ValueError('direct population bytes differ from approved SHA-256')
    frame = pd.DataFrame(rows[2:], columns=columns, dtype=object)
    frame['source_row_id'] = range(1, len(frame) + 1)
    frame['source_sha256'] = sha
    frame['reference_period'] = contract['reference_period']
    frame['reference_date'] = contract['reference_date']
    frame['unit'] = contract['unit']
    return frame
