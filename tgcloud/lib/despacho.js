import { fetch } from 'sdk';
import { GH_DISPATCH_TOKEN, GH_REPOSITORY } from './segredos.js';

export async function dispararBusca(entrada, chatId, mensagemId, modo = "completo", origemId = "") {
  let resposta;
  for (let tentativa = 0; tentativa < 3; tentativa++) {
    try {
      resposta = await fetch(`https://api.github.com/repos/${GH_REPOSITORY}/actions/workflows/resolver.yml/dispatches`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${GH_DISPATCH_TOKEN}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2026-03-10',
          'User-Agent': 'infocard-bot',
        },
        body: fetch.body.json({ ref: 'main', inputs: {
          alvo: String(entrada.username ?? entrada.id ?? ''),
          expected_id: entrada.tipo === 'referencia' ? entrada.id : '',
          chat: String(chatId ?? ''), message_id: String(mensagemId ?? ''),
          modo, origem_id: String(origemId ?? ''),
        } }),
      });
      if (resposta.status >= 200 && resposta.status < 300) return resposta;
      console.error('GitHub dispatch:', resposta.status, await resposta.text());
    } catch (erro) {
      console.error('GitHub dispatch:', erro);
    }
  }
  return resposta;
}
