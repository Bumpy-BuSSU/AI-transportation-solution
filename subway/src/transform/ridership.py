"""Cardinality-checked age comparison at the original station/hour grain."""
import math
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.transform.station_keys import assign_station_ids
from subway.src.validate.raw_validation import Finding
from subway.src.utils.artifacts import _ordering_column

KEYS=['date','canonical_station_id','hour_bin','boarding_type']
IDENTITY=['line','station_name','hour_start','hour_end']
PROVENANCE=['source_row_id','source_file','station_code_raw','station_name_raw','source_dataset_id',
            'source_hour_column','ridership_raw','source_sequence_raw','crosswalk_status','crosswalk_evidence',
            'alias_applied','alias_evidence']
HOURS={'before_06':(None,6),'after_24':(24,None),**{f'{h:02}_{h+1:02}':(h,h+1) for h in range(6,24)}}


def integrate_ridership(senior: pd.DataFrame,total: pd.DataFrame,rules: dict | None = None) -> StageResult:
    """Retain rejected observations individually, never expand duplicate keys.

    Callers supply Task 2 clean rows and Task 3 verified canonical identities.
    Missing or contradictory identity is not reconstructed from source codes.
    """
    findings=[];prepared=[];required=set(KEYS+IDENTITY+['ridership','source_row_id','source_file','station_code_raw','station_name_raw','source_dataset_id'])
    for label,frame in [('senior',senior),('total',total)]:
        if frame.columns.duplicated().any() or not required.issubset(frame):
            parts=[]
            for side,source in [('senior',senior),('total',total)]:
                part=source.copy(deep=True)
                # Position-qualified names preserve every duplicated-header cell.
                part.columns=[f'{side}_input_{i}_{name}' for i,name in enumerate(source.columns)]
                part['exception_source']=side;parts.append(part)
            bad=pd.concat(parts,ignore_index=True,sort=False)
            bad['join_status']='ambiguous_rejected';bad['exception_code']='INTEGRATION_SCHEMA'
            bad['non_senior']=pd.NA;bad['senior_share']=pd.NA
            return StageResult(bad,[Finding('ERROR','ridership','INTEGRATION_SCHEMA',f'{label}: required schema absent')],bad.copy())
        cols=KEYS+IDENTITY+['ridership']+[c for c in PROVENANCE if c in frame]
        out=frame[cols].copy(deep=True).reset_index(drop=True)
        invalid=pd.Series(False,index=out.index)
        for col in KEYS+['line','station_name','source_row_id','source_file']:
            invalid |= out[col].isna() | out[col].astype('string').str.strip().eq('').fillna(False)
        if not pd.api.types.is_datetime64_any_dtype(out.date):invalid[:]=True
        else:
            invalid |= out.date.ne(out.date.dt.normalize()).fillna(True)
            if rules and 'year' in rules:invalid |= out.date.dt.year.ne(rules['year'])
        invalid |= ~out.line.astype('string').isin([str(n) for n in range(1,9)]) | ~out.boarding_type.isin(['boarding','alighting'])
        pairs=out[['line','station_name','canonical_station_id']].drop_duplicates().reset_index(drop=True)
        expected=assign_station_ids(pairs).frame.canonical_station_id
        bad_ids=pairs.loc[expected.ne(pairs.canonical_station_id).fillna(True),'canonical_station_id']
        invalid |= out.canonical_station_id.isin(bad_ids)
        invalid |= ~out.hour_bin.isin(HOURS)
        for column,index in [('hour_start',0),('hour_end',1)]:
            expected=out.hour_bin.map({k:v[index] for k,v in HOURS.items()}).astype('Float64')
            invalid |= ~(out[column].eq(expected).fillna(False) | (out[column].isna() & expected.isna()))
        if label=='senior':
            if 'crosswalk_status' not in out:invalid[:]=True
            else:invalid |= ~out.crosswalk_status.isin(['exact_matched','alias_matched'])
        numeric=pd.to_numeric(out.ridership,errors='coerce')
        if pd.api.types.is_bool_dtype(numeric):
            numeric=pd.Series(pd.NA,index=out.index,dtype='Int64')
        bad_count=numeric.isna() | numeric.isin([float('inf'),float('-inf')]) | numeric.lt(0) | numeric.mod(1).ne(0) | numeric.ge(2**63)
        out['ridership']=numeric.mask(bad_count).astype('Int64')
        # Preserve source values even when the numeric count cannot be used.
        if 'ridership_raw' not in out:out['ridership_raw']=frame.ridership.reset_index(drop=True)
        invalid |= bad_count
        duplicate=out.duplicated(KEYS,keep=False)
        if duplicate.any():findings.append(Finding('ERROR',label,'DUPLICATE_INTEGRATION_KEY',f'{int(duplicate.sum())} duplicate-key source rows rejected'))
        if invalid.any():findings.append(Finding('ERROR',label,'INVALID_INTEGRATION_ROW',f'{int(invalid.sum())} invalid counts/identity/hour/provenance rows rejected'))
        prepared.append((out,invalid | duplicate))

    # Quarantine the counterpart of every rejected key as well: no false valid
    # match or many-to-many product. Null-key rows remain individually rejected.
    rejected_keys=pd.concat([f.loc[bad,KEYS] for f,bad in prepared],ignore_index=True).drop_duplicates()
    rejected_index=pd.MultiIndex.from_frame(rejected_keys)
    valid=[];rejected=[]
    for label,(frame,bad) in zip(['senior','total'],prepared):
        bad=bad | pd.MultiIndex.from_frame(frame[KEYS]).isin(rejected_index)
        rename={c:label+'_'+c for c in frame if c not in KEYS+IDENTITY}
        rename['ridership']=label
        table=frame.rename(columns=rename)
        valid.append(table.loc[~bad])
        if bad.any():
            part=table.loc[bad].copy();part['join_status']='ambiguous_rejected';part['exception_source']=label
            rejected.append(part)
    merged=valid[0].merge(valid[1],on=KEYS,how='outer',validate='one_to_one',suffixes=('_senior','_total'),indicator=True)
    merged['join_status']=merged['_merge'].astype('string').map({'both':'matched','left_only':'senior_only','right_only':'total_only'})
    for column in IDENTITY:
        merged[column]=merged[column+'_senior'].combine_first(merged[column+'_total'])
    # A canonical identity cannot legitimately disagree across the same key.
    conflict=pd.Series(False,index=merged.index)
    for column in IDENTITY:
        a,b=merged[column+'_senior'],merged[column+'_total']
        if isinstance(a.dtype,pd.CategoricalDtype) or isinstance(b.dtype,pd.CategoricalDtype):
            a,b=a.astype('string'),b.astype('string')
        conflict |= merged['_merge'].eq('both') & ~(a.eq(b).fillna(False) | (a.isna() & b.isna()))
    if conflict.any():
        findings.append(Finding('ERROR','ridership','INTEGRATION_IDENTITY_CONFLICT',f'{int(conflict.sum())} matched identity/hour conflicts'))
        merged.loc[conflict,'join_status']='ambiguous_rejected'
    merged=merged.drop(columns=['_merge']+[c+suffix for c in IDENTITY for suffix in ['_senior','_total']])
    if rejected:merged=pd.concat([merged,*rejected],ignore_index=True,sort=False)
    merged['senior']=merged['senior'].astype('Int64');merged['total']=merged['total'].astype('Int64')
    matched=merged.join_status.eq('matched')
    excess=(matched & merged.senior.gt(merged.total)).fillna(False)
    safe=(matched & merged.senior.notna() & merged.total.notna() & merged.senior.le(merged.total)).fillna(False)
    merged['non_senior']=(merged.total-merged.senior).where(safe).astype('Int64')
    merged['senior_share']=(merged.senior.astype('Float64')/merged.total.astype('Float64')).where(safe & merged.total.gt(0)).astype('Float64')
    merged['difference']=(merged.senior-merged.total).where(excess).astype('Int64')
    merged['exception_code']=pd.Series('',index=merged.index,dtype='string')
    merged.loc[merged.join_status.eq('ambiguous_rejected'),'exception_code']='AMBIGUOUS_REJECTED'
    merged.loc[excess,'exception_code']='SENIOR_EXCEEDS_TOTAL'
    if excess.any():
        p=(rules or {}).get('senior_excess_policy',{})
        anomalous=merged.loc[excess]
        count=int(excess.sum());denominator=int(matched.sum());severity='ERROR'
        try:
            limits=[p[k] for k in ['count_threshold','rate_threshold','profile_hour_threshold','recurrence_date_threshold']]
            if p.get('status')!='adopted' or any(v is None or isinstance(v,bool) or not math.isfinite(v) or v<=0 for v in limits) or p['rate_threshold']>1:
                raise ValueError('unverified policy')
            profile=anomalous.groupby(['date','canonical_station_id','boarding_type'],observed=True).hour_bin.nunique().max()
            recurrence=anomalous.groupby(['canonical_station_id','hour_bin','boarding_type'],observed=True).date.nunique().max()
            structural=(count>=p['count_threshold'] or count/denominator>=p['rate_threshold'] or profile>=p['profile_hour_threshold'] or recurrence>=p['recurrence_date_threshold'])
            severity='ERROR' if structural else 'WARNING'
        except (KeyError,TypeError,ValueError):
            findings.append(Finding('ERROR','ridership','EXCESS_POLICY_UNVERIFIED','senior excess requires an adopted quality policy'))
        findings.append(Finding(severity,'ridership','SENIOR_EXCEEDS_TOTAL',f'{count}/{denominator} valid matched cells; values preserved and derived values null'))
    # Typed unique keys handle every accepted row. Rejected duplicates require
    # source provenance as deterministic tie breakers; consumers honor ERROR.
    order=KEYS+['join_status']+[c for c in ['exception_source','senior_source_row_id','total_source_row_id','senior_station_code_raw','total_station_code_raw'] if c in merged]
    rejected_mask=merged.join_status.eq('ambiguous_rejected')
    if rejected_mask.any():
        # Accepted million-row tables use the small canonical key. Only the
        # exceptional rejected table needs payload ties for corrupt provenance.
        rejected_table=merged.loc[rejected_mask].reset_index(drop=True)
        ties=pd.DataFrame({i:_ordering_column(rejected_table[c]) for i,c in enumerate(order+[c for c in rejected_table if c not in order])})
        positions=ties.sort_values(list(ties.columns),kind='stable',na_position='last').index
        merged=pd.concat([merged.loc[~rejected_mask],rejected_table.iloc[positions]],ignore_index=True,sort=False)
    merged=merged.sort_values(order,kind='stable',na_position='last').reset_index(drop=True)
    exceptions=merged.loc[merged.exception_code.ne('')].copy().reset_index(drop=True)
    return StageResult(merged,findings,exceptions)
