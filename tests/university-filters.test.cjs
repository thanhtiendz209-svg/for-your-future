const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('apps/web/public/app.js','utf8');
function app() {
 const ctx={window:{location:{hash:'#truong-dai-hoc'},addEventListener(){}},localStorage:{getItem:()=>null},console};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 ctx.unis=JSON.parse(fs.readFileSync('apps/web/public/data/universities.json','utf8'));
 ctx.careers=JSON.parse(fs.readFileSync('apps/web/public/data/careers.json','utf8'));
 ctx.details=JSON.parse(fs.readFileSync('apps/web/public/data/school_details.json','utf8'));
 vm.runInContext('state.universities=unis;state.schoolDetails=details;state.careers=careers;state.uniFilter={...UNIVERSITY_FILTER_DEFAULTS}',ctx);
 return {ctx,run:s=>vm.runInContext(s,ctx),ids:(f={})=>{ctx.f=f;return Array.from(vm.runInContext('state.uniFilter={...UNIVERSITY_FILTER_DEFAULTS,...f};filterUniversities().map(u=>u.id)',ctx));}};
}
test('accentless school, major, old and new province queries match accented queries',()=>{
 const a=app();assert.equal(a.ids().length,126);
 for (const [accented,plain] of [['Bách khoa Hà Nội','bach khoa ha noi'],['Công nghệ thông tin','cong nghe thong tin'],['Bình Dương','binh duong'],['Thừa Thiên Huế','thua thien hue'],['Hải Dương','hai duong'],['Đắk Lắk','dak lak']]) {
  const left=a.ids({query:accented}),right=a.ids({query:plain});
  assert.ok(left.length>0,accented);assert.deepEqual(left,right,plain);
 }
 assert.ok(a.ids({query:'hust'}).includes('uni-001'));
 assert.deepEqual(a.ids({query:'khong co truong nao nhu nay'}),[]);
});
test('province new and old filters combine without inventing mappings',()=>{
 const a=app();const ids=a.ids({provinceOld:'Bình Dương'});assert.equal(ids.length,3);
 assert.deepEqual(a.ids({provinceNew:'TP. Hồ Chí Minh',provinceOld:'Bình Dương'}),ids);
 assert.equal(a.ids({provinceNew:'Hà Nội',provinceOld:'Bình Dương'}).length,0);
 assert.equal(a.ids({provinceOld:'Hải Dương',provinceNew:'Hải Phòng'}).length,1);
});
test('major names/codes, tuition, THPT ranges and method filtering use dataset',()=>{
 const a=app();assert.ok(a.ids({major:'cong nghe thong tin'}).length>0);
 assert.ok(a.ids({major:'IT-E10'}).includes('uni-001'));
 assert.ok(a.ids({tuition:'20–40 triệu'}).includes('uni-001'));
 const ids=a.ids({score:'Trên 27',method:'Điểm THPT 2026'});
 assert.ok(ids.length>0);
 for(const id of ids) {
  const u=a.ctx.unis.find(u=>u.id===id);
  assert.ok(u.admissions2026.thptValues.some(n=>n>27&&n<=30));
  assert.ok(u.admissionMethods.includes('Điểm THPT 2026'));
 }
});
test('fit filter requires real RIASEC; missing and zero tuition stay distinct',()=>{
 const a=app();assert.equal(a.ids({fitMin:'≥60%'}).length,0);
 a.run("state.results.riasec={scores:{R:45,I:40,A:10,S:15,E:20,C:35}};");
 assert.ok(a.ids({fitMin:'≥60%'}).length>0);
 a.run("state.universities=[{id:'free',tuition:0},{id:'unknown',tuition:null}];state.schoolDetails=[]");
 assert.deepEqual(a.ids({tuition:'Dưới 20 triệu'}),['free']);
});
test('filter markup escapes input, renders one results grid and labels controls',()=>{
 const a=app();a.ctx.query='<img src=x onerror=alert(1)>';
 a.run('state.uniFilter.query=query');
 const html=a.run('renderUniversityExplorerHtml()');
 assert.ok(html.includes('&lt;img'));
 assert.ok(!html.includes('<img src=x onerror'));
 assert.equal((html.match(/id="ue-grid"/g)||[]).length,1);
 assert.ok(html.includes('aria-live="polite"'));
});

test('major suggestions deduplicate typography/ordinals without stripping meaningful numbers',()=>{
 const a=app();
 const names=Array.from(a.run('universityFilterOptions().majors'));
 a.ctx.labels=names;
 assert.equal(a.run('new Set(labels.map(majorKey)).size'),names.length);
 assert.ok(!names.some(n=>/^\(\d+\)/.test(n)));
 assert.ok(names.some(n=>n.includes('2+2')));
 assert.equal(a.run("cleanMajorLabel('(1) Kế toán (*)')"),'Kế toán');
 assert.equal(a.run("cleanMajorLabel('Biên phòng (Quân khu 4)')"),'Biên phòng (Quân khu 4)');
});
test('complete major selection is exact and lookup keeps original program scores',()=>{
 const a=app();
 a.ids({major:'Quan tri kinh doanh'});
 const rows=Array.from(a.run('majorLookupRows()'));
 assert.ok(rows.length>0);
 for(const row of rows) {a.ctx.row=row;assert.equal(a.run('majorKey(row.p.name)'), 'quan tri kinh doanh');assert.ok(!/quoc te/.test(a.run('majorKey(row.p.name)')));}
 a.ids({major:'IT-E10'});
 assert.ok(a.run('majorLookupRows().every(row=>row.p.code==="IT-E10")'));
 a.ids({major:'Ke toan'});
 assert.ok(a.run('majorLookupRows().some(row=>row.p.name.startsWith("(1)"))'));
 const before=JSON.stringify(a.ctx.details);
 const html=a.run('renderMajorLookupResults()');assert.ok(html.includes('major-group'));assert.ok(!html.includes('<table'));
 const table=a.run('renderMajorLookupGroupRows(majorLookupGroups()[0])');assert.ok(table.includes('major-lookup-table'));assert.equal(JSON.stringify(a.ctx.details),before);
});
test('method and THPT score filters in lookup apply to matching program rows',()=>{
 const a=app();a.ids({major:'Ke toan',method:'Điểm THPT 2026',score:'Trên 27'});
 const rows=Array.from(a.run('majorLookupRows()'));
 assert.ok(rows.length>0);
 for(const row of rows)assert.ok(row.p.admissions.some(x=>x.method==='Điểm THPT 2026'&&x.scale===30&&x.value>27));
});

test('major blocks collect all school programs exactly once and start collapsed',()=>{
 const a=app();
 const groups=Array.from(a.run('majorLookupGroups()'));
 assert.ok(groups.length>12);
 assert.equal(new Set(groups.map(g=>g.key)).size,groups.length);
 assert.equal(groups.reduce((n,g)=>n+g.rows.length,0),a.run('majorLookupRows().length'));
 for(const g of groups) {a.ctx.group=g;assert.ok(a.run('group.rows.every(row=>majorKey(row.p.name)===group.key)'));}
 const html=a.run('renderMajorLookupResults()');
 assert.equal((html.match(/<details /g)||[]).length,12);
 assert.ok(!html.includes('<table'));
 assert.ok(!/<details[^>]*\sopen[ >]/.test(html));
 a.ids({major:'ke toan'});
 assert.equal(a.run('majorLookupGroups().length'),1);
 assert.equal(a.run('majorLookupGroups()[0].key'),'ke toan');
 assert.ok(a.run('majorLookupGroups()[0].rows.length')>20);
 assert.ok(a.run('renderMajorLookupGroupRows(majorLookupGroups()[0],1)').includes('data-major-program-page="0"'));
 a.ids({major:'khong co nganh nay'});
 assert.ok(a.run('renderMajorLookupResults()').includes('Không tìm thấy ngành'));
});

test('personalized recommendations and lookup use the same program and comparable scores',()=>{
 const a=app();
 a.run(`state.results.riasec={code:'IRC'};
  state.currentUser={user_id:'example'};state.authToken='example-token';
  schoolFitSession={owner:'example',token:'example-token',province:'',combination:'A00',scoreOnly:true,
   profile:{target_year:2026,background:{hometown_province:'TP HCM'},academic:{subject_scores:{'Toán':8,'Vật lý':9,'Hóa học':9}}}};
 `);
 assert.equal(a.run('schoolFitContext().tests[0].score'),26);
 const html=a.run('renderSchoolRecommendations()');
 assert.equal((html.match(/name="school-fit-recommendations"/g)||[]).length,5);
 assert.ok(html.includes('Khớp nơi muốn học'));
 assert.ok(html.includes('Cần kiểm tra tổ hợp áp dụng tại trường'));
 a.ids({personal:'Bật',major:'Công nghệ thông tin',fitMin:'≥80%'});
 assert.ok(a.run('majorLookupRows().length>0'));
 assert.ok(a.run('majorLookupRows().every(row=>row.fit>=80&&row.references.some(r=>r.reaches&&r.threshold<=26))'));
 assert.equal(a.run("programScoreReferences({admissions:[{method:'Học bạ 2026',scale:30,value:20},{method:'Điểm THPT 2026',scale:40,value:20}]},schoolFitContext()).length"),0);
 a.run("state.currentUser={user_id:'different-account'}");
 assert.equal(a.run('schoolFitContext().tests.length'),0);
 assert.equal(a.run('schoolFitContext().provinceKey'),'');
});

test('school logos use verified local assets and preserve the old badge if absent',()=>{
 const a=app();
 const schools=a.ctx.unis.filter(u=>u.schoolLogo);
 assert.ok(schools.length>0&&schools.length<a.ctx.unis.length);
 for(const school of schools) assert.ok(fs.existsSync('apps/web/dist'+school.schoolLogo),school.id);
 assert.ok(a.run("schoolLogoMarkup(state.universities[0], 'badge')").includes('/school-logos/uni-001.webp'));
 assert.equal(a.run("schoolLogoMarkup({}, 'badge')"),'badge');
});
