import { api } from 'sdk';

const TECLADO = {
  keyboard: [[{ text: 'Escolher usuário', request_users: { request_id: 1, request_name: true, request_username: true, request_photo: true } }]],
  resize_keyboard: true,
  one_time_keyboard: true,
};

export function enviarMensagem(chatId, html, teclado = false) {
  const extra = teclado ? { reply_markup: TECLADO } : {};
  return api.sendMessage({ chat_id: chatId, text: html, parse_mode: 'HTML', ...extra });
}

export function responderInline(queryId, titulo, html, botaoPrivado) {
  return api.answerInlineQuery({
    inline_query_id: queryId,
    results: [{ type: 'article', id: 'resultado', title: titulo, input_message_content: { message_text: html, parse_mode: 'HTML' } }],
    cache_time: 0,
    is_personal: true,
    ...(botaoPrivado ? { button: { text: `Buscar @${botaoPrivado} no privado`, start_parameter: botaoPrivado } } : {}),
  });
}
