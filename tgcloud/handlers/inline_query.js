import { api } from 'sdk';
import { consultar } from '../lib/consulta.js';
import { responderInline } from '../lib/envio.js';
import { relatorioErro } from '../lib/relatorio.js';

export default async function (query) {
  const texto = (query.query || '').trim();
  if (!texto) {
    await api.answerInlineQuery({ inline_query_id: query.id, results: [], cache_time: 0, is_personal: true });
    return;
  }
  let resposta;
  try {
    resposta = await consultar(texto, { canal: 'inline' });
  } catch (e) {
    console.error('falha ao montar a resposta inline:', e);
    resposta = relatorioErro(e);
  }
  await responderInline(query.id, resposta.titulo, resposta.html, resposta.botaoPrivado);
}
