"""Approved Task5 eligibility contract; no geometry, reprojection or Task9 work."""
import math
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.transform.station_keys import assign_station_ids

STATUSES=('ELIGIBLE','ELIGIBLE_CODE_WARNING','EXCLUDED_IDENTITY','EXCLUDED_COORDINATE','EXCLUDED_TEMPORAL')
ELIGIBLE_STATUSES=STATUSES[:2]
COMPLETION_MODE='eligibility_based_with_documented_exclusions'

def _true(value):
    return str(value).lower()=='true'

def _text(value):
    return '' if pd.isna(value) else str(value)

def _validate_eligibility(frame):
    if frame.canonical_station_id.isna().any() or frame.canonical_station_id.duplicated().any():
        raise ValueError('Each canonical identity must have exactly one eligibility status')
    if not frame.spatial_status.isin(STATUSES).all():raise ValueError('Unknown spatial status')
    excluded=~frame.spatial_status.isin(ELIGIBLE_STATUSES)
    for field in ['exclusion_reason','evidence']:
        if frame.loc[excluded,field].isna().any() or frame.loc[excluded,field].astype(str).str.strip().eq('').any():
            raise ValueError('Every exclusion needs a reason and evidence')

def build_spatial_eligibility(identities,station_match,station_result,support,policy):
    """Classify adopted mappings; current KRIC only corroborates code warnings.

    All inputs remain untouched. Coordinate-only source rows cannot enter the
    identity denominator. Missing/contradictory evidence always fails closed.
    """
    required=['canonical_station_id','line','station_name','station_code_raw_ridership']
    if not set(required).issubset(identities):raise ValueError('Canonical identity schema missing')
    identities=identities[required].copy(deep=True)
    if identities[required].isna().any().any() or identities.duplicated(['line','station_name']).any():
        raise ValueError('Canonical identities must be unique and complete')
    if not assign_station_ids(identities).frame.canonical_station_id.eq(identities.canonical_station_id).all():
        raise ValueError('Canonical identity inconsistent with line/name')
    if policy.get('analysis_crs')!='EPSG:4326' or policy.get('crs_status')!='ANALYTICAL_ASSUMPTION':
        raise ValueError('Task5 requires explicitly approved analytical CRS assumption')
    if policy.get('temporal_status')!='SNAPSHOT_STABILITY_ASSUMPTION':
        raise ValueError('Snapshot assumption must remain explicit')
    if not policy.get('crs_evidence') or not policy.get('temporal_evidence'):
        raise ValueError('Analysis assumptions require evidence')
    absent={(str(r['line']),r['station_name']):r for r in policy.get('known_coordinate_absences',[])}
    openings={(str(r['line']),r['station_name']):r for r in policy.get('known_openings',[])}
    bad_rows={}
    for r in station_result.exceptions.to_dict('records'):
        row=r.get('source_row_id')
        if pd.notna(row):bad_rows.setdefault(row,set()).add(r['exception_code'])
    rows=[]
    for identity in identities.to_dict('records'):
        line,name=str(identity['line']),identity['station_name'];key=(line,name)
        candidates=station_match[station_match.line.astype(str).eq(line)&station_match.station_name.eq(name)&station_match.match_status.ne('station_only')]
        r=candidates.iloc[0] if len(candidates)==1 else None
        mapped=r is not None and r.match_status in ['exact_matched','alias_matched']
        conflict=_true(r.source_code_conflict) if r is not None else False
        out={**identity,'station_coordinate_source':_text(r.get('source_file')) if mapped else '',
             'station_coordinate_source_row_id':r.get('source_row_id',pd.NA) if mapped else pd.NA,
             'station_name_raw_coordinate':_text(r.get('station_name_raw')) if mapped else '',
             'station_code_raw_coordinate':_text(r.get('station_code_raw_station')) if mapped else '',
             'latitude':r.get('latitude',pd.NA) if mapped else pd.NA,'longitude':r.get('longitude',pd.NA) if mapped else pd.NA,
             'identity_status':r.match_status if r is not None else 'ambiguous_or_missing_mapping',
             'source_code_conflict':conflict,'spatial_status':'EXCLUDED_IDENTITY','exclusion_reason':'NO_ADOPTED_UNIQUE_COORDINATE_IDENTITY',
             'crs':policy['analysis_crs'],'crs_status':policy['crs_status'],'crs_evidence':policy['crs_evidence'],
             'source_specific_crs_verified':False,'temporal_status':'NOT_APPLICABLE_NO_ACCEPTED_COORDINATE',
             'temporal_evidence':policy['temporal_evidence'],'known_opening_date':openings.get(key,{}).get('date',''),
             'evidence':'current adopted matcher lacks a unique accepted coordinate mapping; no new alias or KRIC coordinate substitution',
             'code_warning_support_evidence':''}
        if not mapped:
            if key in absent:
                out.update(spatial_status='EXCLUDED_COORDINATE',exclusion_reason='NO_ACCEPTED_COORDINATE',evidence=absent[key]['evidence'])
            if key in openings:
                out.update(temporal_status='KNOWN_2024_OPENING',temporal_evidence=openings[key]['evidence'])
            rows.append(out);continue
        source_id=r.get('source_row_id')
        source_rows=station_result.frame[station_result.frame.source_row_id.eq(source_id)]
        out['evidence']=f"adopted {r.match_status}; coordinate source={out['station_coordinate_source']} row={source_id}; "+_text(r.get('alias_evidence'))
        out['temporal_status']=policy['temporal_status']
        errors=bad_rows.get(source_id,set())
        coords=[out['latitude'],out['longitude']]
        numeric=all(pd.notna(v) and isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in coords)
        bounds=numeric and -90<=coords[0]<=90 and -180<=coords[1]<=180
        if len(source_rows)!=1:
            out.update(spatial_status='EXCLUDED_IDENTITY',exclusion_reason='NONUNIQUE_COORDINATE_SOURCE_ROW')
        elif errors or not bounds:
            collision='DUPLICATE_COORDINATE' in errors
            out.update(spatial_status='EXCLUDED_COORDINATE',exclusion_reason='UNRESOLVED_SOURCE_COORDINATE_COLLISION' if collision else 'INVALID_COORDINATE_OR_SOURCE_RECORD',
                       evidence=out['evidence']+'; cleaner exceptions='+','.join(sorted(errors)))
        elif key in openings and str(openings[key]['date']).startswith('2024'):
            out.update(spatial_status='EXCLUDED_TEMPORAL',exclusion_reason='KNOWN_2024_OPENING_NOT_FULL_YEAR_ELIGIBLE',temporal_status='KNOWN_2024_OPENING',
                       temporal_evidence=openings[key]['evidence'],evidence=out['evidence']+'; '+openings[key]['evidence'])
        elif conflict:
            corroboration=support[support.line.astype(str).eq(line)&support.canonical_station_name.eq(name)]
            corroborated=False
            if len(corroboration)==1:
                c=corroboration.iloc[0]
                name_supported=((c.support_status=='exact' and c.support_name==name)
                    or (c.support_status=='reviewed_name' and bool(_text(c.support_name_relation_evidence).strip())))
                corroborated=(r.match_status=='exact_matched' and out['station_name_raw_coordinate']==name
                    and name_supported
                    and _true(c.support_name_line_identity_verified) and str(c.support_candidate_count)=='1'
                    and bool(_text(c.support_operator).strip()) and bool(_text(c.support_address).strip()))
                if corroborated:
                    out['code_warning_support_evidence']=f"current official KRIC support export={c.support_export_reference}; operator={c.support_operator}; address={c.support_address}; {c.support_name_relation_evidence}; {c.support_reference_url}; codes remain incompatible"
            if corroborated:
                out.update(spatial_status='ELIGIBLE_CODE_WARNING',exclusion_reason='',evidence=out['evidence']+'; '+out['code_warning_support_evidence'])
            else:
                out.update(spatial_status='EXCLUDED_IDENTITY',exclusion_reason='CODE_CONFLICT_NOT_UNIQUELY_CORROBORATED',evidence=out['evidence']+'; exact unique name/line KRIC corroboration unavailable or contradictory')
        else:out.update(spatial_status='ELIGIBLE',exclusion_reason='')
        rows.append(out)
    frame=pd.DataFrame(rows).sort_values(['line','station_name','canonical_station_id'],kind='stable').reset_index(drop=True)
    frame[['latitude','longitude']]=frame[['latitude','longitude']].apply(pd.to_numeric,errors='coerce').astype('Float64')
    frame['station_coordinate_source_row_id']=pd.to_numeric(frame.station_coordinate_source_row_id,errors='coerce').astype('Int64')
    _validate_eligibility(frame)
    return StageResult(frame,[],frame[~frame.spatial_status.isin(ELIGIBLE_STATUSES)].copy())

def _core_status(core,eligibility):
    _validate_eligibility(eligibility)
    status=core.canonical_station_id.map(eligibility.set_index('canonical_station_id').spatial_status)
    if status.isna().any():raise ValueError('Every core identity needs an eligibility status')
    return status

def spatial_subset(core,eligibility):
    """Return a separate subset; never replace/delete rows in the core frame."""
    return core.loc[_core_status(core,eligibility).isin(ELIGIBLE_STATUSES)].copy(deep=True)

def summarize_spatial_eligibility(core,eligibility):
    status=_core_status(core,eligibility)
    if set(core.canonical_station_id)!=set(eligibility.canonical_station_id):
        raise ValueError('Eligibility denominator must equal actual core identity set')
    matched=core.join_status.eq('matched')
    def counts(mask,identity_count):
        return dict(station_identities=int(identity_count),integrated_rows=int(mask.sum()),matched_rows=int((mask&matched).sum()),
                    total_only_rows=int((mask&core.join_status.eq('total_only')).sum()),
                    total_ridership_all_observations=int(core.loc[mask,'total'].sum()),
                    total_ridership_matched_observations=int(core.loc[mask&matched,'total'].sum()),
                    senior_ridership_all_observations=int(core.loc[mask,'senior'].sum()),
                    senior_ridership_matched_observations=int(core.loc[mask&matched,'senior'].sum()))
    denominators=counts(pd.Series(True,index=core.index),len(eligibility))
    by_status={s:counts(status.eq(s),eligibility.spatial_status.eq(s).sum()) for s in STATUSES}
    excluded=counts(~status.isin(ELIGIBLE_STATUSES),(~eligibility.spatial_status.isin(ELIGIBLE_STATUSES)).sum())
    def share(field):return excluded[field]/denominators[field] if denominators[field] else None
    reasons=eligibility[~eligibility.spatial_status.isin(ELIGIBLE_STATUSES)].exclusion_reason.value_counts().sort_index().to_dict()
    reason_by_id=eligibility.set_index('canonical_station_id').exclusion_reason
    by_reason={reason:counts(core.canonical_station_id.map(reason_by_id).eq(reason),number) for reason,number in reasons.items()}
    return dict(task5_status='COMPLETE',completion_mode=COMPLETION_MODE,task9_status='NOT STARTED',
                denominators=denominators,by_status=by_status,exclusions=excluded,exclusion_reasons={k:int(v) for k,v in reasons.items()},by_exclusion_reason=by_reason,
                exclusion_shares=dict(excluded_station_identity_share=share('station_identities'),
                    excluded_total_ridership_share=share('total_ridership_all_observations'),
                    excluded_total_ridership_matched_share=share('total_ridership_matched_observations'),
                    excluded_senior_ridership_share=share('senior_ridership_all_observations'),
                    excluded_senior_ridership_matched_share=share('senior_ridership_matched_observations')),
                core_preserved=True,spatial_subset_statuses=list(ELIGIBLE_STATUSES),
                limitation='eligibility contract finalized; unresolved source problems remain; spatial results need not represent all core station identities')
