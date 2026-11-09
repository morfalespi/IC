import { fetch } from 'sdk';
import { encryptPayload } from './payload.js';
import { GH_DISPATCH_TOKEN, GH_REPOSITORY, IC_DISPATCH_PUBLIC_KEY } from './segredos.js';

export async function dispararBusca(entrada, chatId, mensagemId, modo = 'completo', origemId = '') {
  if (!GH_DISPATCH_TOKEN || !/^[\w.-]+\/[\w.-]+$/.test(GH_REPOSITORY)) throw new Error('Configuração de dispatch ausente.');
  const payload = await encryptPayload({ alvo: String(entrada.username ?? entrada.id ?? ''), expected_id: entrada.tipo === 'referencia' ? entrada.id : '', chat: String(chatId), message_id: String(mensagemId ?? ''), modo, origem_id: String(origemId ?? '') }, IC_DISPATCH_PUBLIC_KEY);
  // GitHub dispatch has no idempotency key. An uncertain POST must not be retried automatically.
  const resposta = await fetch(`https://api.github.com/repos/${GH_REPOSITORY}/actions/workflows/resolver.yml/dispatches`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'infocard-bot' },
    body: fetch.body.json({ ref: 'main', inputs: { payload } }),
  });
  if (resposta.status !== 204) {
    const erro = new Error('O GitHub não aceitou a execução.');
    erro.origin = 'github'; erro.status = resposta.status; erro.publicMessage = erro.message;
    throw erro;
  }
  return resposta;
}
