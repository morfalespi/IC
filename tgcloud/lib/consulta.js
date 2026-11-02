import { api, BotApiError } from 'sdk';
import { lerEntrada } from './entrada.js';
import { dispararBusca } from './despacho.js';
import { comRetentativa } from './tentativa.js';
import { reservarDisparo, liberarDisparo } from './limite.js';
import { relatorioLeitura, relatorioFalha, relatorioInvalido, relatorioBuscando } from './relatorio.js';

const transitorioApi = (e) => !(e instanceof BotApiError) || e.code >= 500;

function falhaDaApi(e) {
  if (e instanceof BotApiError) {
    return { apiErro: true, code: e.code, description: e.description, parameters: e.parameters };
  }
  return { apiErro: false, name: e.name, message: e.message };
}

export async function consultar(texto, contexto) {
  const entrada = lerEntrada(texto);
  if (entrada.erro) return relatorioInvalido(texto);
  try {
    return relatorioLeitura(await comRetentativa(() => api.getChat({ chat_id: entrada.chat_id }), transitorioApi));
  } catch (e) {
    console.error('getChat falhou:', entrada.rotulo, e);
    const falha = falhaDaApi(e);
    const naoResolvido = falha.apiErro && falha.code === 400 && /chat not found/i.test(falha.description || '');
    if (!naoResolvido) return relatorioFalha(entrada, falha);
    if (entrada.tipo === 'id') {
      const orientacao = contexto.canal === 'privado'
        ? 'O Bot API não conhece esse ID. Para obter dados de um usuário, use o botão abaixo, encaminhe uma mensagem da pessoa ou envie o @username.'
        : 'O Bot API não conhece esse ID. Abra uma conversa privada com o bot: lá é possível escolher o usuário, encaminhar uma mensagem da pessoa ou enviar o @username.';
      return relatorioFalha(entrada, falha, [orientacao]);
    }
    if (contexto.canal !== 'privado') {
      return { ...relatorioFalha(entrada, falha, ['A busca por MTProto só roda no privado. Toque no botão acima para continuar lá.']), botaoPrivado: entrada.chat_id.slice(1) };
    }
    let reserva;
    try {
      reserva = await reservarDisparo(contexto.chatId);
    } catch (erroLimite) {
      console.error('controle de limite indisponível:', erroLimite);
      return relatorioFalha(entrada, falha, ['O controle de limite das buscas por MTProto está indisponível agora. Tente de novo em instantes.']);
    }
    if (!reserva.permitido) return relatorioFalha(entrada, falha, [reserva.motivo]);
    try {
      await dispararBusca(entrada.chat_id.slice(1), contexto.chatId);
      return relatorioBuscando(entrada);
    } catch (erroDespacho) {
      console.error('dispararBusca falhou:', erroDespacho);
      await liberarDisparo(reserva.id).catch((erroLiberar) => console.error('não consegui liberar a reserva:', erroLiberar));
      return relatorioFalha(entrada, falha, [`Não consegui iniciar a busca por MTProto: ${erroDespacho.name}: ${erroDespacho.message}`]);
    }
  }
}
