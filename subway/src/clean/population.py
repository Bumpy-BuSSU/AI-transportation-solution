"""Q2 official '계' population, joined to independently corroborated hierarchy."""
import pandas as pd
from subway.src.clean.contracts import StageResult
from subway.src.validate.raw_validation import Finding

SENIOR_BANDS=['65~69세','70~74세','75~79세','80~84세','85~89세','90~94세','95~99세','100세 이상']


def verify_population_hierarchy(frame,boundary,rules):
    """Verify full source groups against unique complete SGIS parent-code sets.

    Source sequence proposes membership; official gu labels, reviewed name
    variants and a full boundary-set bijection must independently corroborate
    every group. Once verified, cleaning joins block IDs, not row position.
    """
    config=rules['population']
    required={'source_block_id','source_row_id','동별'}
    if not required.issubset(frame) or not {'ADM_NM','ADM_CD'}.issubset(boundary):raise ValueError('hierarchy evidence inputs absent')
    if not config.get('hierarchy_evidence') or not config.get('code_evidence'):raise ValueError('official hierarchy/code evidence missing')
    if frame.source_row_id.isna().any() or frame.source_row_id.duplicated().any():raise ValueError('source row IDs invalid')
    if frame.groupby('source_block_id')['동별'].nunique().ne(1).any():raise ValueError('block contains conflicting labels')
    blocks=frame.sort_values('source_row_id')[['source_block_id','동별']].drop_duplicates()
    gu_names=config['gu_names'];groups={};records=[];current=None
    if len(gu_names)!=config['expected_gu'] or len(set(gu_names))!=len(gu_names):raise ValueError('official gu labels incomplete')
    for block,name in blocks.itertuples(index=False,name=None):
        if name=='합계':
            if records:raise ValueError('Seoul total must precede hierarchy')
            records.append(dict(source_block_id=block,source_label=name,level='seoul',gu='',dong='',adm_cd=''))
        elif name in gu_names:
            if name in groups:raise ValueError('repeated gu subtotal')
            current=name;groups[name]=[]
            records.append(dict(source_block_id=block,source_label=name,level='gu',gu=name,dong='',adm_cd=''))
        else:
            if current is None:raise ValueError('orphan dong block')
            canonical=config.get('boundary_name_aliases',{}).get(name,name)
            groups[current].append(canonical)
            records.append(dict(source_block_id=block,source_label=name,level='dong',gu=current,dong=canonical,adm_cd=''))
    if list(groups)!=gu_names or sum(r['level']=='seoul' for r in records)!=1:raise ValueError('full official gu hierarchy/order mismatch')
    codes=boundary.ADM_CD.astype('string')
    if codes.isna().any() or not codes.str.fullmatch(r'11\d{6}',na=False).all() or codes.duplicated().any():raise ValueError('invalid SGIS administrative codes')
    b=boundary[['ADM_NM','ADM_CD']].copy();b['prefix']=codes.str[:5]
    sets={prefix:set(group.ADM_NM) for prefix,group in b.groupby('prefix')}
    parents={}
    for gu,names in groups.items():
        hits=[p for p,n in sets.items() if n==set(names)]
        if len(names)!=len(set(names)) or len(hits)!=1:raise ValueError(f'{gu}: boundary membership not uniquely corroborated')
        parents[gu]=hits[0]
    if len(set(parents.values()))!=len(sets) or len(b)!=config['expected_dong']:raise ValueError('boundary hierarchy not bijective')
    for record in records:
        if record['level']=='dong':
            hit=b[(b.prefix==parents[record['gu']]) & (b.ADM_NM==record['dong'])]
            if len(hit)!=1:raise ValueError('ambiguous boundary member')
            record['adm_cd']=str(hit.iloc[0].ADM_CD)
        record['evidence']=config['hierarchy_evidence']+'; '+config['code_evidence']+'; full source block order + exact complete boundary parent-set comparison'
    return pd.DataFrame(records)


def clean_population(frame,hierarchy,rules,source_file):
    raw=frame.copy(deep=True)
    findings,parts=[],[]
    def error(code,message,table=raw):
        findings.append(Finding('ERROR','population',code,message,source_file))
        bad=table.copy();bad['exception_code']=code;parts.append(bad)
    cols={'source_block_id','source_label','level','gu','dong','adm_cd','evidence'}
    if not cols.issubset(hierarchy) or not {'source_block_id','source_row_id','동별','연령별','항목','단위','2024. 2/4'}.issubset(raw):
        error('HIERARCHY_UNVERIFIED','required columns absent');return StageResult(pd.DataFrame(),findings,parts[0])
    h=hierarchy.copy()
    if h.source_block_id.duplicated().any() or h.evidence.fillna('').str.strip().eq('').any() or not h.level.isin(['seoul','gu','dong']).all():
        error('HIERARCHY_UNVERIFIED','duplicate blocks or missing hierarchy evidence');return StageResult(pd.DataFrame(),findings,parts[0])
    out=raw.merge(h,on='source_block_id',how='left',validate='many_to_one')
    invalid=out.level.isna() | out['동별'].ne(out.source_label)
    if invalid.any():error('ORPHAN_BLOCK','source labels do not match verified hierarchy',out.loc[invalid])
    selected=out[out.level.eq('dong') & out['항목'].eq('계')].copy()
    records=[]
    for (gu,dong),group in selected.groupby(['gu','dong'],dropna=False,sort=True):
        ages=group['연령별'].tolist()
        if len(ages)!=9 or set(ages)!=set(['합계']+SENIOR_BANDS):
            error('AGE_BAND_CONTRACT',f'{gu}/{dong}: exactly one total and all eight senior bands required',group);continue
        values=pd.to_numeric(group['2024. 2/4'],errors='coerce')
        bad=values.isna() | values.isin([float('inf'),float('-inf')]) | values.lt(0) | values.mod(1).ne(0) | values.ge(2**63)
        units=group['단위'].astype('string')
        metadata_unit=rules['population'].get('unit')=='명' and bool(rules['population'].get('unit_evidence'))
        valid_units=units.eq('명') | (units.fillna('').eq('') & metadata_unit)
        if bad.any() or not valid_units.fillna(False).all():
            error('INVALID_POPULATION',f'{gu}/{dong}: nonnegative integer people required',group);continue
        indexed=pd.Series(values.tolist(),index=ages)
        total=int(indexed['합계']);senior=sum(int(indexed[age]) for age in SENIOR_BANDS)
        if senior>total:error('SENIOR_EXCEEDS_TOTAL',f'{gu}/{dong}',group)
        if total==0:findings.append(Finding('WARNING','population','ZERO_TOTAL',f'{gu}/{dong}: share remains null',source_file))
        records.append(dict(gu=gu,dong=dong,adm_cd=group.adm_cd.iloc[0],source_block_id=group.source_block_id.iloc[0],
                            population_total=total,population_65_plus=senior,senior_population_share=senior/total if total>0 else None,
                            source_row_ids='|'.join(str(n) for n in sorted(group.source_row_id)),
                            dong_name_raw=group['동별'].iloc[0],source_file=source_file,source_dataset_id='population',
                            source_quarter='2024. 2/4',source_item='계',hierarchy_evidence=group.evidence.iloc[0]))
    result=pd.DataFrame(records)
    config=rules['population']
    if len(result)!=config['expected_dong'] or (not result.empty and result.gu.nunique()!=config['expected_gu']):error('HIERARCHY_COVERAGE','verified gu/dong coverage differs from target')
    if not result.empty and result.duplicated(['gu','dong']).any():error('DUPLICATE_DONG_KEY','gu/dong must be unique',result)
    return StageResult(result,findings,pd.concat(parts,ignore_index=True,sort=False) if parts else pd.DataFrame())
