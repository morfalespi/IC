import { api } from 'sdk';
import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';

export default async function (callback) {
  const chat = callback.message?.chat;
  const messageId = callback.message?.message_id;
  const alvo = typeof callback.data === 'string' && callback.data.startsWith('r:')
    ? callback.data.slice(2)
    : '';
  if (chat?.type !== 'private' || Number(chat.id) !== Number(callback.from?.id) ||
      !Number.isSafeInteger(messageId) || !/^[A-Za-z0-9_|-]{1,55}$/.test(alvo)) {
    await api.answerCallbackQuery({ callback_query_id: callback.id, text: 'Ação indisponível.' });
    return;
  }
  await api.answerCallbackQuery({ callback_query_id: callback.id, text: 'Atualização solicitada.' });
  try {
    const resposta = await consultar(alvo, { canal: 'privado', chatId: chat.id, mensagemId: messageId });
    if (!resposta?.enviado) await enviarMensagem(chat.id, resposta.html, resposta.teclado);
  } catch (erro) {
    console.error('falha no callback do cartão:', erro);
    await enviarMensagem(chat.id, '<b>Atualização indisponível</b>\nTente novamente.');
  }
}
