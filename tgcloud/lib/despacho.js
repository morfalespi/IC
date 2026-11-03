import { fetch } from 'sdk';
import { GH_DISPATCH_TOKEN, GH_REPOSITORY } from './segredos.js';

const EXPLICACOES = {
  401: 'O token do GitHub é inválido ou expirou. Gere outro e atualize o secret GH_DISPATCH_TOKEN.',
  403: 'O token do GitHub não tem permissão para disparar workflows. Ele precisa de "Actions: Read and write" neste repositório.',
  404: 'O token do GitHub não enxerga este repositório ou o workflow resolver.yml.',
  422: 'O GitHub rejeitou as entradas do workflow resolver.yml.',
};

const REPOSITORIO_VALIDO = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

function urlDisparo() {
  if (!REPOSITORIO_VALIDO.test(GH_REPOSITORY)) {
    const erro = new Error('GH_REPOSITORY não foi injetado no deploy');
    erro.status = 0;
    throw erro;
  }
  return `https://api.github.com/repos/${GH_REPOSITORY}/actions/workflows/resolver.yml/dispatches`;
}

export async function dispararBusca(entrada, chatId, mensagemId, modo = "completo", origemId = "") {
  if (!GH_DISPATCH_TOKEN) {
    const erro = new Error('GH_DISPATCH_TOKEN não foi injetado no deploy');
    erro.status = 0;
    throw erro;
  }
  const res = await fetch(urlDisparo(), {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GH_DISPATCH_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2026-03-10',
      'User-Agent': 'infocard-bot',
    },
      body: fetch.body.json({ ref: 'main', inputs: { alvo: String(entrada.username || entrada.id), expected_id: entrada.tipo === "referencia" ? entrada.id : "", chat: String(chatId), message_id: String(mensagemId || ""), modo: modo === "resumo" ? "resumo" : "completo", origem_id: String(origemId || "") } }),
  });
  if (res.status !== 200 && res.status !== 204) {
    const corpo = await res.text();
    const erro = new Error(`${EXPLICACOES[res.status] ?? 'O GitHub recusou o disparo.'} (GitHub respondeu ${res.status}: ${corpo.slice(0, 200)})`);
    erro.status = res.status;
    throw erro;
  }
}
