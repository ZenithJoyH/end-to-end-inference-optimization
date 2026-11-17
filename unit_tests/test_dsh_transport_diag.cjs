'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { attach } = require('../scripts/dsh/transport-diag.cjs');

function fixture({ sinkThrows = false, maxRecords = 256 } = {}) {
  const handlers = new Map();
  const output = [];
  let time = 10;
  const channels = { channel: name => ({
    subscribe: listener => handlers.set(name, listener),
    unsubscribe: listener => { if (handlers.get(name) === listener) handlers.delete(name); },
  }) };
  const close = attach({
    channels, now: () => time, maxRecords,
    sink: record => { output.push(record); if (sinkThrows) throw new Error('sink'); },
  });
  const publish = (name, message) => {
    time += 25;
    const listener = handlers.get('undici:' + name);
    if (listener) listener(message);
  };
  return { output, publish, close, handlers };
}

function poison(extra = {}) {
  const object = { ...extra };
  for (const name of ['message', 'stack', 'headers', 'body', 'origin', 'path', 'query', 'address', 'remoteAddress']) {
    Object.defineProperty(object, name, { get() { throw new Error('SECRET_GETTER_' + name); } });
  }
  return Object.freeze(object);
}

test('success emits only fixed metadata and never inspects request/header/body/address', () => {
  const f = fixture();
  const request = poison();
  f.publish('request:create', { request });
  f.publish('client:sendHeaders', poison({ request, socket: poison({ alpnProtocol: 'http/1.1' }) }));
  f.publish('request:headers', { request, response: poison({ statusCode: 200 }) });
  f.publish('request:trailers', poison({ request }));
  assert.deepEqual(f.output.map(x => x.event), ['created', 'sent', 'headers', 'complete']);
  assert.equal(f.output[3].status, 200);
  assert.equal(f.output[3].elapsedMs, 75);
  assert.equal(f.output[1].alpn, 'http/1.1');
  f.close();
  assert.equal(f.handlers.size, 0);
});

test('pre-header disconnect is distinct from after-header disconnect without leaking error messages', () => {
  const f = fixture();
  const error = poison({ name: 'TypeError', code: 'SECRET_CODE_PAYLOAD', cause: poison({ name: 'SocketError', code: 'UND_ERR_SOCKET' }) });
  const first = poison();
  f.publish('request:create', { request: first });
  f.publish('request:error', { request: first, error });
  const second = poison();
  f.publish('request:create', { request: second });
  f.publish('request:headers', { request: second, response: poison({ statusCode: 200 }) });
  f.publish('request:error', { request: second, error });
  const errors = f.output.filter(x => x.event === 'error');
  assert.equal(errors[0].phase, 'before_headers');
  assert.equal(errors[0].status, null);
  assert.equal(errors[1].phase, 'after_headers');
  assert.equal(errors[1].status, 200);
  assert.deepEqual(errors[0].causes, [{ name: 'TypeError', code: 'OTHER' }, { name: 'SocketError', code: 'UND_ERR_SOCKET' }]);
  assert.ok(!JSON.stringify(f.output).includes('SECRET'));
  f.close();
});

test('socket reuse exposes only process-local sequence numbers, never peer addresses', () => {
  const f = fixture();
  const socket = poison({ alpnProtocol: 'h2' });
  f.publish('client:sendHeaders', { request: poison(), socket });
  f.publish('client:sendHeaders', { request: poison(), socket });
  assert.deepEqual(f.output.map(x => [x.socket, x.socketUse]), [[1, 1], [1, 2]]);
  assert.ok(!JSON.stringify(f.output).includes('SECRET'));
  f.close();
});

test('unknown strings, missing fields, cycles and throwing sinks cannot affect the caller', () => {
  const f = fixture({ sinkThrows: true, maxRecords: 2 });
  const request = poison();
  const error = { name: 'SECRET_NAME', code: 'SECRET_CODE' };
  error.cause = error;
  assert.doesNotThrow(() => {
    f.publish('request:create', { request });
    f.publish('request:error', { request, error });
    f.publish('request:error', { request, error });
    f.publish('request:headers', {});
  });
  assert.equal(f.output.length, 2);
  assert.ok(!JSON.stringify(f.output).includes('SECRET'));
  f.close();
});

test('plain literal secrets in ignored properties never appear in output', () => {
  const f = fixture();
  const request = Object.freeze({ origin: 'https://SECRET_ENDPOINT', path: '/SECRET_QUERY', headers: 'Authorization: SECRET_TOKEN', body: 'SECRET_BODY' });
  f.publish('request:create', { request });
  f.publish('client:sendHeaders', { request, headers: 'SECRET_HEADER', socket: { alpnProtocol: 'SECRET_ALPN', remoteAddress: 'SECRET_ADDRESS' } });
  f.publish('request:error', { request, error: { name: 'Error', code: 'ECONNRESET', message: 'SECRET_MESSAGE', stack: 'SECRET_STACK', body: 'SECRET_ERROR_BODY' } });
  assert.equal(f.output[1].alpn, 'unreported');
  assert.ok(!JSON.stringify(f.output).includes('SECRET'));
  f.close();
});
