"""Frozen Stage3C model; controlled reconstruction with an approved failure gate."""
from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
import yaml

from subway.src.analysis.confirmatory import holm_adjust

MODERATORS = ['senior_population_share', 'shelters_per_10k']
TARGETS = [f'{extreme}_x_z_{moderator}' for moderator in MODERATORS for extreme in ['hot','cold']]
FAILURE = 'NOT_ESTIMABLE_INVALID_TWOWAY_COVARIANCE'
THRESHOLDS = {
    'hot_primary': {'variable':'temperature_max','quantile':.9,'threshold_c':32.75,'operator':'ge'},
    'cold_primary': {'variable':'temperature_min','quantile':.1,'threshold_c':-3.05,'operator':'le'},
    'hot_sensitivity': {'variable':'temperature_max','quantile':.95,'threshold_c':33.675,'operator':'ge'},
    'cold_sensitivity': {'variable':'temperature_min','quantile':.05,'threshold_c':-4.8,'operator':'le'},
}


def validate_spatial_heterogeneity_config(profile: dict, year: int) -> dict:
    frozen = dict(reference_year=2024,study_area_id='seoul_2024',primary_event='boarding',
        age_comparison_rule='common_valid_cells',moderators=MODERATORS,
        expected_stations=243,expected_station_dongs=173,expected_seoul_dongs=426,
        shelter_crs='EPSG:5186',boundary_crs='EPSG:5179',
        standardization='unique_station_dongs_ddof_1',model='ols_log_ratio_station_date_fe',
        calendar_controls='moderator_x_month_and_dow',calendar_reference={'month':1,'dow':0},
        covariance='ADM_CD_date_two_way_cluster',use_correction=False,
        multiple_testing={'method':'holm','alpha':.05,'family_size':4},layer_a='descriptive_only',
        daytime_spatial_analysis=False,moran_lisa=False,station_significance_mining=False,
        causal_policy_conclusion=False,
        sensitivity_failure_protocol={'provenance':'human_approved_post_gate_amendment_not_originally_prespecified',
            'scope':'entire_four_target_inferential_layer','reason':FAILURE}, **THRESHOLDS)
    if year != 2024 or not isinstance(profile,dict):raise ValueError('frozen 2024 Stage3C contract required')
    for key,value in frozen.items():
        if profile.get(key) != value:raise ValueError(f'Stage3C scientific contract drift: {key}')
    return profile


def load_spatial_heterogeneity_config(repo_root: Path, year: int) -> dict:
    config=yaml.safe_load((Path(repo_root)/f'subway/config/spatial_heterogeneity_{year}.yaml').read_text(encoding='utf-8'))
    validate_spatial_heterogeneity_config(config,year)
    prior=yaml.safe_load((Path(repo_root)/f'subway/config/confirmatory_analysis_{year}.yaml').read_text(encoding='utf-8'))
    if any(config[k] != prior[k] for k in THRESHOLDS):raise ValueError('Stage3B threshold continuity drift')
    return config


def build_spatial_context(station_map, population_boundary, shelters, config):
    boundary=population_boundary.copy(deep=True).sort_values('ADM_CD').reset_index(drop=True)
    if boundary.crs is None or boundary.crs.to_epsg()!=5179:raise ValueError('boundary CRS must be EPSG:5179')
    if boundary.ADM_CD.isna().any() or boundary.ADM_CD.duplicated().any():raise ValueError('boundary keys invalid')
    if (boundary.geometry.isna().any() or boundary.geometry.is_empty.any() or not boundary.geometry.is_valid.all()
        or not boundary.geometry.geom_type.isin(['Polygon','MultiPolygon']).all()):raise ValueError('invalid boundary geometry; no repair')
    if not np.isfinite(boundary[['population_total','population_65_plus']].to_numpy(float)).all():raise ValueError('invalid population')
    if (boundary.population_total.le(0).any() or boundary.population_65_plus.lt(0).any()
        or boundary.population_65_plus.gt(boundary.population_total).any()):raise ValueError('nonpositive/invalid population')
    share=boundary.population_65_plus/boundary.population_total
    if not np.allclose(boundary.senior_population_share,share,rtol=1e-12,atol=0):raise ValueError('population share drift')
    stations=station_map.loc[station_map.study_area_status.eq('IN_CURRENT_STUDY_AREA')].copy(deep=True)
    if stations.empty or not stations.mapping_status.eq('MAPPED').all():raise ValueError('current stations must be authoritatively mapped')
    if stations.canonical_station_id.duplicated().any() or stations.ADM_CD.isna().any():raise ValueError('station identity ambiguity')
    if not stations.ADM_CD.isin(boundary.ADM_CD).all():raise ValueError('station dong absent')
    if not np.isfinite(stations[['x_5179','y_5179']].to_numpy(float)).all():raise ValueError('invalid projected station coordinates')
    if shelters.crs is None or shelters.crs.to_string()!=config.get('shelter_crs','EPSG:5186'):raise ValueError('approved shelter source CRS required')
    if shelters.geometry.isna().any() or shelters.geometry.is_empty.any() or not shelters.geometry.geom_type.eq('Point').all():
        raise ValueError('shelter geometry schema invalid')
    points=shelters.to_crs(5179).copy()
    records=[];mapped=[];valid_points=[]
    for i,row in points.iterrows():
        point=row.geometry
        source_id=row.get('source_row_id',i)
        if not np.isfinite([point.x,point.y]).all():
            status='INVALID_COORDINATE';candidates=[]
        else:
            valid_points.append(point)
            candidates=list(boundary.sindex.query(point,predicate='within'))
            if len(candidates)==1:status='MAPPED';mapped.append(boundary.iloc[candidates[0]].ADM_CD)
            elif len(candidates)>1:status='MULTIPLE_MATCH'
            elif boundary.geometry.touches(point).any():status='BOUNDARY_POINT'
            else:status='ZERO_MATCH'
        if status!='MAPPED':records.append(dict(source_row_id=source_id,mapping_status=status,
            mapping_reason='STRICT_PIP_NO_REPAIR_OR_FALLBACK',x_5179=point.x,y_5179=point.y,
            candidate_ADM_CD=';'.join(sorted(boundary.iloc[candidates].ADM_CD.astype(str)))))
    counts=pd.Series(mapped,dtype='str').value_counts()
    dong=boundary.drop(columns='geometry').copy()
    dong['mapped_shelter_count']=dong.ADM_CD.map(counts).fillna(0).astype(int)
    dong['shelters_per_10k']=dong.mapped_shelter_count/dong.population_total*10000
    dong['analyzed_station_count']=dong.ADM_CD.map(stations.ADM_CD.value_counts()).fillna(0).astype(int)
    dong['has_analyzed_station']=dong.analyzed_station_count.gt(0)
    unique=dong.loc[dong.has_analyzed_station]
    stats={}
    for moderator in MODERATORS:
        mean=float(unique[moderator].mean());sd=float(unique[moderator].std(ddof=1))
        if not np.isfinite(sd) or sd<=0:raise ValueError('unidentified constant moderator')
        dong[f'z_{moderator}']=(dong[moderator]-mean)/sd
        stats[moderator]={'mean':mean,'sample_sd':sd,'ddof':1,'dongs':len(unique)}
    attach=['ADM_CD','mapped_shelter_count','shelters_per_10k','population_total','population_65_plus','senior_population_share']+[f'z_{m}' for m in MODERATORS]
    stations=stations.drop(columns=[c for c in attach if c!='ADM_CD' and c in stations]).merge(dong[attach],on='ADM_CD',validate='many_to_one')
    if not valid_points:raise ValueError('no coordinate-valid shelters for descriptive distance')
    coords=np.array([[p.x,p.y] for p in valid_points])
    station_xy=stations[['x_5179','y_5179']].to_numpy(float)
    stations['nearest_shelter_distance_m']=np.sqrt(((station_xy[:,None,:]-coords[None,:,:])**2).sum(axis=2)).min(axis=1)
    exceptions=pd.DataFrame(records,columns=['source_row_id','mapping_status','mapping_reason','x_5179','y_5179','candidate_ADM_CD']).sort_values(['mapping_status','source_row_id']).reset_index(drop=True)
    qa=dict(raw_shelters=len(shelters),mapped_shelters=len(mapped),
        zero_match=int(exceptions.mapping_status.eq('ZERO_MATCH').sum()),boundary_point=int(exceptions.mapping_status.eq('BOUNDARY_POINT').sum()),
        multiple_match=int(exceptions.mapping_status.eq('MULTIPLE_MATCH').sum()),invalid_coordinate=int(exceptions.mapping_status.eq('INVALID_COORDINATE').sum()),
        mapped_percent=100*len(mapped)/len(shelters) if len(shelters) else 0,
        standardization=stats,moderator_correlation=float(unique[MODERATORS].corr().iloc[0,1]),
        analysis_stations=len(stations),station_dongs=len(unique),seoul_dongs=len(dong))
    for key,col in [('expected_stations','analysis_stations'),('expected_station_dongs','station_dongs'),('expected_seoul_dongs','seoul_dongs')]:
        if key in config and config[key]!=qa[col]:raise ValueError(f'Stage3C sample gate: {col}')
    return dong,stations.sort_values('canonical_station_id').reset_index(drop=True),exceptions,qa


def _balanced(frame):
    keys=['canonical_station_id','date']
    if frame.empty or frame.duplicated(keys).any() or frame[keys].isna().any().any():raise ValueError('station-date keys invalid')
    if len(frame)!=frame.canonical_station_id.nunique()*frame.date.nunique():raise ValueError('unbalanced station-date panel')


def build_station_day_panel(base,station_context,config,year):
    boarding=base.loc[base.boarding_type.eq('boarding')].copy()
    keys=['canonical_station_id','date','hour_bin']
    if boarding.duplicated(keys).any():raise ValueError('duplicate source cell')
    if station_context.canonical_station_id.duplicated().any():raise ValueError('duplicate context identity')
    if set(boarding.canonical_station_id)!=set(station_context.canonical_station_id):raise ValueError('base/context population mismatch')
    valid=boarding.loc[boarding.age_comparison_valid.eq(True)].copy()
    values=valid[['senior','total','non_senior']].to_numpy(float)
    if not np.isfinite(values).all() or (values<0).any() or valid.senior.gt(valid.total).any():raise ValueError('invalid common-support age counts')
    if not np.allclose(valid.non_senior,valid.total-valid.senior,rtol=0,atol=0):raise ValueError('derived age-count contract drift')
    panel=valid.groupby(['canonical_station_id','date'],observed=True).agg(senior=('senior','sum'),non_senior=('non_senior','sum'),support_cells=('senior','size')).reset_index()
    if set(panel.canonical_station_id)!=set(station_context.canonical_station_id):
        raise ValueError('required station has no common-valid boarding support')
    _balanced(panel)
    expected=pd.date_range(f'{year}-01-01',f'{year}-12-31')
    if set(panel.date)!=set(expected):raise ValueError('incomplete annual date coverage')
    if panel.senior.le(0).any() or panel.non_senior.le(0).any():raise ValueError('zero age station-day blocks log ratio; no pseudocount')
    panel['log_ratio']=np.log(panel.senior/panel.non_senior)
    weather=boarding[['date','temperature_max','temperature_min']].drop_duplicates()
    if weather.date.duplicated().any() or not np.isfinite(weather[['temperature_max','temperature_min']].to_numpy(float)).all():raise ValueError('invalid citywide daily weather')
    panel=panel.merge(weather,on='date',validate='many_to_one').merge(station_context,on='canonical_station_id',validate='many_to_one')
    if panel[['ADM_CD','z_senior_population_share','z_shelters_per_10k']].isna().any().any():raise ValueError('missing station context')
    for key in THRESHOLDS:
        rule=config[key];series=panel[rule['variable']]
        panel[key]=(series.ge(rule['threshold_c']) if rule['operator']=='ge' else series.le(rule['threshold_c'])).astype(int)
    panel['month']=panel.date.dt.month;panel['dow']=panel.date.dt.dayofweek
    return panel.sort_values(['canonical_station_id','date']).reset_index(drop=True)


def _calendar(frame):
    return pd.concat([pd.get_dummies(frame.month,prefix='month',drop_first=True,dtype=float),
        pd.get_dummies(frame.dow,prefix='dow',drop_first=True,dtype=float)],axis=1)


def fit_station_heterogeneity(panel):
    _balanced(panel);rows=[]
    for station,frame in panel.sort_values(['canonical_station_id','date']).groupby('canonical_station_id',observed=True):
        x=pd.concat([pd.Series(1.,index=frame.index,name='constant'),frame[['hot_primary','cold_primary']],_calendar(frame)],axis=1).astype(float)
        if np.linalg.matrix_rank(x)!=x.shape[1]:raise ValueError('Layer A design rank deficient')
        beta=np.linalg.lstsq(x.to_numpy(),frame.log_ratio.to_numpy(),rcond=None)[0]
        rows.append(dict(canonical_station_id=station,ADM_CD=frame.ADM_CD.iloc[0],beta_hot=float(beta[1]),beta_cold=float(beta[2]),valid_days=len(frame)))
    return pd.DataFrame(rows)


def design_spatial_moderation(panel,*,hot,cold):
    if (hot,cold) not in [('hot_primary','cold_primary'),('hot_sensitivity','cold_sensitivity')]:raise ValueError('unapproved extreme specification')
    x=pd.DataFrame(index=panel.index)
    for moderator in MODERATORS:
        z=panel[f'z_{moderator}']
        x[f'hot_x_z_{moderator}']=panel[hot]*z
        x[f'cold_x_z_{moderator}']=panel[cold]*z
    calendar=_calendar(panel)
    for moderator in MODERATORS:
        for col in calendar:
            x[f'z_{moderator}_x_{col}']=panel[f'z_{moderator}']*calendar[col]
    if not np.isfinite(x.to_numpy(float)).all():raise ValueError('nonfinite moderation design')
    return x.astype(float)


def absorb_station_date_fe(frame,columns):
    _balanced(frame)
    x=frame[columns].astype(float)
    return x-x.groupby(frame.canonical_station_id,observed=True).transform('mean')-x.groupby(frame.date,observed=True).transform('mean')+x.mean()


def fit_spatial_moderation(panel,*,hot,cold,threshold_label):
    sensitivity=(hot,cold,threshold_label)==('hot_sensitivity','cold_sensitivity','p95/p05')
    if not sensitivity and (hot,cold,threshold_label)!=('hot_primary','cold_primary','p90/p10'):raise ValueError('unapproved threshold/model label')
    panel=panel.sort_values(['canonical_station_id','date']).reset_index(drop=True)
    x=design_spatial_moderation(panel,hot=hot,cold=cold)
    a=absorb_station_date_fe(pd.concat([panel[['canonical_station_id','date','log_ratio']],x],axis=1),['log_ratio']+list(x))
    rank=int(np.linalg.matrix_rank(a[x.columns].to_numpy()))
    if rank!=len(x.columns):raise ValueError('joint moderation rank deficient; no single-moderator fallback')
    group1=pd.factorize(panel.ADM_CD,sort=True)[0];group2=pd.factorize(panel.date,sort=True)[0]
    if min(len(np.unique(group1)),len(np.unique(group2)))<2:raise ValueError('insufficient cluster dimensions')
    fit=sm.OLS(a.log_ratio,a[x.columns]).fit()
    covariance=cov_cluster_2groups(fit,group1,group2,use_correction=False)[0]
    variances=np.diag(covariance)[:4]
    invalid=(not np.isfinite(covariance).all()) or (not np.isfinite(variances).all()) or bool((variances<=0).any())
    if invalid and not sensitivity:raise ValueError('invalid primary two-way covariance; scientific gate BLOCKED')
    reason=FAILURE if invalid else None
    rows=[]
    for i,term in enumerate(TARGETS):
        beta=float(fit.params.iloc[i])
        if not np.isfinite(beta):raise ValueError('nonfinite coefficient')
        row=dict(term=term,threshold=threshold_label,beta=beta,se=None,ci95_low=None,ci95_high=None,p_raw=None,
            p_holm=None,holm_reject=None,inference_status='NOT ESTIMABLE' if invalid else 'ESTIMABLE',failure_reason=reason)
        if not invalid:
            se=math.sqrt(float(variances[i]));z=beta/se
            row.update(se=se,ci95_low=beta-1.959963984540054*se,ci95_high=beta+1.959963984540054*se,p_raw=math.erfc(abs(z)/math.sqrt(2)))
        rows.append(row)
    # Retain the untouched covariance, including negative entries; JSON cannot encode NaN/Inf.
    raw=covariance.tolist()
    raw=[[v if math.isfinite(v) else None for v in row] for row in raw]
    meta=dict(nobs=len(panel),stations=int(panel.canonical_station_id.nunique()),rank=rank,design_columns=list(x),
        cluster_counts={'ADM_CD':int(panel.ADM_CD.nunique()),'date':int(panel.date.nunique())},
        covariance='statsmodels.cov_cluster_2groups',use_correction=False,
        raw_covariance=raw,raw_target_variances=[float(v) if np.isfinite(v) else None for v in variances],
        negative_target_variance_count=int((variances<0).sum()),invalid_target_variance_count=int((~np.isfinite(variances)|(variances<=0)).sum()),
        covariance_all_finite=bool(np.isfinite(covariance).all()),covariance_repaired=False,covariance_fallback_used=False,
        inference_status='NOT ESTIMABLE' if invalid else 'ESTIMABLE',failure_reason=reason)
    return pd.DataFrame(rows),meta


def fit_stage3c_models(panel):
    primary,pmeta=fit_spatial_moderation(panel,hot='hot_primary',cold='cold_primary',threshold_label='p90/p10')
    sensitivity,smeta=fit_spatial_moderation(panel,hot='hot_sensitivity',cold='cold_sensitivity',threshold_label='p95/p05')
    primary['p_holm']=holm_adjust(primary.p_raw.tolist())
    primary['holm_reject']=primary.p_holm.lt(.05)
    return primary,sensitivity,dict(primary=pmeta,sensitivity=smeta,primary_test_count=4,
        threshold_changed_after_results=False,daytime_spatial_analysis=False,moran_lisa=False,station_significance_mining=False)
