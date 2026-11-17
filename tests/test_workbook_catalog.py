import unittest,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from replace_admissions_workbook import SOURCE,parse_score
import openpyxl

class WorkbookCatalogTests(unittest.TestCase):
 def test_every_program_and_raw_score_matches_workbook(self):
  book=openpyxl.load_workbook(SOURCE,data_only=True)
  schools=json.loads((ROOT/'apps/web/public/data/school_details.json').read_text())
  self.assertEqual(len(schools),126)
  n=0
  for d in schools:
   sheet=book[d['sheet']]
   head=next(r[0].row for r in sheet.iter_rows() if r[0].value=='STT')
   rows=[r for r in sheet.iter_rows(min_row=head+1) if isinstance(r[0].value,(int,float)) and r[2].value]
   self.assertEqual(len(rows),len(d['programs']))
   columns={str(c.value):c.column for c in sheet[head][4:] if isinstance(c.value,str)}
   for p,row in zip(d['programs'],rows):
    self.assertEqual(p['name'],row[2].value)
    for a in p['admissions']:
     self.assertEqual(a['raw'],str(sheet.cell(row[0].row,columns[a['method']]).value));n+=1
  self.assertEqual(n,11428)
 def test_no_old_thpt_for_combined_only_schools(self):
  unis=json.loads((ROOT/'apps/web/public/data/universities.json').read_text())
  for name in ['HCMUT','HCMUS','UIT','UEL','TDTU','UEH']:
   d=next(d for d in json.loads((ROOT/'apps/web/public/data/school_details.json').read_text()) if d['sheet']==name)
   u=next(u for u in unis if u['id']==d['id'])
   self.assertEqual(u['admissions2026']['thptValues'],[])
 def test_scale_conversion_is_not_mixed(self):
  self.assertEqual(parse_score('910/1200\nQuy đổi: 26,46 (thang đối chiếu)','V-ACT 2026'),(910,1200))
  self.assertEqual(parse_score('Quy đổi: 22,5 (thang đối chiếu)','V-SAT 2026'),(None,None))
  self.assertEqual(parse_score('55/100\n56,5/100','Học bạ + CCQT'),(None,None))
  self.assertEqual(parse_score(40500000,'Điểm THPT 2026'),(None,None))
if __name__=='__main__':unittest.main()
