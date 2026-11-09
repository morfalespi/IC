import { reservarDisparo } from './limite.js';
import { autorizado } from './autorizacao.js';
import { lerEntrada } from './entrada.js';
import { dispararBusca } from './despacho.js';
import { relatorioBuscando } from './relatorio.js';
import { enviarCartao, editarCartao } from './envio.js';
import { cartaoPesquisa } from './cartao.js';
import { diagnosticoErro } from './erros.js';

export async function consultar(texto, contexto) {
  if (!autorizado(contexto.userId, contexto.chatId)) throw new Error('Operação não autorizada.');
  const entrada = typeof texto === 'string' ? lerEntrada(texto) : texto;
  if (!(await reservarDisparo(contexto.chatId)).permitido) throw new Error('Aguarde 30 segundos antes de outra consulta.');
  const modo = contexto.modo === 'resumo' ? 'resumo' : 'completo';
  let mensagemId = contexto.mensagemId ?? null;
  try {
    if (mensagemId) {
      await editarCartao(contexto.chatId, mensagemId, cartaoPesquisa(entrada, contexto.dadosCompartilhados, modo));
    } else {
      const mensagem = await enviarCartao(contexto.chatId, cartaoPesquisa(entrada, contexto.dadosCompartilhados, modo));
      mensagemId = mensagem?.message_id;
    }
  } catch (erro) {
    console.error('cartão inicial:', diagnosticoErro(erro));
  }
  try {
    await dispararBusca(entrada, contexto.chatId, mensagemId, modo, contexto.origemMensagemId);
  } catch (erro) {
    console.error('despacho:', diagnosticoErro(erro));
    throw erro;
  }
  return { ...relatorioBuscando(entrada), enviado: true, mensagemId };
}
