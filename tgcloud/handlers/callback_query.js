import { diagnosticoErro } from '../lib/erros.js';
import { api } from 'sdk';
import { lerCallback } from '../lib/entrada.js';
import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';

export default async function (callback) {
  const chat = callback.message?.chat;
  const messageId = callback.message?.message_id;
  const pedido = lerCallback(callback.data);
  if (chat?.type !== 'private' || Number(chat.id) !== Number(callback.from?.id) ||
      !Number.isSafeInteger(messageId) || !pedido) {
    await api.answerCallbackQuery({
      callback_query_id: callback.id,
      text: 'Referência inválida ou botão antigo. Envie uma nova pesquisa.',
      show_alert: true,
    });
    return;
  }
  const completo = pedido.acao === 'f';
  await api.answerCallbackQuery({
    callback_query_id: callback.id,
    text: completo ? 'Preparando exportação completa…' : 'Atualização solicitada.',
  });
  try {
    const contexto = completo
      ? { canal: 'privado', chatId: chat.id, modo: 'completo', origemMensagemId: messageId }
      : { canal: 'privado', chatId: chat.id, mensagemId: messageId };
    const resposta = await consultar(pedido.entrada, contexto);
    if (!resposta?.enviado) await enviarMensagem(chat.id, resposta.html, resposta.teclado);
  } catch (erro) {
    console.error('falha ao processar callback:', diagnosticoErro(erro));
    await enviarMensagem(chat.id, '<b>Não foi possível processar a ação.</b>\nEnvie uma nova pesquisa.');
  }
}
