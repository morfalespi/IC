import { diagnosticoErro } from '../lib/erros.js';
import { api } from 'sdk';
import { consultar } from '../lib/consulta.js';
import { responderInline } from '../lib/envio.js';
import { relatorioErro } from '../lib/relatorio.js';

export default async function (query) {
  const texto = (query.query || '').trim();
  let resposta;
  try {
    resposta = await consultar(texto, { canal: 'inline', chatId: query.from?.id });
  } catch (e) {
    console.error('falha ao montar a resposta inline:', diagnosticoErro(e));
    resposta = relatorioErro(e);
  }
  await responderInline(query.id, resposta.titulo, resposta.html, resposta.botaoPrivado);
}

