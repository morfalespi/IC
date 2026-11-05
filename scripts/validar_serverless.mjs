import fs from 'node:fs';
import path from 'node:path';
import { scanFiles } from '../node_modules/@tgcloud/cli/src/core/scanner.js';
import { pathToModule } from '../node_modules/@tgcloud/cli/src/core/snapshot.js';
import { resolveToken } from '../node_modules/@tgcloud/cli/src/core/credentials.js';
import { runFunction } from '../node_modules/@tgcloud/cli/src/api/endpoints.js';

const fonte = `
import { api, db, fetch, BotApiError } from 'sdk';
import { disparos } from '../schema.js';
import { diagnosticoErro } from '../lib/erros.js';
import '../handlers/message.js';
import '../handlers/callback_query.js';
import '../handlers/inline_query.js';

export default async function (esperado) {
  const bot = await api.getMe();
  if (bot?.is_bot !== true || bot.id !== esperado.bot_id) {
    throw new Error('SDK Serverless não confirmou o mesmo bot da Bot API HTTP.');
  }
  const chat = await api.getChat({ chat_id: esperado.chat_id });
  if (chat?.id !== esperado.chat_id || chat.type !== 'channel') {
    throw new Error('SDK Serverless não confirmou o mesmo canal.');
  }
  const linhas = await db.select({ id: disparos.id, chatId: disparos.chatId, em: disparos.em })
    .from(disparos).limit(1).all();
  if (!Array.isArray(linhas) || linhas.length > 1) throw new Error('Consulta do schema não retornou linhas válidas.');
  let recusa = false;
  try {
    await api.getChat({ chat_id: 0 });
  } catch (erro) {
    const diagnostico = diagnosticoErro(erro);
    if (!(erro instanceof BotApiError) || erro.code !== 400 || diagnostico.origin !== 'telegram' ||
        diagnostico.error_code !== 400 || typeof diagnostico.description !== 'string') throw erro;
    recusa = true;
  }
  if (!recusa) throw new Error('getChat com ID zero não confirmou a recusa esperada.');
  const resposta = await fetch('https://api.github.com/repos/' + esperado.repository + '/actions/workflows/resolver.yml', {
    headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'infocard-validation' },
  });
  if (resposta.status !== 200) throw new Error('Leitura GitHub recusada pelo HTTP do SDK: ' + resposta.status);
  const workflow = await resposta.json();
  if (workflow?.state !== 'active' || workflow?.path !== '.github/workflows/resolver.yml') {
    throw new Error('GitHub não confirmou o workflow ativo.');
  }
  return { bot: true, channel: true, schema: true, github: true, modules: true, rejection: recusa };
}
`;

try {
  if (!process.env.RUNNER_TEMP || !process.env.TGCLOUD_TOKEN) {
    throw new Error('RUNNER_TEMP e TGCLOUD_TOKEN são obrigatórios.');
  }
  const esperado = JSON.parse(fs.readFileSync(path.join(process.env.RUNNER_TEMP, 'telegram_validation.json'), 'utf8'));
  esperado.repository = process.env.GITHUB_REPOSITORY;
  if (!Number.isSafeInteger(esperado.bot_id) || !Number.isSafeInteger(esperado.chat_id) ||
      !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(esperado.repository)) {
    throw new Error('Evidência anterior ou repositório inválidos.');
  }
  const fontes = Object.fromEntries(scanFiles().map(arquivo => [pathToModule(arquivo), fs.readFileSync(arquivo, 'utf8')]));
  fontes['endpoints/validar_integracoes'] = fonte;
  const resposta = await runFunction(await resolveToken(), 'endpoints/validar_integracoes', fontes, esperado, {});
  if (!['bot', 'channel', 'schema', 'github', 'modules', 'rejection'].every(chave => resposta?.result?.[chave] === true)) {
    throw new Error('O runtime não confirmou todas as leituras.');
  }
  console.log('Serverless real: módulos carregados, mesmo bot/canal, schema legível, erro 400 diagnosticado e workflow GitHub ativo; sem escrita, deploy ou envio.');
} catch (erro) {
  const segredos = ['BOT_TOKEN', 'API_HASH', 'TGCLOUD_TOKEN', 'GH_DISPATCH_TOKEN']
    .map(nome => process.env[nome]).filter(Boolean);
  let descricao = String(erro?.description ?? erro?.message ?? erro?.name ?? 'Erro');
  for (const segredo of segredos) descricao = descricao.split(segredo).join('[redigido]');
  descricao = descricao.replace(/(?:app|bot)?\d+:[A-Za-z0-9_-]+/g, '[redigido]')
    .replace(/(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)/g, '[redigido]');
  console.error(JSON.stringify({ origin: 'serverless_validation', type: erro?.name, status: erro?.status, description: descricao }));
  process.exitCode = 1;
}
