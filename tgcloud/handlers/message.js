import { consultar } from '../lib/consulta.js';
import { enviarMensagem } from '../lib/envio.js';
import { relatorioErro, relatorioAjuda } from '../lib/relatorio.js';

export default async function (message) {
  if (message.chat.type !== 'private') return;

  let resposta;
  try {
    const texto = message.text || '';
    const inicio = /^\/start(?:@\w+)?(?:\s+(\S+))?\s*$/.exec(texto);
    const ajuda = /^\/help(?:@\w+)?\s*$/.test(texto);
    if ((inicio && !inicio[1]) || ajuda) {
      resposta = relatorioAjuda();
    } else {
      resposta = await consultar(inicio?.[1] ?? texto, { canal: 'privado', chatId: message.chat.id });
    }
  } catch (erro) {
    console.error('falha ao montar a resposta:', erro);
    resposta = relatorioErro(erro);
  }
  await enviarMensagem(message.chat.id, resposta.html);
}
