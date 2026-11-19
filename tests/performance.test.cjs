const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('apps/web/public/app.js', 'utf8');
function setup(fetch) {
  const context = {window: {location: {hash: '#home'}, addEventListener() {}},
    localStorage: {getItem: () => null}, console, fetch};
  vm.createContext(context); vm.runInContext(source, context);
  return {context, run: code => vm.runInContext(code, context)};
}
test('home skips large datasets; concurrent requests share work and loaded data are reused', async () => {
  const requests = [];
  const app = setup(async url => {requests.push(url); return {ok: true, json: async () => [{loaded: url}]};});
  await app.run('Promise.all([loadAllData(), loadAllData()])');
  assert.equal(requests.length, 7);
  assert.ok(requests.every(url => !/school_details|riasec_combinations/.test(url)));
  assert.equal(app.run("routeDataFiles('home').length"), 0);
  assert.equal(app.run("routeDataFiles('tra-cuu-nganh')[0][0]"), 'schoolDetails');
  app.run("state.results.riasec={code:'IRC'}");
  assert.equal(app.run("routeDataFiles('ket-qua','riasec')[0][0]"), 'riasecCombinations');
  assert.equal(app.run("routeDataFiles('ket-qua','riasec').length"), 1);
  await app.run("Promise.all([loadStaticData('schoolDetails','school_details.json'),loadStaticData('schoolDetails','school_details.json')])");
  assert.equal(requests.filter(url => url.includes('school_details')).length, 1);
  assert.equal(app.run("routeDataFiles('tra-cuu-nganh').length"), 0);
});
test('failed static data retries without refetching successful datasets', async () => {
  let attempts = 0;
  const app = setup(async () => ({ok: ++attempts > 1, json: async () => [{id: 'saved'}]}));
  await assert.rejects(app.run("loadStaticData('schoolDetails','school_details.json')"));
  assert.equal(app.run('state.schoolDetails.length'), 0);
  await app.run("loadStaticData('schoolDetails','school_details.json')");
  await app.run("loadStaticData('schoolDetails','school_details.json')");
  assert.equal(attempts, 2);
  assert.equal(app.run('state.schoolDetails[0].id'), 'saved');
});
test('slow university route cannot overwrite a newer home route', async () => {
  let release;
  const app = setup(() => new Promise(resolve => {release = () => resolve({ok: true, json: async () => []});}));
  const container = {innerHTML: '', querySelector: () => ({addEventListener() {}})};
  app.context.document = {getElementById: id => id === 'app-container' ? container : null,
    querySelectorAll: () => [], body: {classList: {toggle() {}}}};
  app.context.window.scrollTo = () => {};
  app.run("renderHome = c => {c.innerHTML='HOME'}; refreshIcons=()=>{}; refreshVisibleMotion=()=>{}");
  app.context.window.location.hash = '#tra-cuu-nganh';
  const pending = app.run('renderRoute()');
  app.context.window.location.hash = '#home';
  await app.run('renderRoute()'); release(); await pending;
  assert.equal(container.innerHTML, 'HOME');
});

test('RIASEC illustrations use the new animated artwork in the deployable site', () => {
  const app = setup();
  const images = [...app.run("renderRiasecTripletImages('CSI', 'large')").matchAll(/<img[^>]+>/g)];
  assert.equal(images.length, 3);
  for (const [index, letter] of [...'CSI'].entries()) {
    assert.ok(images[index][0].includes(`src="/riasec/animated/RIASEC_${letter}_animated.svg"`));
    assert.doesNotMatch(images[index][0], /onerror|\.webp/);
  }
  for (const letter of 'RIASEC') {
    const filename = `riasec/animated/RIASEC_${letter}_animated.svg`;
    const source = fs.readFileSync(`apps/web/public/${filename}`);
    assert.match(source.toString(), /@keyframes/);
    assert.deepEqual(fs.readFileSync(`apps/web/dist/${filename}`), source);
    assert.deepEqual(fs.readFileSync(`apps/web/dist/riasec/animated/${letter}.svg`), source);
  }
});
