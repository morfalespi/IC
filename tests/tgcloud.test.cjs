const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const pair = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const publicJwk = pair.publicKey.export({ format: 'jwk' });
function decryptDispatch(call) {
  const body = JSON.parse(call[2].body);
  assert.deepEqual(Object.keys(body.inputs), ['payload']);
  assert.equal(body.inputs.payload.includes('alice'), false);
  const envelope = JSON.parse(body.inputs.payload);
  const key = crypto.privateDecrypt({ key: pair.privateKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' }, Buffer.from(envelope.key, 'base64url'));
  const ciphertext = Buffer.from(envelope.data, 'base64url');
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64url'));
  decipher.setAAD(Buffer.from('IC-dispatch-v1'));
  decipher.setAuthTag(ciphertext.subarray(-16));
  return JSON.parse(Buffer.concat([decipher.update(ciphertext.subarray(0, -16)), decipher.final()]).toString());
}

async function setup({ status = 204, authorized = true, duplicate = false } = {}) {
  const calls = [];
  const context = vm.createContext({ console: { error() {} }, Date, Number, String, Error, Array, crypto: crypto.webcrypto, TextEncoder, Uint8Array });
  const fetch = async (url, options) => { calls.push(['dispatch', url, options]); return { status }; };
  fetch.body = { json: value => JSON.stringify(value) };
  const api = new Proxy({}, { get: (_, method) => async value => { calls.push([method, value]); return { message_id: 7 }; } });
  const builder = () => ({ values() { return this; }, onConflictDoNothing() { return this; }, returning() { return Promise.resolve(duplicate ? [] : [{ id: 'update' }]); } });
  const db = { insert: builder, all: async () => [{ id: 1 }] };
  const column = () => ({ primaryKey() { return this; }, notNull() { return this; } });
  const sdk = new vm.SyntheticModule(['api', 'fetch', 'db', 'BotApiError'], function() {
    this.setExport('api', api); this.setExport('fetch', fetch); this.setExport('db', db); this.setExport('BotApiError', class extends Error {});
  }, { context });
  const dbSdk = new vm.SyntheticModule(['table', 'integer', 'text'], function() {
    this.setExport('table', (name, columns) => columns); this.setExport('integer', column); this.setExport('text', column);
  }, { context });
  const cache = new Map([['sdk', sdk], ['sdk/db', dbSdk]]);
  function load(file) {
    file = path.resolve(file);
    if (cache.has(file)) return cache.get(file);
    let source = fs.readFileSync(file, 'utf8');
    if (file.endsWith('/segredos.js')) source = "export const GH_DISPATCH_TOKEN = 'synthetic'; export const GH_REPOSITORY = 'fixture/IC'; export const IC_DISPATCH_PUBLIC_KEY = " + JSON.stringify(publicJwk) + ';';
    if (authorized && file.endsWith('/autorizacao.js')) source = source.replace('ALLOWED_USER_IDS = []', "ALLOWED_USER_IDS = ['42']").replace('ALLOWED_CHAT_IDS = []', "ALLOWED_CHAT_IDS = ['42']");
    const module = new vm.SourceTextModule(source, { context, identifier: file });
    cache.set(file, module);
    return module;
  }
  return { calls, async module(file) { const m = load(file); if (m.status === 'unlinked') await m.link((specifier, parent) => cache.get(specifier) || load(path.resolve(path.dirname(parent.identifier), specifier))); if (m.status !== 'evaluated') await m.evaluate(); return m.namespace; } };
}

(async () => {
  let app = await setup();
  const input = await app.module('tgcloud/lib/entrada.js');
  assert.equal(input.lerEntrada('-1000000000008 @group_name').id, '-1000000000008');
  for (const value of ['0', 'arbitrary text', 'a\nb', '@', '123 invalid']) assert.throws(() => input.lerEntrada(value));
  assert.equal(input.lerCallback(input.codigoCallback('f', input.lerEntrada('42 @alice'))).entrada.id, '42');
  assert.throws(() => input.lerCallback('bogus:action'));
  const envio = await app.module('tgcloud/lib/envio.js');
  await envio.editarCartao(42, 7, '<h2>Header</h2>');
  assert.equal(app.calls[0][0], 'editMessageText');
  assert.equal(app.calls[0][1].text, 'Header');
  assert.equal(app.calls[0][1].rich_message, undefined);

  app = await setup({ authorized: false });
  let handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42 }, text: '@alice' }, { update: { update_id: 1 } });
  assert.equal(app.calls.length, 0);

  app = await setup({ duplicate: true });
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42 }, text: '@alice' }, { update: { update_id: 1 } });
  assert.equal(app.calls.length, 0);

  app = await setup({ status: 503 });
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42 }, text: '@alice' }, { update: { update_id: 2 } });
  assert.equal(app.calls.filter(c => c[0] === 'dispatch').length, 1, 'Uncertain dispatch must not be retried');
  assert.match(app.calls.at(-1)[1].text, /Falha/);

  app = await setup();
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42 }, text: '42 @alice' }, { update: { update_id: 3 } });
  const dispatch = app.calls.find(c => c[0] === 'dispatch');
  assert.equal(decryptDispatch(dispatch).expected_id, '42');
  assert.equal(decryptDispatch(dispatch).chat, '42');
  assert.equal(decryptDispatch(dispatch).alvo, 'alice');

  app = await setup();
  handler = await app.module('tgcloud/handlers/inline_query.js');
  await handler.default({ id: 'query', from: { id: 42 }, query: 'alice' });
  assert.deepEqual(JSON.parse(JSON.stringify(app.calls[0][1].results)), []);
  assert.equal(app.calls.filter(c => c[0] === 'dispatch').length, 0);
  console.log('TgCloud controlled handler checks passed: authorization, dispatch, callbacks, replay suppression and inline privacy.');
})().catch(error => { console.error(error); process.exitCode = 1; });
