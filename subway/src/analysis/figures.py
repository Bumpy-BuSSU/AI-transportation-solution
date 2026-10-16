"""Five descriptive, deterministic figures; no inferential annotations."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def render_figures(tables: dict, directory: Path) -> list[str]:
    directory.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2,'figure.facecolor':'white'})
    names=[]
    def save(fig,name,caption):
        fig.text(.5,.01,caption,ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.04,1,.97));fig.savefig(directory/name,dpi=160,metadata={'Software':'subway Stage3A / matplotlib '+matplotlib.__version__});plt.close(fig);names.append(name)
    daily=tables['eda_daily_age_weather.csv']
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,c,label in zip(axes,['temperature_mean','temperature_max','temperature_min'],['Daily mean','Daily maximum','Daily minimum']):
        ax.hist(daily[c].dropna(),bins=20,color='#356b8c',edgecolor='white');ax.set(xlabel='Temperature (degC)',ylabel='Days',title=label,ylim=(0,None))
    fig.suptitle('2024 Seoul ASOS108 temperature distributions')
    save(fig,'eda_temperature_distribution.png','Daily weather only; missing values excluded from that variable; no extreme cutoff adopted.')
    profiles=tables['eda_temperature_profiles.csv']
    for c,label in [('temperature_max','maximum'),('temperature_min','minimum')]:
        frame=profiles.loc[profiles.weather_variable.eq(c)]
        fig,ax=plt.subplots(figsize=(8,5))
        for age,color,title in [('senior','#ab4c28','65+'),('non_senior','#24668c','Non-senior')]:
            ax.plot(frame.temperature_mean,frame[age+'_relative_index'],marker='o',color=color,label=title)
        ax.axhline(100,color='gray',linestyle='--',linewidth=1);ax.legend()
        ax.set(xlabel=f'Daily {label} temperature: mean within weather-only bin (degC)',ylabel='Mean daily ridership index (annual mean = 100)',ylim=(0,None),title=f'Descriptive {label}-temperature / age profile')
        save(fig,f'eda_{c}_age_profile.png','Weather-only quantile bins; common valid age cells; boarding + alighting. Season/calendar unadjusted; no effects tested.')
    hourly=tables['eda_hourly_profile.csv']
    fig,axes=plt.subplots(1,2,figsize=(14,5),sharey=True)
    for ax,kind in zip(axes,['boarding','alighting']):
        frame=hourly.loc[hourly.boarding_type.eq(kind)].sort_values('hour_order')
        labels=frame.hour_bin.str.replace('_','-').tolist();xs=list(range(len(frame)))
        for age,color,label in [('senior','#ab4c28','65+'),('non_senior','#24668c','Non-senior')]:
            ax.plot(xs,frame[age+'_within_direction_share']*100,marker='.',color=color,label=label)
        indices=[i for i,v in enumerate(frame.daytime_10_16) if v]
        if indices:ax.axvspan(min(indices)-.5,max(indices)+.5,color='#eac77a',alpha=.3,label='Pre-specified 10-16')
        ax.set_xticks(xs,labels,rotation=65,ha='right',fontsize=8);ax.set(xlabel='Original hour interval',ylabel='Share of age-group annual direction counts (%)',title=kind.capitalize(),ylim=(0,None));ax.legend(fontsize=9)
    fig.suptitle('Descriptive hour-of-day age structure')
    save(fig,'eda_hourly_age_profile.png','Within each age/direction denominator; pre-specified [10:00,16:00) shading is not an extreme-temperature result.')
    stations=tables['eda_station_summary.csv']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].hist(stations.total_ridership.dropna()/1e6,bins=20,color='#356b8c',edgecolor='white');axes[0].set(xlabel='Annual valid-cell total counts (millions)',ylabel='Station identities',xlim=(0,None),ylim=(0,None),title='Station volume distribution')
    axes[1].hist(stations.senior_share.dropna()*100,bins=20,color='#ab4c28',edgecolor='white');axes[1].set(xlabel='Annual senior share (%)',ylabel='Station identities',xlim=(0,100),ylim=(0,None),title='Station age-share distribution')
    fig.suptitle('Descriptive station heterogeneity within current study area')
    save(fig,'eda_station_heterogeneity.png','Common valid age cells; boarding + alighting; no station-specific temperature effects or station ranking.')
    return names
