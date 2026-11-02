import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';
import { relatorioErro, relatorioAjuda, relatorioInvalido } from '../lib/relatorio.js';

function referenciaPorUsuario(usuario) {
  const id = usuario?.user_id ?? usuario?.id;
  if (!Number.isSafeInteger(Number(id)) || Number(id) <= 0) return null;
  return String(id) + (usuario.username ? ' @' + usuario.username : '');
}

function entradaDeMensagem(message) {
  if (message.users_shared) {
    const escolhido = message.users_shared.users?.[0];
    return referenciaPorUsuario(escolhido);
  }
  if (message.forward_origin) {
    const origem = message.forward_origin;
    if (origem.type === 'user') return referenciaPorUsuario(origem.sender_user);
    if (origem.type === 'channel' || origem.type === 'chat') {
      const chat = origem.chat ?? origem.sender_chat;
      if (chat?.id) return String(chat.id) + (chat.username ? ' @' + chat.username : '');
    }
    return null;
  }
  if (message.contact) return referenciaPorUsuario(message.contact);
  const mencao = [...(message.entities || []), ...(message.caption_entities || [])]
    .find(item => item.type === 'text_mention' && item.user);
  return mencao ? referenciaPorUsuario(mencao.user) : undefined;
}

export default async function (message) {
  if (message.chat.type !== 'private') return;

  let resposta;
  try {
    const referencia = entradaDeMensagem(message);
    if (referencia === null) {
      resposta = relatorioInvalido({ rotulo: '', erro: 'A referência compartilhada não inclui um ID identificável. Se houver @username público, envie-o diretamente.' });
    } else if (referencia) {
      resposta = await consultar(referencia, { canal: 'privado', chatId: message.chat.id });
    } else {
      const texto = message.text || '';
      const inicio = /^\/start(?:@\w+)?(?:\s+(\S+))?\s*$/.exec(texto);
      const ajuda = /^\/help(?:@\w+)?\s*$/.test(texto);
      if ((inicio && !inicio[1]) || ajuda) {
        resposta = relatorioAjuda();
      } else {
        resposta = await consultar(inicio?.[1] ?? texto, { canal: 'privado', chatId: message.chat.id });
      }
    }
  } catch (erro) {
    console.error('falha ao montar a resposta:', erro);
    resposta = relatorioErro(erro);
  }
  await enviarMensagem(message.chat.id, resposta.html, resposta.teclado);
}
