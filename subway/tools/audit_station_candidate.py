"""P-S2-2RC read-only audit helpers; never assigns spatial authority or a CRS."""
from __future__ import annotations
import hashlib
from statistics import median

def historical_gate(export_reference: str, target_reference: str, exact_bytes: bytes | None = None) -> dict:
    """A row reference date cannot authenticate the historical export bytes."""
    acquired = export_reference == target_reference
    if acquired and not exact_bytes:
        raise ValueError('Historical export requires exact acquired bytes')
    return {'acquired': acquired, 'target_reference': target_reference,
            'export_reference': export_reference,
            'sha256': hashlib.sha256(exact_bytes).hexdigest() if acquired else None,
            'compared_count': 0}

def resolve_name(line: str, name: str, relations: dict) -> tuple[str, str]:
    """Only explicit, line-scoped relations; never strip adjuncts or offset codes."""
    return relations.get((str(line), name), (name, 'exact name'))

def comparison_statistics(rows: list[dict]) -> dict:
    """Degree differences are descriptive; no tolerance or distance/CRS claim."""
    lat=[abs(float(r['latitude_difference'])) for r in rows]
    lon=[abs(float(r['longitude_difference'])) for r in rows]
    exact=sum(a==0 and b==0 for a,b in zip(lat,lon))
    return {'compared_count':len(rows),'exact_count':exact,'nonexact_count':len(rows)-exact,
            'median_absolute_latitude_difference':median(lat) if lat else None,
            'median_absolute_longitude_difference':median(lon) if lon else None,
            'max_absolute_latitude_difference':max(lat) if lat else None,
            'max_absolute_longitude_difference':max(lon) if lon else None,
            'units':'degrees; not metric distances; no PASS tolerance'}
