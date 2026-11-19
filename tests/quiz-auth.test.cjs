const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('apps/web/public/app.js', 'utf8');
function setup(status, token = null) {
  const stored = new Map();
  const sandbox = {
    window: { location: { hash: '#trac-nghiem/riasec' }, addEventListener() {} },
    localStorage: { getItem() { return null; } },
    sessionStorage: { setItem(k, v) { stored.set(k, v); }, getItem(k) { return stored.get(k); }, removeItem(k) { stored.delete(k); } },
    document: { getElementById() { return null; } },
    fetch: async () => ({ ok: status === 200 }), console,
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox);
  vm.runInContext(`state.authToken = ${JSON.stringify(token)};`, sandbox);
  return { sandbox, stored };
}
test('guest and expired sessions redirect and remember selected quiz', async () => {
  for (const token of [null, 'expired']) {
    const { sandbox, stored } = setup(401, token);
    await vm.runInContext("renderQuizPlayer({}, 'riasec')", sandbox);
    assert.equal(sandbox.window.location.hash, '#dang-nhap');
    assert.equal(stored.get('fyf_after_login'), '#trac-nghiem/riasec');
    assert.equal(vm.runInContext("authDestination('student')", sandbox), '#thiet-lap-ho-so');
    assert.equal(stored.has('fyf_after_login'), true);
  }
});
test('verified session can open quiz', async () => {
  const { sandbox } = setup(200, 'valid');
  vm.runInContext("state.questions.riasec = [{ text: 'Câu hỏi' }];", sandbox);
  const container = {};
  sandbox.container = container;
  await vm.runInContext("renderQuizPlayer(container, 'riasec')", sandbox);
  assert.equal(sandbox.window.location.hash, '#trac-nghiem/riasec');
  assert.match(container.innerHTML, /Câu hỏi/);
});

test('student starts intake and administrator opens management', () => {
  const { sandbox } = setup(200);
  assert.equal(vm.runInContext("authDestination('student')", sandbox), '#thiet-lap-ho-so');
  assert.equal(vm.runInContext("authDestination('admin')", sandbox), '#quan-tri');
});

test('assessment synchronization sends current account token and preserves failed queue', async () => {
  const { sandbox } = setup(200);
  const storage = new Map();
  sandbox.localStorage = {getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)};
  const result={code:'SIA',scores:{S:30,I:20,A:10}};
  storage.set('fyf_pending_assessments_account-a',JSON.stringify({riasec:result}));
  storage.set('fyf_pending_assessments_account-b',JSON.stringify({mbti:{type:'INTJ'}}));
  vm.runInContext("state.currentUser={user_id:'account-a'};state.authToken='token-a'",sandbox);
  const sent=[];
  sandbox.fetch=async(url,options)=>{sent.push({url,...options});return {ok:true}};
  await vm.runInContext('syncAccountAssessments()',sandbox);
  assert.equal(sent.length,1);
  assert.equal(sent[0].headers.Authorization,'Bearer token-a');
  assert.equal(JSON.parse(sent[0].body).result_code,'SIA');
  assert.equal(storage.get('fyf_pending_assessments_account-a'),'{}');
  assert.ok(JSON.parse(storage.get('fyf_pending_assessments_account-b')).mbti);
  storage.set('fyf_pending_assessments_account-a',JSON.stringify({riasec:result}));
  sandbox.fetch=async()=>({ok:false});
  await assert.rejects(vm.runInContext('syncAccountAssessments()',sandbox));
  assert.ok(JSON.parse(storage.get('fyf_pending_assessments_account-a')).riasec);
});

test('quiz drafts stay scoped to the active quiz and account', async () => {
  const {sandbox} = setup(200, 'valid');
  sandbox.container = {};
  vm.runInContext(`
    state.questions.riasec = [{text:'RIASEC one'},{text:'RIASEC two'}];
    state.questions.mbti = [{text:'MBTI one'},{text:'MBTI two'}];
    state.currentUser = {user_id:'first'};
  `, sandbox);
  await vm.runInContext("renderQuizPlayer(container, 'riasec')", sandbox);
  vm.runInContext('state.quizAttempt.index=1; state.quizAttempt.answers[0]=2;', sandbox);
  await vm.runInContext("renderQuizPlayer(container, 'riasec')", sandbox);
  assert.match(sandbox.container.innerHTML, /RIASEC two/);
  sandbox.window.location.hash = '#trac-nghiem/mbti';
  await vm.runInContext("renderQuizPlayer(container, 'mbti')", sandbox);
  assert.match(sandbox.container.innerHTML, /MBTI one/);
  assert.equal(vm.runInContext('state.quizAttempt.answers[0]', sandbox), -1);
  vm.runInContext("state.quizAttempt.answers[0]=1; state.currentUser={user_id:'second'};", sandbox);
  await vm.runInContext("renderQuizPlayer(container, 'mbti')", sandbox);
  assert.equal(vm.runInContext('state.quizAttempt.answers[0]', sandbox), -1);
});
