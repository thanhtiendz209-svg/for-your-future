const assert = require('node:assert/strict');
const fs = require('node:fs');
const {test} = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync('apps/web/public/app.js', 'utf8');

function setup(fetch) {
  let probe;
  const ids = ['health-pg-badge', 'health-neo4j-badge', 'health-ollama-badge', 'health-db-backend', 'admin-log-output'];
  const nodes = new Map(ids.map(id => [id, {textContent: '', classList: {toggle() {}}}]));
  nodes.set('btn-admin-probe', {addEventListener(_, onClick) { probe = onClick; }});
  const toasts = [];
  const context = vm.createContext({
    window: {location: {hash: '#quan-tri'}, addEventListener() {}},
    localStorage: {getItem: () => null},
    document: {getElementById: id => nodes.get(id)},
    console,
    fetch,
    container: {innerHTML: ''},
    recordToast: (...args) => toasts.push(args),
  });
  vm.runInContext(source, context);
  vm.runInContext('showToast = recordToast; renderAdmin(container);', context);
  return {probe, nodes, toasts, html: context.container.innerHTML};
}

test('admin panel shows live database failure details from a 503 response', async () => {
  const app = setup(async () => ({
    ok: false,
    status: 503,
    json: async () => ({
      status: 'degraded',
      database: {status: 'unhealthy', backend: 'postgresql'},
      neo4j: {status: 'not_checked'},
      ollama: {status: 'not_checked'},
    }),
  }));
  assert.match(app.html, /Chưa kiểm tra/);
  await app.probe();
  assert.equal(app.nodes.get('health-pg-badge').textContent, 'Lỗi kết nối');
  assert.equal(app.nodes.get('health-db-backend').textContent, 'PostgreSQL');
  assert.match(app.nodes.get('admin-log-output').textContent, /"status": "degraded"/);
  assert.equal(app.toasts[0][1], 'error');
});

test('admin panel labels local SQLite and clears stale backend state on network errors', async () => {
  let calls = 0;
  const app = setup(async () => {
    if (calls++) throw new Error('Network error');
    return {ok: true, json: async () => ({
      database: {status: 'healthy', backend: 'sqlite'},
      neo4j: {status: 'unhealthy'},
      ollama: {status: 'offline'},
    })};
  });
  await app.probe();
  assert.equal(app.nodes.get('health-db-backend').textContent, 'SQLite cục bộ');
  assert.equal(app.toasts[0][1], 'info');
  await app.probe();
  assert.equal(app.nodes.get('health-pg-badge').textContent, 'Chưa xác định');
  assert.match(app.nodes.get('admin-log-output').textContent, /Network error/);
});
