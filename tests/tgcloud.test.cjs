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

async function setup({ status = 204, duplicate = false, rejectRich = false, rejectRichPhoto = false, uncertainRich = false } = {}) {
  const calls = [];
  const context = vm.createContext({ console: { error() {} }, Date, Number, String, Error, Array, crypto: crypto.webcrypto, TextEncoder, Uint8Array });
  const fetch = async (url, options) => { calls.push(['dispatch', url, options]); return { status }; };
  fetch.body = { json: value => JSON.stringify(value) };
  class BotApiError extends Error { constructor(code) { super('Explicit API rejection'); this.code = code; } }
  const api = new Proxy({}, { get: (_, method) => async value => {
    calls.push([method, value]);
    if (value?.rich_message) {
      if (uncertainRich) throw new Error('Transport status unknown');
      if (rejectRich || (rejectRichPhoto && value.rich_message.media)) throw new BotApiError(400);
    }
    return { message_id: 7 };
  } });
  const builder = () => ({ values() { return this; }, onConflictDoNothing() { return this; }, returning() { return Promise.resolve(duplicate ? [] : [{ id: 'update' }]); } });
  const db = { insert: builder, all: async () => [{ id: 1 }] };
  const column = () => ({ primaryKey() { return this; }, notNull() { return this; } });
  const sdk = new vm.SyntheticModule(['api', 'fetch', 'db', 'BotApiError'], function() {
    this.setExport('api', api); this.setExport('fetch', fetch); this.setExport('db', db); this.setExport('BotApiError', BotApiError);
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
  assert.equal(app.calls[0][1].rich_message.html, '<h2>Header</h2>');
  assert.equal(app.calls[0][1].text, undefined);

  // Teclado nativo: os três botões selecionam o alvo, não o destino do IC.
  await envio.enviarMensagem(42, 'Menu', true);
  const keyboard = app.calls.at(-1)[1].reply_markup.keyboard;
  assert.deepEqual(JSON.parse(JSON.stringify(keyboard.map(row => row[0].text))),
    ['Escolher usuário', 'Escolher canal', 'Escolher grupo']);

  // Rejeição explícita 400: entregar a mesma informação em texto comum.
  app = await setup({ rejectRich: true });
  const envioFallback = await app.module('tgcloud/lib/envio.js');
  await envioFallback.enviarCartao(42, '<h2>Header</h2>');
  assert.deepEqual(app.calls.map(c => c[0]), ['sendRichMessage', 'sendMessage']);
  assert.equal(app.calls.at(-1)[1].text, 'Header');

  // Foto rejeitada: manter Rich sem a imagem, sem criar outra mensagem.
  app = await setup({ rejectRichPhoto: true });
  const envioFoto = await app.module('tgcloud/lib/envio.js');
  await envioFoto.enviarCartao(42, '<h2>Foto</h2>', 'telegram_photo_fixture_123');
  assert.deepEqual(app.calls.map(c => c[0]), ['sendRichMessage', 'sendRichMessage']);
  assert.equal(app.calls[0][1].rich_message.media[0].media.type, 'photo');
  assert.equal(app.calls[1][1].rich_message.media, undefined);

  // Resultado de envio incerto: proibir fallback automático ou duplicação.
  app = await setup({ uncertainRich: true });
  const envioIncerto = await app.module('tgcloud/lib/envio.js');
  await assert.rejects(() => envioIncerto.enviarCartao(42, '<h2>Foto</h2>'));
  assert.deepEqual(app.calls.map(c => c[0]), ['sendRichMessage']);


  const auth = await app.module('tgcloud/lib/autorizacao.js');
  assert.equal(auth.autorizado(42, 42, 'private'), true);
  assert.equal(auth.autorizado(43, 42, 'private'), false);
  assert.equal(auth.autorizado(42, 42, 'supergroup'), false);
  assert.equal(auth.autorizado(42, 42, 'private', true), false);
  assert.equal(auth.autorizado(undefined, 42, 'private'), false);

  app = await setup();
  let handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 43 }, chat: { id: 42, type: 'private' }, text: '@alice' }, { update: { update_id: 1 } });
  await handler.default({ from: { id: 42 }, chat: { id: -100123, type: 'supergroup' }, text: '@alice' }, { update: { update_id: 9 } });
  assert.equal(app.calls.length, 0);
  const callbacks = await app.module('tgcloud/handlers/callback_query.js');
  await callbacks.default({
    id: 'cb-group', from: { id: 42 },
    message: { chat: { id: -100123, type: 'supergroup' }, message_id: 6 },
    data: 'r:n:alice',
  }, { update: { update_id: 10 } });
  assert.equal(app.calls.filter(c => c[0] === 'dispatch').length, 0);
  assert.equal(app.calls.at(-1)[0], 'answerCallbackQuery');

  app = await setup({ duplicate: true });
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42, type: 'private' }, text: '@alice' }, { update: { update_id: 1 } });
  assert.equal(app.calls.length, 0);

  app = await setup({ status: 503 });
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42, type: 'private' }, text: '@alice' }, { update: { update_id: 2 } });
  assert.equal(app.calls.filter(c => c[0] === 'dispatch').length, 1, 'Uncertain dispatch must not be retried');
  assert.match(app.calls.at(-1)[1].text, /Falha/);

  app = await setup();
  handler = await app.module('tgcloud/handlers/message.js');
  await handler.default({ from: { id: 42 }, chat: { id: 42, type: 'private' }, text: '42 @alice' }, { update: { update_id: 3 } });
  const dispatch = app.calls.find(c => c[0] === 'dispatch');
  assert.equal(decryptDispatch(dispatch).expected_id, '42');
  assert.equal(decryptDispatch(dispatch).chat, '42');
  assert.equal(decryptDispatch(dispatch).alvo, 'alice');

  // Cada seleção do Telegram vira uma consulta, mas apenas no chat privado do dono.
  const selections = [
    { key: 'users_shared', data: { request_id: 1, users: [{
      user_id: 551, first_name: 'Alice', username: 'alice_demo',
      photo: [{ file_id: 'telegram_photo_551_fixture', width: 64, height: 64 }],
    }] }, expected: '551', target: 'alice_demo' },
    { key: 'chat_shared', data: { request_id: 2, chat_id: -1000000000008, title: 'Canal', username: 'canal_demo' },
      expected: '-1000000000008', target: 'canal_demo' },
    { key: 'chat_shared', data: { request_id: 3, chat_id: -1000000000009, title: 'Grupo', username: 'grupo_demo' },
      expected: '-1000000000009', target: 'grupo_demo' },
  ];
  for (const [index, selection] of selections.entries()) {
    app = await setup();
    handler = await app.module('tgcloud/handlers/message.js');
    await handler.default({
      from: { id: 42 }, chat: { id: 42, type: 'private' },
      [selection.key]: selection.data,
    }, { update: { update_id: 200 + index } });
    const call = app.calls.find(c => c[0] === 'dispatch');
    assert.ok(call, 'Selected target should be dispatched');
    const decoded = decryptDispatch(call);
    assert.equal(decoded.alvo, selection.target);
    assert.equal(decoded.expected_id, selection.expected);
    assert.equal(decoded.modo, 'resumo');
    if (index === 0) {
      const rich = app.calls.find(c => c[0] === 'sendRichMessage');
      assert.equal(rich[1].rich_message.media[0].media.media, 'telegram_photo_551_fixture');
    }
  }

  app = await setup();
  handler = await app.module('tgcloud/handlers/inline_query.js');
  await handler.default({ id: 'query', from: { id: 42 }, query: 'alice' });
  assert.deepEqual(JSON.parse(JSON.stringify(app.calls[0][1].results)), []);
  assert.equal(app.calls.filter(c => c[0] === 'dispatch').length, 0);
  console.log('TgCloud controlled handler checks passed: authorization, dispatch, callbacks, replay suppression and inline privacy.');
})().catch(error => { console.error(error); process.exitCode = 1; });
