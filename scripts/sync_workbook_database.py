"""Replace admission entities only; keep accounts and assessment data untouched."""
from pathlib import Path
import json,sys,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.database import SessionLocal,engine
from sqlalchemy import null
from app.core.models_db import University,Program,AdmissionCriteria

def run():
    schools=json.loads((ROOT/'apps/web/public/data/school_details.json').read_text())
    meta={u['id']:u for u in json.loads((ROOT/'apps/web/public/data/universities.json').read_text())}
    with SessionLocal() as db:
        backup={m.__tablename__:[{c.name:getattr(x,c.name) for c in m.__table__.columns} for x in db.query(m)] for m in [University,Program,AdmissionCriteria]}
        out=ROOT/'data/backups/admissions_before_20261114.json';out.parent.mkdir(exist_ok=True,parents=True)
        if not out.exists():out.write_text(json.dumps(backup,ensure_ascii=False,default=str));out.chmod(0o600)
        db.query(AdmissionCriteria).delete(synchronize_session=False)
        db.query(Program).delete(synchronize_session=False)
        db.flush()
        ids=[s['id'] for s in schools]
        db.query(University).filter(~University.uni_id.in_(ids)).delete(synchronize_session=False)
        n=0; program_rows=[]; criteria_rows=[]
        for sd in schools:
            u=db.get(University,sd['id'])
            if not u:u=University(uni_id=sd['id']);db.add(u)
            u.name=sd['name'];u.short_name=sd['shortName'];u.type=sd['category'] or 'Đa ngành';u.location=sd['provinceNew'] or 'Chưa xác định';u.region=sd['region'] or 'Chưa xác định';u.website=sd['website'];u.admissions_url=sd['admissionsUrl'];u.focus_riasec=sd.get('focusRiasec') or [];u.logo=meta[sd['id']].get('logo')
            db.flush()
            for p in sd['programs']:
                # Annual school ranges are not per-program prices.
                program_rows.append(dict(program_id=p['programId'],uni_id=sd['id'],major_code=p['code'],name=p['name'],tuition_annual=p['tuition_annual'] if p['tuition_annual'] is not None else None,effective_cost=p['tuition_annual'] if p['tuition_annual'] is not None else None,degree_level=None,duration_years=None))
                for i,a in enumerate(p['admissions']):
                    criteria_rows.append(dict(criteria_id=f"{p['programId']}-{i}",program_id=p['programId'],year=2026,method=a['method'],group_code=None,benchmark_score=a['value'],score_scale=a['scale'] or 30,source_url=sd['scoreSource'],special_conditions=json.dumps({'raw':a['raw'],'scale_provided':a['scale'],'sheet':sd['sheet'],'row':p['row'],'revision':sd['revision']},ensure_ascii=False)))
                    n+=1
        db.flush()
        db.bulk_insert_mappings(Program,program_rows,render_nulls=True)
        db.bulk_insert_mappings(AdmissionCriteria,criteria_rows,render_nulls=True)
        db.commit();print(engine.dialect.name,'schools',len(schools),'programs',sum(len(d['programs']) for d in schools),'criteria',n)
if __name__=='__main__':run()
