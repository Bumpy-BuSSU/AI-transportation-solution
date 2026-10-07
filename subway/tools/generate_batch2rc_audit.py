"""Reproduce Batch 2R-C diagnostics from pinned official audit files, outside Raw.

Run from repository root: python -m subway.tools.generate_batch2rc_audit
  --audit-dir <local audit directory> --output-dir <temporary report directory>
This is a fixed Mission audit, not a preprocessing/publishing runner.
"""
from pathlib import Path
import argparse,hashlib,json
from collections import defaultdict,deque
import pandas as pd
from subway.tools.audit_station_candidate import historical_gate,resolve_name,comparison_statistics
from subway.tools.audit_station_candidate import unapproved_display_evidence

BASE='054b5d09754801413789377909ec7f45cf278ca8'
KRIC_URL='https://data.kric.go.kr/rips/M_01_01/detail.do?id=32'
RENAME_URL='https://data.seoul.go.kr/dataList/OA-22477/F/1/datasetView.do'
PINNED={'kric_current_export.xlsx':'cdf1d84a7e5c898b2aacd622783ba8ba9af35c40bee0561dc97d55ce8e063f94',
        'rename.csv':'fc1c285c6309c63c4c3f5b4928d47ec50fb3a2008c5e959d4c3a623fd68b6f52',
        'station_2023.csv':'9da58a78b07852906b9b9c75c539770d8a50a16c0cb5b8c21b23383327f85ce6',
        'station_2024.csv':'9da58a78b07852906b9b9c75c539770d8a50a16c0cb5b8c21b23383327f85ce6',
        'standard_2024.hwpx':'d3d464f6a9dd9f6dfd3ff61fec966c95ccce8aec085c234ba3af9e665d3c67cd',
        'standard_attributes.csv':'b6092f441eb8e7b3a70deb6605e6770ac2fb2414a48f69f6b9a71f1e8c717d0a'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();local=args.audit_dir.resolve();out=args.output_dir.resolve()
    repo=Path(__file__).resolve().parents[2]
    raw=(repo/'subway/data/raw').resolve()
    if out==raw or raw in out.parents:raise ValueError('Audit output cannot be authoritative Raw')
    for name,expected in PINNED.items():
        if sha(local/name)!=expected:raise ValueError('Audit input hash mismatch: '+name)
    out.mkdir(parents=True,exist_ok=True)
    def save(name,obj):
        (out/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    def csv(name,rows,keys):
        pd.DataFrame(rows).sort_values(keys,kind='stable').to_csv(out/name,index=False,encoding='utf-8',lineterminator='\n')
    audit=pd.read_csv(repo/'subway/data/validation/batch2rb_station_identity_audit.csv',dtype=str,keep_default_na=False)
    identities=audit[audit.match_status.ne('station_only')].copy()
    assert len(identities)==274 and not identities.duplicated(['line','station_name']).any()
    aliases=pd.read_csv(repo/'subway/config/station_aliases.csv',dtype=str,keep_default_na=False)
    renames=pd.read_csv(local/'rename.csv',encoding='cp949',dtype=str,keep_default_na=False)
    manifest=pd.read_csv(repo/'subway/data_manifest.csv',dtype=str,keep_default_na=False).set_index('dataset_id')
    current_seoul=pd.read_csv(repo/manifest.loc['station','raw_path'],encoding='cp949',dtype=str,keep_default_na=False)
    historic_columns=['호선','고유역번호(외부역코드)','역명','위도','경도']
    for filename in ['station_2023.csv','station_2024.csv']:
        historic=pd.read_csv(local/filename,encoding='cp949',dtype=str,keep_default_na=False)
        assert len(historic)==len(current_seoul)==276
        pd.testing.assert_frame_equal(historic[historic_columns].reset_index(drop=True),current_seoul[historic_columns].reset_index(drop=True))
    kric=pd.read_excel(local/'kric_current_export.xlsx',dtype=str,keep_default_na=False)
    line_map={'I4101':'1','S1102':'2','S1121':'2','S1122':'2','I1103':'3','I1104':'4',
              'S1105':'5','S1106':'6','S1107':'7','S1108':'8'}
    kric['line']=kric['노선번호'].map(line_map)
    kric=kric[kric.line.notna() & kric['운영기관명'].isin(['서울교통공사','인천교통공사'])].copy()
    kric['source_row_id']=kric.index+1
    graph=defaultdict(list)
    def edge(line,a,b,e):
        graph[(line,a)].append((b,e));graph[(line,b)].append((a,e))
    for r in aliases[aliases.dataset_id.eq('station') & aliases.verified.str.lower().eq('true')].itertuples():
        edge(r.line,r.station_name_raw,r.station_name,'approved P-S2-2RB station alias: '+r.evidence)
    for r in renames.to_dict('records'):
        edge(r['호선'],r['역명 변경 전'],r['역명 변경 후'],f"official OA-22477 row={r['연번']} date={r['개정일']} {r['비고']}; new relationships are proposal only")
    def connected(line,name):
        seen={name:''};q=deque([name])
        while q:
            current=q.popleft()
            for target,e in sorted(graph[(line,current)]):
                if target not in seen:seen[target]=(seen[current]+'; '+e).strip('; ');q.append(target)
        return seen
    mapping=[];compare=[];temporal=[]
    for r in identities.to_dict('records'):
        line,name=r['line'],r['station_name'];relations=connected(line,name)
        candidates=kric[kric.line.eq(line) & kric['역사명'].isin(relations)]
        record={'canonical_station_id':'station:'+json.dumps([line,name],ensure_ascii=False,separators=(',',':')),
                'line':line,'canonical_station_name':name,'ridership_code':r['station_code_raw_ridership'],
                'seoul_name':r['station_name_raw'],'seoul_code':r['station_code_raw_station'],
                'seoul_latitude':r['latitude'],'seoul_longitude':r['longitude'],
                'baseline_match_status':r['match_status'],'source_code_conflict':r['source_code_conflict']=='True',
                'kric_2024_status':'unresolved','kric_2024_name':'','kric_2024_code':'','kric_2024_address':'',
                'kric_2024_latitude':'','kric_2024_longitude':'','kric_2024_row_reference':'',
                'kric_2024_missing_reason':'exact historical export not acquired; do not backdate 2026 bytes',
                'spatially_verified':False,'authority_adopted':False,'support_export_reference':'2026-06-30',
                'support_candidate_count':len(candidates),'support_status':'ambiguous' if len(candidates)>1 else 'unresolved',
                'support_name_line_identity_verified':False,'support_name_relation_evidence':'',
                'support_row_id':'','support_name':'','support_line_code':'','support_code':'','support_operator':'',
                'support_address':'','support_latitude':'','support_longitude':'','support_row_reference':'',
                'support_coordinate_present':False,'support_reference_url':KRIC_URL}
        if len(candidates)==1:
            c=candidates.iloc[0]
            assert c['역사도로명주소'] and c['운영기관명']
            relation=resolve_name(line,c['역사명'],{(line,n):(name,e) for n,e in relations.items()})[1]
            record.update(support_status='exact' if c['역사명']==name else 'reviewed_name',
                support_name_line_identity_verified=True,support_name_relation_evidence=relation or 'exact name/line; official operator/address; no code-only join',
                support_row_id=int(c.source_row_id),support_name=c['역사명'],support_line_code=c['노선번호'],
                support_code=c['역번호'],support_operator=c['운영기관명'],support_address=c['역사도로명주소'],
                support_latitude=c['역위도'],support_longitude=c['역경도'],support_row_reference=c['데이터기준일자'],
                support_coordinate_present=bool(c['역위도'] and c['역경도']))
            if r['latitude'] and r['longitude'] and record['support_coordinate_present']:
                a=float(r['latitude']);b=float(r['longitude']);x=float(c['역위도']);y=float(c['역경도'])
                compare.append(dict(canonical_station_id=record['canonical_station_id'],line=line,station_name=name,
                    seoul_name=r['station_name_raw'],seoul_code=r['station_code_raw_station'],
                    seoul_reference='2025-08-14',seoul_latitude=a,seoul_longitude=b,
                    kric_2024_comparable=False,kric_2024_latitude='',kric_2024_longitude='',
                    support_export_reference='2026-06-30',support_row_reference=c['데이터기준일자'],
                    support_name=c['역사명'],support_code=c['역번호'],support_operator=c['운영기관명'],support_address=c['역사도로명주소'],
                    support_latitude=x,support_longitude=y,latitude_difference=x-a,longitude_difference=y-b,
                    relation_evidence=record['support_name_relation_evidence'],coordinate_decision='diagnostic only; not historical verification; no tolerance'))
        mapping.append(record)
        events=renames[renames['호선'].eq(line) & renames['개정일'].str.startswith('2024') &
                       (renames['역명 변경 전'].eq(name)|renames['역명 변경 후'].eq(name))]
        category='unresolved';eventdate='';event_evidence=''
        if len(events):
            category='renamed_during_2024_same_physical_station';eventdate=events.iloc[0]['개정일'];event_evidence=RENAME_URL+' row='+events.iloc[0]['연번']
        if line=='8' and name=='암사역사공원':
            category='opened_during_2024';eventdate='2024-08-10';event_evidence='https://scpm.seoul.go.kr/seoul-policy/evt0064'
        temporal.append(dict(canonical_station_id=record['canonical_station_id'],line=line,station_name=name,classification=category,
            event_date=eventdate,event_evidence=event_evidence,kric_2023_acquired=False,kric_2024_acquired=False,
            seoul_2023_label='2023-10-31',seoul_2024_label='2024-10-31',
            same_source_snapshot_equal=bool(r['latitude'] and r['longitude']),
            temporal_spatial_eligibility=False,
            limitation='Seoul October files byte-identical and omit Amsa; not year-end snapshots, not continuous observation; KRIC year-end bytes absent',
            proposed_date_rule='exclude dates before 2024-08-10; on/after still requires accepted coordinates/contract' if name=='암사역사공원' else 'unresolved until year-end/other official temporal evidence accepted'))
    csv('batch2rc_station_candidate_mapping.csv',mapping,['line','canonical_station_name'])
    csv('batch2rc_coordinate_comparison.csv',compare,['line','station_name'])
    csv('batch2rc_temporal_audit.csv',temporal,['line','station_name'])
    bykey={(r['line'],r['canonical_station_name']):r for r in mapping}
    conflicts=[]
    for r in mapping:
        if r['source_code_conflict']:
            assert r['line']=='6'
            conflicts.append(dict(ridership_line=r['line'],ridership_name=r['canonical_station_name'],ridership_code=r['ridership_code'],
                seoul_line=r['line'],seoul_name=r['seoul_name'],seoul_code=r['seoul_code'],seoul_latitude=r['seoul_latitude'],seoul_longitude=r['seoul_longitude'],
                kric_2024_line='',kric_2024_name='',kric_2024_code='',kric_2024_address='',kric_2024_latitude='',kric_2024_longitude='',
                classification='unresolved',reason='2024 official bytes absent; current support cannot verify historical code/coordinates',
                support_name=r['support_name'],support_line_code=r['support_line_code'],support_code=r['support_code'],support_address=r['support_address'],
                support_operator=r['support_operator'],support_latitude=r['support_latitude'],support_longitude=r['support_longitude'],support_row_reference=r['support_row_reference'],
                support_export_reference=r['support_export_reference'],name_relation_evidence=r['support_name_relation_evidence'],
                current_identity_corroborated=r['support_name_line_identity_verified'],raw_code_rewritten=False))
    assert len(conflicts)==21
    csv('batch2rc_line6_code_audit.csv',conflicts,['ridership_line','ridership_name'])
    unmatched=[]
    proposed={('6','녹사평(용산구청)'):'녹사평',('6','봉화산(서울의료원)'):'봉화산'}
    unreviewed={'고려대(종암)':'고려대','광흥창(서강)':'광흥창','대흥(서강대앞)':'대흥',
                '상월곡(한국과학기술연구원)':'상월곡','새절(신사)':'새절','안암(고대병원앞)':'안암',
                '월곡(동덕여대)':'월곡','월드컵경기장(성산)':'월드컵경기장','증산(명지대앞)':'증산','화랑대(서울여대입구)':'화랑대'}
    for r in audit[audit.match_status.isin(['ridership_only','station_only'])].to_dict('records'):
        line,name=r['line'],r['station_name'];pair='';category='';evidence='';decision='unresolved';row={}
        if line=='6' and (name in unreviewed or name in unreviewed.values()):
            pair=unreviewed.get(name,next((k for k,v in unreviewed.items() if v==name),''));category='display_name_unverified'
            full_name=name if name in unreviewed else pair
            bare_name=unreviewed[full_name]
            assert len(kric[kric.line.eq(line)&kric['역사명'].eq(full_name)])==1
            evidence=unapproved_display_evidence(full_name,bare_name)
        elif line=='6' and (name in proposed.values() or (line,name) in proposed):
            pair=proposed[(line,name)] if (line,name) in proposed else next(k[1] for k,v in proposed.items() if v==name)
            category='official_display_relation_proposal';decision='name relation verified; adoption/code/spatial still blocked';evidence=RENAME_URL+' rows54/55 (2013-12-26); no alias config change'
        elif (line,name) in [('2','까치산'),('3','충무로')]:
            category='coordinate_only_transfer';decision='outside actual Task8 line-specific identity set; do not force mapping';evidence='approved transfer group; total source uses line5 까치산 / line4 충무로'
        elif (line,name)==('6','신내'):
            category='coordinate_only_preexisting';decision='outside actual Task8 identity set; source omission reason unresolved';evidence='https://mediahub.seoul.go.kr/archives/1261413; service2019-12-21'
        elif name in ['까치울','암사역사공원']:
            category='missing_seoul_coordinate';decision='2026 official support only; exact2024 file absent';evidence=KRIC_URL
        elif (line,name)==('6','연신내'):
            category='coordinate_only_identity';decision='outside actual Task8 identity set; total source omission not explained';evidence=KRIC_URL+' S1106 row; no forced mapping'
        else:raise AssertionError((line,name))
        support=bykey.get((line,name))
        target=proposed.get((line,name),name)
        candidate=kric[kric.line.eq(line)&kric['역사명'].eq(target)]
        if support and support['support_status'] in ['exact','reviewed_name']:
            row={k:support[k] for k in ['support_name','support_code','support_operator','support_address','support_latitude','support_longitude','support_row_reference']}
        elif len(candidate)==1:
            c=candidate.iloc[0];row=dict(support_name=c['역사명'],support_code=c['역번호'],support_operator=c['운영기관명'],support_address=c['역사도로명주소'],support_latitude=c['역위도'],support_longitude=c['역경도'],support_row_reference=c['데이터기준일자'])
        unmatched.append(dict(line=line,name=name,side=r['match_status'],ridership_code=r['station_code_raw_ridership'],seoul_code=r['station_code_raw_station'],
            seoul_latitude=r['latitude'],seoul_longitude=r['longitude'],proposed_pair=pair,category=category,decision=decision,evidence=evidence,
            kric_2024_available=False,new_alias_adopted=False,support_export_reference='2026-06-30',**row))
    assert len(unmatched)==30
    csv('batch2rc_unmatched_identity_audit.csv',unmatched,['line','name','side'])
    supportstats=comparison_statistics(compare)
    outliers=sorted(compare,key=lambda r:max(abs(r['latitude_difference']),abs(r['longitude_difference'])),reverse=True)[:10]
    summary=dict(mission='P-S2-2RC',audit_date='2026-10-07',starting_head=BASE,
        acquisition_2024={**historical_gate('2026-06-30','2024-12-31'),'official_file':None,'failure_reason':'portal labels20241231 but link returns20260630 XLSX; public history/standard export endpoints HTTP500; no historical attachment or official historical download found'},
        acquisition_2023=dict(acquired=False,official_file=None,sha256=None,reference_date='2023-12-31',reason='official KRIC historical bytes not obtained'),
        support_candidate=dict(dataset_id='15013205',kric_id=32,official_filename='전체_도시철도역사정보_20260630.xlsx',provider='국가철도공단 / 전국도시철도운영기관',
            reference_date='2026-06-30',download_date='2026-10-07',sha256=PINNED['kric_current_export.xlsx'],rows=1099,
            url=KRIC_URL,download_url='https://data.kric.go.kr/rips/dataset/download.file?type=filedata&id=32&operation=1',
            license='public official file, no login; data.go.kr15013205 이용허락범위 제한 없음',authoritative_raw_adopted=False,row_reference_does_not_backdate_export=True),
        coverage_2024=dict(task8_identities=274,exact=0,reviewed_name=0,unresolved=274,ambiguous=0,duplicate_candidate_identities=None,verified_coordinates=0,missing_coordinate_count=None,
            unavailable_not_observed_missing=274,counts_are_acquisition_unavailability_not_empty_dataset=True),
        support_2026_coverage=dict(status_counts=pd.DataFrame(mapping).support_status.value_counts().to_dict(),
            unique_identity_coordinate_present=sum(r['support_coordinate_present'] for r in mapping),
            ambiguous=sum(r['support_status']=='ambiguous' for r in mapping),missing_coordinates_on_unique_mapped=sum(r['support_status'] in ['exact','reviewed_name'] and not r['support_coordinate_present'] for r in mapping),
            duplicate_candidate_identity_groups=int(kric.groupby(['line','역사명']).size().gt(1).sum()),not_historical_coverage=True),
        line6=dict(count=21,classifications={'unresolved':21,'verified_same_station_different_source_code':0,'contradictory':0},
            support_name_line_corroborated=sum(r['current_identity_corroborated'] for r in conflicts),namespace_result='source-specific numbering observed; universal cross-source code equality contradicted; no arithmetic conversion established',raw_rewritten=False),
        unmatched_categories=pd.DataFrame(unmatched).groupby(['side','category']).size().unstack(fill_value=0).to_dict('index'),
        comparison_2024=comparison_statistics([]),comparison_2026_support={**supportstats,'top_outliers':outliers,'not_a_2024_validation':True},
        magok_balsan=dict(seoul_coordinate_equal=True,seoul_latitude=37.562182,seoul_longitude=126.82693,
            historical_2024_result='C unresolved: historical candidate not acquired',
            current_support=[r for r in compare if r['station_name'] in ['마곡','발산']],
            interpretation='2026 values numerically distinct by latitude0.000042 / longitude0.000060 degrees but nearly coincident despite separate road addresses163/267; not enough evidence of independently plausible distinct station locations; retain blocker'),
        crs=dict(outcome='A',official_standard='WGS84 explicitly specified for dataset42 도시철도역사정보 items10 역위도 /11 역경도',
            standard_2024_url='https://www.data.go.kr/bbs/rcr/selectRecsroom.do?originId=PDS_0000000001227&atchFileId=FILE_000000003049184',
            standard_2024_download='https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003049184&fileDetailSn=2&insertDataPrcus=N',
            standard_2024_sha256=PINNED['standard_2024.hwpx'],latest_attribute_source='https://www.data.go.kr/data/15156444/fileData.do',latest_attribute_sha256=PINNED['standard_attributes.csv'],
            proposed_contract='WGS84 geographic degrees; longitude=x latitude=y; proposed GIS representation EPSG:4326 (EPSG identifier inferred from explicit WGS84, not stated in standard)',
            feature_location='operator-managed exits center per standard item10; not platform centroid or arbitrary entrance',
            current_seoul_crs_verified=False,crs_assigned=False,datum_assumption_needed=False,authority_contract_approval_pending=True,
            limitation='normative standard datum is explicit; individual row conformance still requires audit, especially provider-acknowledged coordinate errors'),
        temporal=dict(classification_counts=pd.DataFrame(temporal).classification.value_counts().to_dict(),
            stable_preexisting=0,coordinate_change_detected=0,kric_year_end_comparison_available=False,
            seoul_october_equal_coordinate_rows=276,snapshot_hashes={'2023-10-31':PINNED['station_2023.csv'],'2024-10-31':PINNED['station_2024.csv']},
            warning='byte-identical October snapshots omit Amsa opened August2024; no year-end or continuous-observation inference'),
        local_audit_input_hashes=PINNED,
        official_documents=[dict(filename='공공데이터 제공 표준(전문)_업로드.hwpx',local_name='standard_2024.hwpx',provider='행정안전부',reference='19th revision 2024.10',download_date='2026-10-07',bytes=2256495,sha256=PINNED['standard_2024.hwpx'],url='https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003049184&fileDetailSn=2&insertDataPrcus=N'),
            dict(filename='제공표준데이터셋_최종2.csv',local_name='standard_attributes.csv',provider='행정안전부',reference='20th revision 2025.10',download_date='2026-10-07',bytes=4015990,sha256=PINNED['standard_attributes.csv'],url='https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003564130&fileDetailSn=1&insertDataPrcus=N')],
        task5_status='BLOCKED',task6_status='COMPLETE',task8_status='COMPLETE',task9_status='NOT STARTED',task10_status='NOT STARTED',task11_status='NOT STARTED',
        recommendation='retain current authority configuration; conditional KRIC2024 primary proposal only after exact historical bytes, row quality/identity/temporal gates and human acceptance')
    save('batch2rc_kric_candidate_summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['coverage_2024','support_2026_coverage','comparison_2026_support','temporal']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
