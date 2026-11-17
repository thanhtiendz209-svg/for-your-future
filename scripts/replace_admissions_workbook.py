"""Import the supplied workbook verbatim; metadata retains IDs/location/personality only."""
from pathlib import Path
import json,re,hashlib,openpyxl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/raw/diem_va_hoc_phi_2026_20261114.xlsx'
PUBLIC=ROOT/'apps/web/public'

def numeric(value):
    if isinstance(value,(int,float)): return value
    return None

def parse_score(raw,method):
    text=str(raw).strip()
    if method=='Điểm THPT 2026' and isinstance(raw,(int,float)) and 0<=raw<=30:return float(raw),30
    # Only an explicit single original score with its denominator is comparable.
    match=re.match(r'^\s*(\d+(?:[.,]\d+)?)\s*/\s*(\d+)(?:\s*\nQuy đổi:.*)?\s*$',text,re.S)
    if match:
        score=float(match[1].replace(',','.'));scale=float(match[2])
        if 0<=score<=scale:return score,scale
    return None,None

def build():
    book=openpyxl.load_workbook(SOURCE,data_only=True)
    links=openpyxl.load_workbook(SOURCE,data_only=False)
    old=json.loads((PUBLIC/'data/universities.json').read_text())
    by_name={u['name']:u for u in old};details=[];unis=[];audit=[]
    for sheet in book.worksheets[:126]:
        meta=by_name[sheet['A1'].value]
        header=next(r[0].row for r in sheet.iter_rows() if r[0].value=='STT')
        cols=[(c.column,str(c.value)) for c in sheet[header][4:] if isinstance(c.value,str)]
        amounts=[c.column for c in sheet[header][4:] if isinstance(c.value,(int,float))]
        link_sheet=links[sheet.title]
        def url(row):
            cell=link_sheet.cell(row,3)
            if cell.hyperlink:return cell.hyperlink.target
            formula=str(cell.value or '').replace('\\"','"')
            match=re.search(r'HYPERLINK\(\s*"([^"\s]+)"',formula,re.I)
            return match[1] if match else (formula if formula.startswith('http') else None)
        tuition={'min':numeric(sheet['C5'].value),'max':numeric(sheet['C6'].value),'perCredit':numeric(sheet['C7'].value),'median':numeric(sheet['C8'].value),'label':sheet['A3'].value,'sources':[str(sheet.cell(r,3).value) for r in range(9,14) if str(sheet.cell(r,3).value).startswith('http')]}
        tuition['source']=next(iter(tuition['sources']),None)
        programs=[]
        for row in sheet.iter_rows(min_row=header+1):
            if not isinstance(row[0].value,(int,float)) or not row[2].value:continue
            values=[]
            for col,method in cols:
                raw=sheet.cell(row[0].row,col).value
                if raw is None or str(raw).strip()=='':continue
                score,scale=parse_score(raw,method)
                values.append({'method':method,'raw':str(raw),'value':score,'scale':scale})
            seq=len(programs)+1
            code=str(row[1].value or '')
            programs.append({'programId':f"{meta['id']}-2026-{seq:04d}",'code':code,'name':str(row[2].value),'type':str(row[3].value or ''),'row':row[0].row,'admissions':values,'tuition_annual':next((numeric(sheet.cell(row[0].row,c).value) for c in amounts if numeric(sheet.cell(row[0].row,c).value) is not None),None)})
        methods=[label for _,label in cols]
        thpt=[a['value'] for p in programs for a in p['admissions'] if a['method']=='Điểm THPT 2026' and a['scale']==30 and a['value'] is not None]
        sd={k:meta.get(k) for k in ['id','shortName','region','provinceNew','provinceOld','focusRiasec','category']}
        sd.update(name=sheet['A1'].value,website=url(14),admissionsUrl=url(15),scoreSource=url(16),tuition=tuition,programs=programs,methods=methods,sheet=sheet.title,updatedAt='2026-11-14',revision=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),sourceFile='Điểm và học phí.xlsx')
        details.append(sd)
        u={k:meta.get(k) for k in ['id','shortName','location','region','provinceNew','provinceOld','logo','category','focusRiasec']}
        u.update(name=sd['name'],website=sd['website'],admissionsUrl=sd['admissionsUrl'],majors=list(dict.fromkeys(p['name'] for p in programs)),majorItems=[{'code':p['code'],'name':p['name']} for p in programs],programs=[],tuition=tuition['min'],admissionScores={},admissionMethods=methods,lastUpdated='2026-11-14',admissions2026={'year':2026,'thptValues':thpt,'methods':methods,'programCount':len(programs)},dataNote='Dữ liệu thay thế từ Điểm và học phí.xlsx · 14/11/2026')
        unis.append(u)
    for sheet in book.worksheets[126:]:
        audit.append({'sheet':sheet.title,'rows':[[c.value for c in r] for r in sheet.iter_rows()]})
    assert len(details)==126 and all(d['programs'] for d in details)
    for folder in [PUBLIC/'data',ROOT/'apps/web/dist/data',ROOT/'data/staging']:
        folder.mkdir(parents=True,exist_ok=True)
        for name,data in [('universities.json',unis),('school_details.json',details),('admissions_review.json',audit)]:
            (folder/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    report={'revision':details[0]['revision'],'schools':len(details),'programs':sum(len(d['programs']) for d in details),'admission_cells':sum(len(p['admissions']) for d in details for p in d['programs']),'schools_without_thpt':[d['sheet'] for d in details if 'Điểm THPT 2026' not in d['methods']]}
    (ROOT/'data/staging/workbook_import_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':build()
