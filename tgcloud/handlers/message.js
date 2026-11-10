import { reservarAtualizacao } from '../lib/limite.js';
import { autorizado } from '../lib/autorizacao.js';
import { diagnosticoErro } from '../lib/erros.js';
import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';
import { relatorioErro, relatorioAjuda, relatorioInvalido } from '../lib/relatorio.js';

function esc(valor) {
  return String(valor).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function reduzir(valor, limite = 160) {
  return String(valor).slice(0, limite);
}

function referencia(objeto, origem, tipo = 'usuario') {
  const idBruto = tipo === 'chat' ? objeto?.chat_id ?? objeto?.id : objeto?.user_id ?? objeto?.id;
  const id = Number(idBruto);
  if (!Number.isSafeInteger(id) || id === 0) return null;
  const username = objeto?.username ?? null;
  const fotos = Array.isArray(objeto?.photo) ? objeto.photo : [];
  const maiorFoto = fotos.filter(p => typeof p?.file_id === 'string')
    .sort((a, b) => (b.width || 0) * (b.height || 0) - (a.width || 0) * (a.height || 0))[0];
  const nome = tipo === 'chat'
    ? objeto?.title
    : [objeto?.first_name, objeto?.last_name].filter(v => typeof v === 'string' && v.trim()).join(' ');
  return {
    entrada: String(id) + (username ? ' @' + username : ''),
    id: String(id),
    username,
    nome: nome ? reduzir(nome) : null,
    origem,
    fotoInformada: fotos.length > 0,
    fotoId: maiorFoto?.file_id ?? null,
  };
}

function referenciaCompartilhada(message) {
  if (message.users_shared) {
    return referencia(message.users_shared.users?.[0], 'Seleção de usuário no Telegram');
  }
  if (message.chat_shared) {
    const especie = message.chat_shared.request_id === 2 ? 'canal' : message.chat_shared.request_id === 3 ? 'grupo' : 'chat';
    return referencia(message.chat_shared, 'Seleção de ' + especie + ' no Telegram', 'chat');
  }
  if (message.forward_origin) {
    const origem = message.forward_origin;
    if (origem.type === 'user') return referencia(origem.sender_user, 'Mensagem encaminhada com remetente identificado');
    if (origem.type === 'chat') return referencia(origem.sender_chat, 'Mensagem encaminhada de chat', 'chat');
    if (origem.type === 'channel') return referencia(origem.chat, 'Mensagem encaminhada de canal', 'chat');
    return null;
  }
  if (message.contact) {
    return referencia(message.contact, 'Contato compartilhado');
  }
  const mencao = [...(message.entities || []), ...(message.caption_entities || [])]
    .find(item => item.type === 'text_mention' && item.user);
  return mencao ? referencia(mencao.user, 'Menção oficial a usuário') : undefined;
}

function adicionarDadosCompartilhados(resposta, dados) {
  const linhas = [
    '<b>Informações fornecidas pelo Telegram</b>',
    'Origem: ' + esc(dados.origem),
    'ID: <code>' + esc(dados.id) + '</code>',
  ];
  if (dados.nome) linhas.push('Nome ou título: ' + esc(dados.nome));
  if (dados.username) linhas.push('Username informado: @' + esc(dados.username));
  if (dados.fotoInformada) linhas.push('Foto: o Telegram forneceu uma referência de foto.');
  linhas.push('Esses dados vieram do compartilhamento, não de uma consulta MTProto. Podem mudar depois do compartilhamento.');
  linhas.push('', resposta.html);
  return { ...resposta, html: linhas.join('\n') };
}

export default async function (message, ctx) {
  if (!autorizado(message.from?.id, message.chat?.id, message.chat?.type, message.from?.is_bot)) return;
  if (!await reservarAtualizacao(ctx?.update?.update_id)) return;
  let resposta;
  try {
    const compartilhamento = referenciaCompartilhada(message);
    if (compartilhamento === null) {
      resposta = relatorioInvalido({
        rotulo: '',
        erro: 'O Telegram não forneceu um ID acessível nessa referência. Compartilhe um usuário ou chat com remetente identificado.',
      });
    } else if (compartilhamento) {
      const consulta = await consultar(compartilhamento.entrada, { canal: 'privado', userId: message.from?.id, chatId: message.chat.id, chatType: message.chat?.type, isBot: message.from?.is_bot, dadosCompartilhados: compartilhamento });
      resposta = consulta.enviado ? consulta : adicionarDadosCompartilhados(consulta, compartilhamento);
    } else {
      const texto = message.text || '';
      const inicio = /^\/start(?:@\w+)?(?:\s+(\S+))?\s*$/.exec(texto);
      const ajuda = /^\/help(?:@\w+)?\s*$/.test(texto);
      const comando = /^\/(info|export)(?:@\w+)?\s+(.+)$/i.exec(texto);
      const entrada = comando ? comando[2] : (inicio?.[1] ?? texto);
      const modo = comando?.[1]?.toLowerCase() === 'export' ? 'completo' : 'resumo';
      resposta = ((inicio && !inicio[1]) || ajuda)
        ? relatorioAjuda()
        : await consultar(entrada, { canal: 'privado', userId: message.from?.id, chatId: message.chat.id, chatType: message.chat?.type, isBot: message.from?.is_bot, modo });
    }
  } catch (erro) {
    console.error('falha ao montar a resposta:', diagnosticoErro(erro));
    resposta = relatorioErro(erro);
  }
  if (!resposta?.enviado) await enviarMensagem(message.chat.id, resposta.html, resposta.teclado);
}

