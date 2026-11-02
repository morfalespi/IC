import { api } from 'sdk';

export function enviarMensagem(chatId, html) {
  return api.sendMessage({
    chat_id: chatId,
    text: html,
    parse_mode: 'HTML',
    reply_markup: { remove_keyboard: true },
  });
}

export function responderInline(queryId, titulo, html, botaoPrivado) {
  return api.answerInlineQuery({
    inline_query_id: queryId,
    results: [{ type: 'article', id: 'resultado', title: titulo, input_message_content: { message_text: html, parse_mode: 'HTML' } }],
    cache_time: 0,
    is_personal: true,
    ...(botaoPrivado ? { button: { text: 'Pesquisar @' + botaoPrivado + ' no privado', start_parameter: botaoPrivado } } : {}),
  });
}
