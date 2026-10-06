"""Configured current-study-area membership, separate from dong assignment."""
from pathlib import Path
import yaml
import pandas as pd
import geopandas as gpd
import numpy as np
from subway.src.clean.contracts import StageResult
from subway.src.transform.spatial import build_station_master,_boundary_error,_failure
from subway.src.transform.spatial_eligibility import ELIGIBLE_STATUSES

SCOPE_STATUSES=('IN_CURRENT_STUDY_AREA','OUTSIDE_CURRENT_STUDY_AREA','UNRESOLVED_STUDY_AREA_STATUS')


def load_study_area(repo_root: Path,year: int) -> dict:
    try:
        profile=yaml.safe_load((repo_root/'subway/config'/f'study_area_{year}.yaml').read_text(encoding='utf-8'))
        fields={'schema_version','reference_year','study_area_id','study_area_label','boundary_dataset_id',
            'population_dataset_id','weather_dataset_id','climate_response_dataset_id','boundary_contract','current_empirical_scope'}
        if not isinstance(profile,dict) or not fields.issubset(profile) or profile['schema_version']!=1 or profile['reference_year']!=year:
            raise ValueError('study-area profile schema/year mismatch')
        for field in fields-{'schema_version','reference_year','boundary_contract'}:
            value=profile[field]
            if not isinstance(value,str) or not value.strip() or ':' in value or '/' in value or '\\' in value:
                # Human-readable scope sentences may contain punctuation, but never filesystem paths.
                if field!='current_empirical_scope':raise ValueError(f'invalid study-area field: {field}')
        return profile
    except (OSError,TypeError,yaml.YAMLError) as exc:raise ValueError('study-area profile unavailable or invalid') from exc


def classify_study_area(stations: pd.DataFrame,boundary: gpd.GeoDataFrame,profile: dict) -> StageResult:
    master=build_station_master(stations)
    if master.findings:return master
    error=_boundary_error(boundary,profile.get('boundary_contract'))
    if error:return _failure(boundary,*error)
    out=master.frame.copy(deep=True)
    out['study_area_id']=profile['study_area_id'];out['study_area_status']=SCOPE_STATUSES[2]
    out['study_area_reason']='TASK5_EXCLUDED_NO_ACCEPTED_SPATIAL_IDENTITY'
    out['study_area_evidence']='current configured validated boundary union; no replacement coordinates or correction'
    eligible=out.spatial_status.isin(ELIGIBLE_STATUSES)
    selected=out.loc[eligible]
    lat=pd.to_numeric(selected.latitude,errors='coerce');lon=pd.to_numeric(selected.longitude,errors='coerce')
    if (not np.isfinite(lat.to_numpy(dtype=float,na_value=np.nan)).all() or not np.isfinite(lon.to_numpy(dtype=float,na_value=np.nan)).all()
            or not lat.between(-90,90).all() or not lon.between(-180,180).all()
            or not selected.crs.eq('EPSG:4326').all() or not selected.crs_status.eq('ANALYTICAL_ASSUMPTION').all()):
        return _failure(selected,'STUDY_AREA_COORDINATE','eligible geographic coordinates and approved CRS assumption required')
    area=boundary.geometry.union_all()
    if area.is_empty or not area.is_valid:return _failure(boundary,'STUDY_AREA_GEOMETRY','valid nonempty union required; no repair')
    points=gpd.GeoSeries(gpd.points_from_xy(lon,lat),index=selected.index,crs=4326).to_crs(boundary.crs)
    for index,point in points.items():
        if area.contains(point):status,reason=SCOPE_STATUSES[0],'STRICTLY_INSIDE_CONFIGURED_BOUNDARY_UNION'
        elif area.touches(point):status,reason=SCOPE_STATUSES[2],'ON_OUTER_STUDY_AREA_BOUNDARY'
        else:status,reason=SCOPE_STATUSES[1],'OUTSIDE_CONFIGURED_BOUNDARY_UNION'
        out.loc[index,['study_area_status','study_area_reason']]=[status,reason]
    return StageResult(out,[],pd.DataFrame())
