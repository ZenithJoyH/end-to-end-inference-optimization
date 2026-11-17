'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
const { attach } = require('../transport-diag.cjs');

test('native fetch distinguishes success, pre-header close and after-header close without logging secrets', { timeout: 10000 }, async t => {
  const output = [];
  const closeObserver = attach({ sink: record => output.push(record) });
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/before')) { req.socket.destroy(); return; }
    if (req.url.startsWith('/after')) {
      res.writeHead(200, { 'Content-Type': 'text/plain', 'Content-Length': '9999' });
      res.flushHeaders();
      res.write('synthetic-test-body\n');
      setTimeout(() => req.socket.destroy(), 20);
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('synthetic-success\n');
  });
  t.after(() => { closeObserver(); server.closeAllConnections(); server.close(); });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const origin = 'http://127.0.0.1:' + server.address().port;
  for (const path of ['/success?SECRET_QUERY', '/before?SECRET_QUERY', '/after?SECRET_QUERY']) {
    try {
      const response = await fetch(origin + path, {
        method: 'POST', headers: { Authorization: 'Bearer SECRET_TOKEN' },
        body: 'SECRET_SYNTHETIC_BODY', signal: AbortSignal.timeout(2000),
      });
      const body = await response.text();
      assert.equal(body, 'synthetic-success\n');
    } catch (error) {
      if (path.startsWith('/success')) throw error;
    }
  }
  assert.ok(output.some(x => x.event === 'complete' && x.status === 200));
  assert.ok(output.some(x => x.event === 'error' && x.phase === 'before_headers'));
  assert.ok(output.some(x => x.event === 'error' && x.phase === 'after_headers' && x.status === 200));
  assert.ok(output.some(x => x.event === 'error' && x.causes.some(c => c.code === 'UND_ERR_SOCKET')));
  assert.ok(!JSON.stringify(output).includes('SECRET'));
  console.log('SAFE_NATIVE_TRACE ' + JSON.stringify(output));
});
