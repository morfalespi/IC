import { lerEntrada } from './entrada.js';
import { dispararBusca } from './despacho.js';
import { reservarDisparo, liberarDisparo } from './limite.js';
import { relatorioInvalido, relatorioFalha, relatorioBuscando, relatorioInline } from './relatorio.js';
import { enviarCartao, editarCartao } from './envio.js';
import { cartaoPesquisa, cartaoErro } from './cartao.js';

export async function consultar(texto, contexto) {
  const entrada = lerEntrada(texto);
  if (entrada.erro) return relatorioInvalido(entrada);
  if (contexto.canal !== 'privado') return relatorioInline(entrada);

  let reserva;
  try {
    reserva = await reservarDisparo(contexto.chatId);
  } catch (erroLimite) {
    console.error('controle de limite indisponível:', erroLimite);
    return relatorioFalha(entrada, 'O controle de limite das buscas está indisponível. Tente novamente em instantes.');
  }
  if (!reserva.permitido) return relatorioFalha(entrada, reserva.motivo);

  let mensagemId = contexto.mensagemId ?? null;
  try {
    const pendente = relatorioBuscando(entrada);
    if (mensagemId) {
      await editarCartao(contexto.chatId, mensagemId, cartaoPesquisa(entrada, contexto.dadosCompartilhados), pendente.html);
    } else {
      const mensagem = await enviarCartao(contexto.chatId, cartaoPesquisa(entrada, contexto.dadosCompartilhados), pendente.html);
      mensagemId = mensagem?.message_id;
      if (!Number.isSafeInteger(mensagemId)) throw new Error('O Telegram não retornou message_id para acompanhar a consulta.');
    }
    await dispararBusca(entrada.alvo, contexto.chatId, mensagemId);
    return { enviado: true, mensagemId };
  } catch (erroDespacho) {
    console.error('pesquisa ou despacho falhou:', erroDespacho);
    await liberarDisparo(reserva.id).catch(erro => console.error('falha ao liberar reserva:', erro));
    if (mensagemId) {
      try {
        await editarCartao(
          contexto.chatId,
          mensagemId,
          cartaoErro(entrada, erroDespacho.message),
          relatorioFalha(entrada, erroDespacho.message).html
        );
        return { enviado: true, mensagemId };
      } catch (erroEdicao) {
        console.error('falha ao editar erro da ficha:', erroEdicao);
      }
    }
    return relatorioFalha(entrada, 'Não foi possível iniciar a busca MTProto: ' + erroDespacho.message);
  }
}
