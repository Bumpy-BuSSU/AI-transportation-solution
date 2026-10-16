"""Exactly three descriptive/primary Stage3C report figures."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def render_spatial_figures(dong_context,station_context,heterogeneity,primary,output_dir: Path):
    if len(primary)!=4 or primary[['beta','ci95_low','ci95_high']].isna().any().any():
        raise ValueError('exactly four estimable primary coefficients required for figure')
    if any('signif' in c or 'reject' in c for c in heterogeneity.columns):raise ValueError('Layer A must be descriptive only')
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    names=['station_extreme_heterogeneity.png','spatial_context.png','spatial_moderation_effects.png']
    metadata={'Software':'subway Stage3C / matplotlib '+matplotlib.__version__}
    def save(fig,name):
        fig.savefig(out/name,dpi=160,metadata=metadata);plt.close(fig)
    stations=station_context.merge(heterogeneity,on='canonical_station_id',validate='one_to_one',suffixes=('','_layer_a'))
    bound=float(np.max(np.abs(stations[['beta_hot','beta_cold']].to_numpy(float))))
    if bound==0:bound=1e-12
    fig,axes=plt.subplots(1,2,figsize=(10,6),layout='constrained')
    for ax,col,title in zip(axes,['beta_hot','beta_cold'],['Hot p90','Cold p10']):
        dong_context.plot(ax=ax,color='#eeeeee',edgecolor='#cccccc',linewidth=.2)
        artist=ax.scatter(stations.x_5179,stations.y_5179,c=stations[col],cmap='RdBu_r',vmin=-bound,vmax=bound,s=13)
        ax.set_title(title+' descriptive station coefficient');ax.set_axis_off()
    fig.colorbar(artist,ax=axes,label='Log senior/non-senior boarding ratio coefficient',shrink=.7)
    fig.suptitle('Layer A: point estimates only; no station significance or risk classification')
    save(fig,names[0])
    fig,axes=plt.subplots(1,2,figsize=(10,6),layout='constrained')
    for ax,col,title in zip(axes,['senior_population_share','shelters_per_10k'],['Senior population share (2024 Q2)','Observed shelters per 10,000 residents']):
        dong_context.plot(column=col,ax=ax,cmap='viridis',legend=True,legend_kwds={'shrink':.65})
        dong_context.loc[dong_context.has_analyzed_station].boundary.plot(ax=ax,color='black',linewidth=.5)
        ax.set_title(title);ax.set_axis_off()
    fig.suptitle('All dongs; black outlines mark dongs containing analyzed stations\nShelter snapshot and straight-line distance do not establish accessibility')
    save(fig,names[1])
    labels=['Hot × senior population share','Cold × senior population share','Hot × shelters/10k','Cold × shelters/10k']
    beta=primary.beta.to_numpy(float);low=primary.ci95_low.to_numpy(float);high=primary.ci95_high.to_numpy(float)
    fig,ax=plt.subplots(figsize=(9,4.8))
    ax.errorbar(beta,np.arange(4),xerr=np.vstack([beta-low,high-beta]),fmt='o',capsize=4)
    ax.axvline(0,color='gray',linestyle='--');ax.set_yticks(np.arange(4),labels);ax.invert_yaxis()
    ax.set_xlabel('Log-ratio coefficient per one SD of dong context; pointwise 95% CI')
    ax.set_title('Primary Layer B: station-weighted associations');ax.grid(axis='x',alpha=.2)
    fig.text(.5,.015,'OLS station-day log ratio; station/date FE; moderator × month/DOW controls.\nADM_CD/date two-way clustered SE; Holm adjusts four p-values; displayed CIs are pointwise.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,1));save(fig,names[2])
    return names
