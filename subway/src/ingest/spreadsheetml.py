"""Read only the contracted data worksheet; malformed metadata is isolated."""
import re
import xml.etree.ElementTree as ET
import pandas as pd
from subway.src.ingest.schema_inspector import _SPREADSHEET_NS, _spreadsheetml_row_values


def read_spreadsheetml(path, sheet_name, encoding, title_row_count):
    text=path.read_bytes().decode(encoding)
    matches=list(re.finditer(rf'<Worksheet\b[^>]*\bss:Name="{re.escape(sheet_name)}"[^>]*>',text))
    if len(matches)!=1:raise ValueError('selected worksheet missing or duplicated')
    start=matches[0].start();end=text.find('</Worksheet>',matches[0].end())
    if end<0:raise ValueError('truncated selected worksheet')
    root=ET.fromstring(f'<Workbook xmlns="{_SPREADSHEET_NS}" xmlns:ss="{_SPREADSHEET_NS}" xmlns:x="urn:schemas-microsoft-com:office:excel">'+text[start:end+12]+'</Workbook>')
    rows=[_spreadsheetml_row_values(row) for row in root.findall(f'.//{{{_SPREADSHEET_NS}}}Row')]
    if title_row_count<0 or len(rows)<=title_row_count:raise ValueError('missing header')
    header=rows[title_row_count]
    if not header or len(set(header))!=len(header) or '' in header:raise ValueError('invalid header')
    data=rows[title_row_count+1:]
    if any(len(row)>len(header) for row in data):raise ValueError('data row exceeds header width')
    out=pd.DataFrame([row+['']*(len(header)-len(row)) for row in data],columns=header)
    out['source_row_id']=range(1,len(out)+1)
    if '동별' in out:out['source_block_id']=out['동별'].ne(out['동별'].shift()).cumsum()
    return out
