"""Descriptive analysis only; no extreme classification or fitted model."""
import numpy as np
import pandas as pd
from subway.src.transform.ridership import KEYS,HOURS

TEMPERATURES=['temperature_mean','temperature_max','temperature_min']
WEATHER=TEMPERATURES+['precipitation','wind_max','wind_mean','humidity_mean','snow_new_max','snow_depth_max']
DAYTIME=[f'{h:02}_{h+1:02}' for h in range(10,16)]
QUANTILES=[.01,.05,.10,.25,.50,.75,.90,.95,.99]


def distribution(values):
    x=pd.to_numeric(values,errors='raise').dropna().astype(float)
    def number(value):return float(value) if pd.notna(value) and np.isfinite(value) else None
    result=dict(valid_n=len(x),missing_n=int(values.isna().sum()),mean=number(x.mean()),sd=number(x.std(ddof=1)),
        variance=number(x.var(ddof=1)),minimum=number(x.min()),maximum=number(x.max()))
    result.update({f'p{int(q*100):02}':number(x.quantile(q,interpolation='linear')) for q in QUANTILES})
    return result


def temperature_bins(values,number=10):
    """Weather-only linear quantiles; repeated edges collapse, ties never split."""
    clean=values.dropna().astype(float)
    edges=np.unique(clean.quantile(np.linspace(0,1,number+1),interpolation='linear').to_numpy()).tolist()
    if not edges:return pd.Series(pd.NA,index=values.index,dtype='Int64'),[]
    if len(edges)==1:return pd.Series(0,index=values.index,dtype='Int64').where(values.notna()),edges
    return pd.cut(values,bins=edges,labels=False,include_lowest=True,right=True).astype('Int64'),edges


def _unique(frame,key,name):
    if frame[key].isna().any().any() or frame.duplicated(key).any():raise ValueError(f'{name}: null or duplicate join key')


def build_eda(core,master,mapping,weather,year):
    """Preserve every current-area cell, flag invalid metrics, aggregate safe cells."""
    _unique(core,KEYS,'core');_unique(master,['canonical_station_id'],'master')
    _unique(mapping,['canonical_station_id'],'mapping');_unique(weather,['date'],'weather')
    if not pd.api.types.is_datetime64_any_dtype(core.date) or not pd.api.types.is_datetime64_any_dtype(weather.date):raise ValueError('date must be datetime')
    for frame in [core,weather]:
        if not frame.date.dt.year.eq(year).all() or not frame.date.eq(frame.date.dt.normalize()).all():raise ValueError('year/date alignment')
    if not set(core.canonical_station_id).issubset(set(master.canonical_station_id)):raise ValueError('core identity absent from master')
    joined=master[['canonical_station_id','study_area_status','spatial_status']].merge(
        mapping[['canonical_station_id','study_area_status','mapping_status','ADM_CD']],on='canonical_station_id',how='outer',validate='one_to_one',suffixes=('_master','_map'),indicator=True)
    both=joined['_merge'].eq('both')
    if joined['_merge'].eq('right_only').any() or not joined.loc[both,'study_area_status_master'].eq(joined.loc[both,'study_area_status_map']).all():raise ValueError('membership disagreement')
    inside=joined.study_area_status_master.eq('IN_CURRENT_STUDY_AREA')
    if not (joined.loc[inside,'mapping_status'].eq('MAPPED') & joined.loc[inside,'spatial_status'].isin(['ELIGIBLE','ELIGIBLE_CODE_WARNING']) & joined.loc[inside,'ADM_CD'].notna()).all():raise ValueError('current identity has no valid mapping')
    ids=joined.loc[inside,'canonical_station_id']
    if ids.empty:raise ValueError('empty current-study-area sample')
    required=KEYS+['hour_start','hour_end','senior','total','non_senior','senior_share','join_status','exception_code']
    base=core.loc[core.canonical_station_id.isin(ids),required].copy()
    if base.empty:raise ValueError('empty current-study-area observations')
    actual=base[['hour_bin','hour_start','hour_end']].drop_duplicates()
    if not set(DAYTIME).issubset(set(actual.hour_bin)):raise ValueError('exact10-16 intervals absent')
    for row in actual.itertuples():
        if row.hour_bin not in HOURS:raise ValueError('unknown hour_bin')
        expected=HOURS[row.hour_bin]
        for a,b in zip([row.hour_start,row.hour_end],expected):
            if not ((pd.isna(a) and b is None) or (pd.notna(a) and a==b)):raise ValueError('hour interval differs from source contract')
    base['daytime_10_16']=base.hour_bin.isin(DAYTIME)
    matched=base.join_status.eq('matched')
    excess=(matched & base.senior.gt(base.total)).fillna(False)
    safe=(matched & base.senior.notna() & base.total.notna() & base.senior.ge(0) & base.total.ge(0) & base.senior.le(base.total) & base.non_senior.notna()).fillna(False)
    if not base.loc[safe,'non_senior'].eq(base.loc[safe,'total']-base.loc[safe,'senior']).all():raise ValueError('derived age counts disagree')
    if base.loc[excess,['non_senior','senior_share']].notna().any().any():raise ValueError('excess null policy violated')
    positive=safe & base.total.gt(0)
    if base.loc[positive,'senior_share'].isna().any() or not np.allclose(base.loc[positive,'senior_share'].astype(float), (base.loc[positive,'senior']/base.loc[positive,'total']).astype(float),rtol=1e-12,atol=0):raise ValueError('share policy violated')
    if base.loc[safe & base.total.eq(0),'senior_share'].notna().any():raise ValueError('zero denominator share policy violated')
    base['age_comparison_valid']=safe
    w=weather[['date','station_id']+WEATHER].copy().sort_values('date').reset_index(drop=True)
    if not w.station_id.astype(str).eq('108').all():raise ValueError('current weather requires approved ASOS108')
    base=base.merge(w,on='date',how='left',validate='many_to_one',indicator='_weather_join')
    if not base._weather_join.eq('both').all():raise ValueError('weather date missing for current-area observations')
    base=base.drop(columns='_weather_join').sort_values(KEYS,kind='stable').reset_index(drop=True)
    base['weekday']=base.date.dt.dayofweek;base['weekend']=base.weekday.ge(5)
    valid=base.loc[base.age_comparison_valid]
    invalid_matched=int((matched & ~safe & ~excess).sum())
    sample=dict(original_core_rows=len(core),original_core_stations=int(core.canonical_station_id.nunique()),
        current_study_area_rows=len(base),current_study_area_stations=int(base.canonical_station_id.nunique()),
        outside_or_unresolved_rows=len(core)-len(base),matched_rows=int(matched.sum()),
        unmatched_rows=int((~matched).sum()),senior_exceeds_total_rows=int(excess.sum()),
        other_invalid_matched_rows=invalid_matched,valid_age_comparison_rows=len(valid),
        zero_total_valid_rows=int(valid.total.eq(0).sum()))
    stages=[('original_core',len(core),int(core.canonical_station_id.nunique()),0,'all approved Stage2 observations'),
        ('current_study_area',len(base),sample['current_study_area_stations'],len(core)-len(base),'exclude only from current analysis scope; full core unchanged'),
        ('matched',int(matched.sum()),int(base.loc[base.join_status.eq('matched'),'canonical_station_id'].nunique()),int((~matched).sum()),'unmatched kept in base; excluded from age-comparison metrics'),
        ('valid_age_comparison',len(valid),int(valid.canonical_station_id.nunique()),int(matched.sum())-len(valid),'excess/invalid matched kept in base; derived null preserved')]
    tables={'eda_sample_accounting.csv':pd.DataFrame(stages,columns=['stage','rows','stations','excluded_from_previous','reason'])}
    scope=core[['canonical_station_id']].merge(master[['canonical_station_id','study_area_status']],on='canonical_station_id',validate='many_to_one')
    excluded=[]
    for reason,frame in scope.loc[scope.study_area_status.ne('IN_CURRENT_STUDY_AREA')].groupby('study_area_status',observed=True):
        excluded.append(dict(stage='current_study_area',reason=reason,rows=len(frame),stations=int(frame.canonical_station_id.nunique())))
    for reason,frame in base.loc[base.join_status.ne('matched')].groupby('join_status',observed=True):
        excluded.append(dict(stage='matched',reason=reason,rows=len(frame),stations=int(frame.canonical_station_id.nunique())))
    for reason,mask in [('SENIOR_EXCEEDS_TOTAL',excess),('OTHER_INVALID_MATCHED',matched & ~safe & ~excess)]:
        if mask.any():excluded.append(dict(stage='valid_age_comparison',reason=reason,rows=int(mask.sum()),stations=int(core.loc[mask.index[mask],'canonical_station_id'].nunique())))
    tables['eda_exclusions.csv']=pd.DataFrame(excluded,columns=['stage','reason','rows','stations']).sort_values(['stage','reason']).reset_index(drop=True)
    tables['eda_weather_summary.csv']=pd.DataFrame([dict(variable=c,unit='degC' if c in TEMPERATURES else {'precipitation':'mm','wind_max':'m/s','wind_mean':'m/s','humidity_mean':'percent','snow_new_max':'cm','snow_depth_max':'cm'}[c],**distribution(w[c])) for c in WEATHER])
    tails=[]
    for c in TEMPERATURES:
        x=w[c].dropna()
        for q in [.01,.05,.10,.90,.95,.99]:
            value=float(x.quantile(q)) if len(x) else None
            tails.append(dict(variable=c,percentile=q,candidate_value=value,valid_days=len(x),missing_days=int(w[c].isna().sum()),
                days_strictly_below=int(x.lt(value).sum()) if value is not None else 0,days_strictly_above=int(x.gt(value).sum()) if value is not None else 0,status='DIAGNOSTIC ONLY; NOT ADOPTED'))
    tables['eda_temperature_quantiles.csv']=pd.DataFrame(tails)
    counts=[]
    for c in ['senior','non_senior']:
        stats=distribution(valid[c]);mean=stats['mean'];variance=stats['variance'];n=len(valid)
        counts.append(dict(age_group=c,observation_count=n,total_ridership=int(valid[c].sum()),zero_count=int(valid[c].eq(0).sum()),zero_rate=float(valid[c].eq(0).mean()) if n else None,
            variance_mean_ratio=variance/mean if mean and variance is not None else None,**stats))
    tables['eda_count_diagnostics.csv']=pd.DataFrame(counts)
    daily=valid.groupby('date',observed=True)[['senior','non_senior','total']].sum(min_count=1).rename(columns={c:c+'_daily' for c in ['senior','non_senior','total']})
    daily=daily.join(valid.groupby('date',observed=True).size().rename('valid_age_comparison_rows'))
    all_daily=base.groupby('date',observed=True)[['senior','total']].sum(min_count=1).rename(columns={'senior':'senior_all_current','total':'total_all_current'})
    all_daily=all_daily.join(base.groupby('date',observed=True).size().rename('current_rows'))
    daily=all_daily.join(daily).reset_index().merge(w,on='date',how='left',validate='one_to_one')
    daily['senior_share']=daily.senior_daily/daily.total_daily.where(daily.total_daily.gt(0))
    daily['weekday']=daily.date.dt.dayofweek;daily['weekend']=daily.weekday.ge(5)
    daily=daily.sort_values('date').reset_index(drop=True)
    tables['eda_daily_age_weather.csv']=daily
    calendar=daily.groupby('weekend',observed=True).agg(days=('date','size'),senior_daily_mean=('senior_daily','mean'),non_senior_daily_mean=('non_senior_daily','mean'),total_daily_mean=('total_daily','mean')).reset_index()
    tables['eda_calendar_profile.csv']=calendar
    hourly=valid.groupby(['hour_bin','hour_start','hour_end','boarding_type','daytime_10_16'],observed=True,dropna=False).agg(senior_ridership=('senior','sum'),non_senior_ridership=('non_senior','sum'),total_ridership=('total','sum'),valid_rows=('date','size')).reset_index()
    hourly['senior_share']=hourly.senior_ridership/hourly.total_ridership.where(hourly.total_ridership.gt(0))
    for c in ['senior','non_senior']:
        denominator=hourly.groupby('boarding_type',observed=True)[c+'_ridership'].transform('sum')
        hourly[c+'_within_direction_share']=hourly[c+'_ridership']/denominator.where(denominator.gt(0))
    hourly['hour_order']=hourly.hour_bin.map({'before_06':0,**{f'{h:02}_{h+1:02}':h for h in range(6,24)},'after_24':24}).astype('Int64')
    tables['eda_hourly_profile.csv']=hourly.sort_values(['hour_order','boarding_type']).reset_index(drop=True)
    station=valid.groupby('canonical_station_id',observed=True).agg(total_ridership=('total','sum'),senior_ridership=('senior','sum'),non_senior_ridership=('non_senior','sum'),valid_rows=('date','size')).reset_index()
    full_station=base.groupby('canonical_station_id',observed=True).agg(total_all_current=('total','sum'),senior_all_current=('senior','sum'),current_rows=('date','size')).reset_index()
    station=full_station.merge(station,on='canonical_station_id',how='left',validate='one_to_one')
    station['senior_share']=station.senior_ridership/station.total_ridership.where(station.total_ridership.gt(0))
    tables['eda_station_summary.csv']=station.sort_values('canonical_station_id').reset_index(drop=True)
    tables['eda_station_distribution.csv']=pd.DataFrame([dict(variable=c,**distribution(station[c])) for c in ['total_ridership','senior_ridership','non_senior_ridership','senior_share']])
    profiles=[];edges={}
    for c in ['temperature_max','temperature_min']:
        bins,e=temperature_bins(w[c]);edges[c]=e
        assignment=pd.DataFrame(dict(date=w.date,temperature_bin=bins))
        data=daily.merge(assignment,on='date',validate='one_to_one')
        group=data.groupby('temperature_bin',observed=True,dropna=True)
        p=group.agg(days=('date','size'),temperature_mean=(c,'mean'),temperature_min=(c,'min'),temperature_max=(c,'max'),
            weekend_fraction=('weekend','mean'),senior_daily_sum=('senior_daily','sum'),senior_daily_mean=('senior_daily','mean'),
            non_senior_daily_sum=('non_senior_daily','sum'),non_senior_daily_mean=('non_senior_daily','mean'),total_daily_sum=('total_daily','sum'),
            senior_valid_days=('senior_daily','count'),non_senior_valid_days=('non_senior_daily','count')).reset_index()
        p['weather_variable']=c
        for age in ['senior','non_senior']:
            annual=daily[age+'_daily'].mean();p[age+'_relative_index']=p[age+'_daily_mean']/annual*100 if annual else np.nan
        profiles.append(p)
    tables['eda_temperature_profiles.csv']=pd.concat(profiles,ignore_index=True)
    summary=dict(year=year,status='EDA COMPLETE',stage2_status='HUMAN APPROVED',sample=sample,daytime_bins=DAYTIME,
        actual_hour_bins=actual.sort_values('hour_bin').hour_bin.tolist(),temperature_columns=TEMPERATURES,weather_days=len(w),
        unused_weather_dates=int((~w.date.isin(base.date)).sum()),temperature_bin_edges=edges,
        quantile_rule='linear interpolation; strict below/above tails; diagnostics only',
        temperature_bin_rule='10 weather-only equal-frequency quantile intervals; duplicate edges collapsed; equal temperatures unsplit; right-closed, first includes min',
        metric_denominator='common valid age-comparison cells; all-current senior/total retained separately; boarding and alighting are counts, not unique trips',
        normalization='100 = each age group mean daily valid-cell ridership across all current sample dates',
        variance_rule='sample variance and SD, ddof=1',extreme_threshold_status='NOT ADOPTED',hypothesis_test='NOT PERFORMED',regression='NOT FITTED',policy_conclusion='NONE',human_eda_review='PENDING')
    return base,tables,summary
