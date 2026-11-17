'use strict';

// Task-private observation only. Never read or serialize URL, headers, body,
// message, stack, peer address, process environment, or request properties.
const dc = require('node:diagnostics_channel');
const { performance } = require('node:perf_hooks');

const CODES = new Set([
  'UND_ERR_SOCKET', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT',
  'UND_ERR_BODY_TIMEOUT', 'UND_ERR_ABORTED', 'UND_ERR_DESTROYED',
  'ECONNRESET', 'ECONNREFUSED', 'ETIMEDOUT', 'ENOTFOUND', 'EAI_AGAIN',
  'ABORT_ERR', 'ERR_HTTP2_STREAM_CANCEL', 'ERR_HTTP2_SESSION_ERROR',
]);
const NAMES = new Set([
  'Error', 'TypeError', 'SocketError', 'ConnectTimeoutError',
  'HeadersTimeoutError', 'BodyTimeoutError', 'AbortError', 'TimeoutError',
  'APIConnectionError', 'APIConnectionTimeoutError',
]);

function own(object, key) {
  if (!object || (typeof object !== 'object' && typeof object !== 'function')) return undefined;
  const descriptor = Object.getOwnPropertyDescriptor(object, key);
  return descriptor && Object.hasOwn(descriptor, 'value') ? descriptor.value : undefined;
}

function errorCodes(error) {
  const result = [];
  const seen = new Set();
  for (let depth = 0; depth < 5 && error && !seen.has(error); depth++) {
    seen.add(error);
    const name = own(error, 'name');
    const code = own(error, 'code');
    result.push({
      name: NAMES.has(name) ? name : 'OtherError',
      code: CODES.has(code) ? code : 'OTHER',
    });
    error = own(error, 'cause');
  }
  return result;
}

function attach({ sink, now = () => performance.now(), channels = dc, maxRecords = 256 } = {}) {
  if (typeof sink !== 'function') throw new TypeError('sink required');
  const states = new WeakMap();
  const sockets = new WeakMap();
  const subscriptions = [];
  let sequence = 0;
  let socketSequence = 0;
  let records = 0;
  function state(request) {
    if (!request || typeof request !== 'object') return undefined;
    let value = states.get(request);
    if (!value) {
      value = { id: ++sequence, start: now(), headers: false, status: undefined };
      states.set(request, value);
    }
    return value;
  }
  function emit(value, event, extra = {}) {
    if (!value || records >= maxRecords) return;
    records++;
    const elapsed = now() - value.start;
    const elapsedMs = Number.isFinite(elapsed) ? Math.max(0, Math.round(elapsed * 1000) / 1000) : null;
    sink({ schema: 1, event, request: value.id, elapsedMs, ...extra });
  }
  function subscribe(name, handler) {
    const listener = message => {
      // Undici publishes synchronously. Observation must not affect requests.
      try { handler(message); } catch { /* diagnostic failure is isolated */ }
    };
    const channel = channels.channel(name);
    channel.subscribe(listener);
    subscriptions.push([channel, listener]);
  }
  subscribe('undici:request:create', message => {
    emit(state(own(message, 'request')), 'created');
  });
  subscribe('undici:client:sendHeaders', message => {
    const socket = own(message, 'socket');
    const alpn = own(socket, 'alpnProtocol');
    let connection;
    if (socket && typeof socket === 'object') {
      connection = sockets.get(socket);
      if (!connection) {
        connection = { id: ++socketSequence, uses: 0 };
        sockets.set(socket, connection);
      }
      connection.uses++;
    }
    emit(state(own(message, 'request')), 'sent', {
      alpn: alpn === 'h2' || alpn === 'http/1.1' ? alpn : 'unreported',
      socket: connection?.id ?? null,
      socketUse: connection?.uses ?? null,
    });
  });
  subscribe('undici:request:headers', message => {
    const value = state(own(message, 'request'));
    if (!value) return;
    value.headers = true;
    const status = own(own(message, 'response'), 'statusCode');
    if (Number.isInteger(status) && status >= 100 && status <= 599) value.status = status;
    emit(value, 'headers', { status: value.status ?? null });
  });
  subscribe('undici:request:trailers', message => {
    const value = state(own(message, 'request'));
    emit(value, 'complete', { status: value?.status ?? null });
  });
  subscribe('undici:request:error', message => {
    const value = state(own(message, 'request'));
    emit(value, 'error', {
      phase: value?.headers ? 'after_headers' : 'before_headers',
      status: value?.status ?? null,
      causes: errorCodes(own(message, 'error')),
    });
  });
  return () => {
    for (const [channel, listener] of subscriptions) channel.unsubscribe(listener);
  };
}

if (process.env.DSH_TRANSPORT_DIAG_ENABLE === '1') {
  attach({ sink: record => {
    process.stderr.write('[dsh-transport-meta] ' + JSON.stringify(record) + '\n');
  } });
}

module.exports = { attach, errorCodes };
