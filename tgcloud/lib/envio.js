import { api, BotApiError } from 'sdk';
import { diagnosticoErro } from './erros.js';

const TECLADO_REFERENCIA = {
  keyboard: [
    [{ text: 'Escolher usuário', request_users: { request_id: 1, max_quantity: 1, request_name: true, request_username: true, request_photo: true } }],
    [{ text: 'Escolher canal', request_chat: { request_id: 2, chat_is_channel: true, request_title: true, request_username: true, request_photo: true } }],
    [{ text: 'Escolher grupo', request_chat: { request_id: 3, chat_is_channel: false, request_title: true, request_username: true, request_photo: true } }],
  ],
  resize_keyboard: true,
  one_time_keyboard: true,
};

export function enviarMensagem(chatId, html, teclado = false) {
  return api.sendMessage({
    chat_id: chatId,
    text: html,
    parse_mode: 'HTML',
    ...(teclado ? { reply_markup: TECLADO_REFERENCIA } : {}),
  });
}

export function responderInline(queryId, titulo, html, botaoPrivado) {
  return api.answerInlineQuery({
    inline_query_id: queryId,
    results: [{ type: 'article', id: 'resultado', title: titulo, input_message_content: { message_text: html, parse_mode: 'HTML' } }],
    cache_time: 0,
    is_personal: true,
    ...(botaoPrivado ? { button: { text: 'Pesquisar no privado', start_parameter: botaoPrivado } } : {}),
  });
}

function plainCard(value) {
  return String(value)
    .replace(/<\\/(?:p|h[1-6]|tr|table|details)>/gi, '\\n')
    .replace(/<\\/?(?:td|th)[^>]*>/gi, ' ')
    .replace(/<[^>]*>/g, '')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'").replace(/&amp;/g, '&')
    .replace(/\\n{3,}/g, '\\n\\n').trim().slice(0, 3900);
}

// Só uma rejeição EXPLÍCITA do Telegram autoriza mudar o formato.
// Erros de rede/timeout/5xx são incertos: não reenviar e não duplicar.
function formatoRejeitado(erro) {
  if (!(erro instanceof BotApiError)) return false;
  return Number(erro.code ?? erro.error_code) === 400;
}

function fotoValida(id) {
  return typeof id === 'string' && id.length > 8 && id.length < 512;
}

async function enviarOuEditarRico(metodo, args, richHtml, fotoId) {
  // Usar a foto que o seletor do Telegram compartilhou, quando disponível.
  // A imagem é um bloco separado, dentro da MESMA Rich Message.
  if (fotoValida(fotoId)) {
    const htmlComFoto = richHtml.replace('</h2>', '</h2><img src="tg://photo?id=perfil"/>');
    if (htmlComFoto !== richHtml) {
      try {
        return await api[metodo]({
          ...args,
          rich_message: {
            html: htmlComFoto,
            media: [{ id: 'perfil', media: { type: 'photo', media: fotoId } }],
          },
        });
      } catch (erro) {
        if (!formatoRejeitado(erro)) throw erro;
      }
    }
  }
  try {
    return await api[metodo]({ ...args, rich_message: { html: richHtml } });
  } catch (erro) {
    if (!formatoRejeitado(erro)) throw erro;
    // Só após rejeição definitiva da API. Não reenvia após timeout ou erro 5xx.
    const texto = plainCard(richHtml);
    return metodo === 'sendRichMessage'
      ? api.sendMessage({ ...args, text: texto })
      : api.editMessageText({ ...args, text: texto });
  }
}

export function enviarCartao(chatId, richHtml, fotoId = null) {
  return enviarOuEditarRico('sendRichMessage', { chat_id: chatId }, richHtml, fotoId);
}

export function editarCartao(chatId, messageId, richHtml, fotoId = null) {
  return enviarOuEditarRico('editMessageText', { chat_id: chatId, message_id: messageId }, richHtml, fotoId);
}
