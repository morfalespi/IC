import { api } from 'sdk';
import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';

export default async function (callback) {
  const chat = callback.message?.chat;
  const messageId = callback.message?.message_id;
  const data = typeof callback.data === 'string' ? callback.data : '';
  const comando = data.slice(0, 2);
  const alvo = data.slice(2);
  if (chat?.type !== 'private' || Number(chat.id) !== Number(callback.from?.id) ||
      !Number.isSafeInteger(messageId) || !['r:', 'f:'].includes(comando) ||
      !/^[A-Za-z0-9_|-]{1,55}$/.test(alvo)) {
    await api.answerCallbackQuery({ callback_query_id: callback.id, text: 'Ação indisponível.' });
    return;
  }
  const completo = comando === 'f:';
  await api.answerCallbackQuery({
    callback_query_id: callback.id,
    text: completo ? 'Preparando relatório completo e arquivo Markdown…' : 'Atualização solicitada.',
  });
  try {
    const contexto = completo
      ? { canal: 'privado', chatId: chat.id, modo: 'completo', origemMensagemId: messageId }
      : { canal: 'privado', chatId: chat.id, mensagemId: messageId };
    const resposta = await consultar(alvo, contexto);
    if (!resposta?.enviado) await enviarMensagem(chat.id, resposta.html, resposta.teclado);
  } catch (erro) {
    console.error('falha no callback do cartão:', erro);
    await enviarMensagem(chat.id, '<b>Não foi possível processar a solicitação</b>\nTente novamente.');
  }
}
