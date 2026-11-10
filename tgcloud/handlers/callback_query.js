import { reservarAtualizacao } from '../lib/limite.js';
import { autorizado } from '../lib/autorizacao.js';
import { diagnosticoErro } from '../lib/erros.js';
import { api } from 'sdk';
import { lerCallback } from '../lib/entrada.js';
import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';

export default async function (callback, ctx) {
  const chat = callback.message?.chat ?? callback.from;
  if (!autorizado(callback.from?.id, chat?.id, chat?.type, callback.from?.is_bot)) {
    await api.answerCallbackQuery({ callback_query_id: callback.id, text: 'Operação não autorizada.' });
    return;
  }
  if (!await reservarAtualizacao(ctx?.update?.update_id)) return;
  const messageId = callback.message?.message_id;
  const pedido = lerCallback(callback.data);
  const completo = pedido.acao === 'f';
  await api.answerCallbackQuery({
    callback_query_id: callback.id,
    text: completo ? 'Preparando exportação completa…' : 'Atualização solicitada.',
  });
  try {
    const contexto = completo
      ? { canal: 'privado', userId: callback.from?.id, chatId: chat.id, chatType: chat?.type, isBot: callback.from?.is_bot, modo: 'completo', origemMensagemId: messageId }
      : { canal: 'privado', userId: callback.from?.id, chatId: chat.id, chatType: chat?.type, isBot: callback.from?.is_bot, mensagemId: messageId };
    const resposta = await consultar(pedido.entrada, contexto);
    if (!resposta?.enviado) await enviarMensagem(chat.id, resposta.html, resposta.teclado);
  } catch (erro) {
    console.error('falha ao processar callback:', diagnosticoErro(erro));
    await enviarMensagem(chat.id, '<b>Falha no processamento.</b>');
  }
}

