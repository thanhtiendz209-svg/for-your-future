"""Replace graph admission data; reuse only existing career/group metadata when matched exactly."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apps/api'))
from app.integrations.neo4j.client import get_sync_driver
from app.core.config import settings
schools=json.loads((ROOT/'apps/web/public/data/school_details.json').read_text())
with get_sync_driver().session(database=settings.NEO4J_DATABASE) as session:
    old=session.run('MATCH (p:Program)-[:OFFERED_BY]->(u:University) OPTIONAL MATCH (p)-[:PREPARES_FOR]->(c:Career) OPTIONAL MATCH (p)-[:HAS_CRITERIA]->(:AdmissionCriteria)-[:REQUIRES_GROUP]->(sg:SubjectGroup) RETURN u.uni_id AS uid,p.major_code AS code,p.name AS name,collect(DISTINCT c.career_id) AS careers,collect(DISTINCT sg.group_code) AS groups').data()
    lookup={(r['uid'],r['code'],r['name']):r for r in old}
    rows=[];unis=[]
    for d in schools:
        unis.append({'id':d['id'],'name':d['name'],'short':d['shortName'],'city':d['provinceNew'],'revision':d['revision']})
        for p in d['programs']:
            context=lookup.get((d['id'],p['code'],p['name']),{})
            fee=p['tuition_annual'] if p['tuition_annual'] is not None else d['tuition']['max']
            if fee is None:fee=d['tuition']['min']
            rows.append({'id':p['programId'],'uid':d['id'],'code':p['code'],'name':p['name'],'careers':context.get('careers',[]),'groups':context.get('groups',[]),'fee':fee,'revision':d['revision'],'criteria':[{'id':f"{p['programId']}-{i}",'method':a['method'],'score':a['value'],'scale':a['scale'],'raw':a['raw']} for i,a in enumerate(p['admissions'])]})
    # Backup only this domain, never user data or credentials.
    backup=ROOT/'data/backups/graph_admissions_before_20261114.json'
    if not backup.exists():
        backup.write_text(json.dumps(session.run('MATCH (n) WHERE n:Program OR n:AdmissionCriteria OR n:FinancialAspect RETURN labels(n) AS labels,properties(n) AS properties').data(),ensure_ascii=False,default=str));backup.chmod(0o600)
    def replace(tx):
        ids=[d['id'] for d in schools]
        tx.run('MATCH (p:Program)-[:OFFERED_BY]->(u:University) WHERE u.uni_id IN $ids OPTIONAL MATCH (p)-[:HAS_CRITERIA]->(ad:AdmissionCriteria) OPTIONAL MATCH (p)-[:HAS_FINANCIAL]->(fa:FinancialAspect) DETACH DELETE ad,fa,p',ids=ids).consume()
        tx.run('UNWIND $rows AS row MATCH (u:University {uni_id:row.id}) SET u.name=row.name,u.short_name=row.short,u.catalog_revision=row.revision WITH u,row OPTIONAL MATCH (u)-[r:LOCATED_AT]->() DELETE r WITH u,row MERGE (l:Location {city:row.city}) MERGE (u)-[:LOCATED_AT]->(l)',rows=unis).consume()
        for offset in range(0,len(rows),200):
            batch=rows[offset:offset+200]
            tx.run('UNWIND $rows AS row MATCH (u:University {uni_id:row.uid}) CREATE (p:Program {program_id:row.id,major_code:row.code,name:row.name,catalog_revision:row.revision,educational_credential_awarded:"Chưa cung cấp trong file"}) CREATE (p)-[:OFFERED_BY]->(u) WITH p,row FOREACH (fee IN CASE WHEN row.fee IS NULL THEN [] ELSE [row.fee] END | CREATE (f:FinancialAspect {academic_year:2026,tuition_fee_annual:fee,effective_annual_cost:fee,catalog_revision:row.revision}) CREATE (p)-[:HAS_FINANCIAL]->(f))',rows=batch).consume()
            tx.run('UNWIND $rows AS row MATCH (p:Program {program_id:row.id}) UNWIND row.careers AS cid MATCH (c:Career {career_id:cid}) MERGE (p)-[:PREPARES_FOR]->(c)',rows=batch).consume()
            tx.run('UNWIND $rows AS row MATCH (p:Program {program_id:row.id}) UNWIND row.criteria AS value CREATE (a:AdmissionCriteria {criteria_id:value.id,year:2026,is_latest:true,method:value.method,benchmark_score:value.score,score_scale:value.scale,source_raw:value.raw,gender_requirement:"Any",catalog_revision:row.revision}) CREATE (p)-[:HAS_CRITERIA]->(a) WITH a,row UNWIND row.groups AS code MATCH (g:SubjectGroup {group_code:code}) MERGE (a)-[:REQUIRES_GROUP]->(g)',rows=batch).consume()
    session.execute_write(replace)
    print('Graph imported',len(rows),'programs. Existing exact-match career/group context:',sum(bool(r['careers']) and bool(r['groups']) for r in rows))
