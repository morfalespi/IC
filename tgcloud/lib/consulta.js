import { lerEntrada } from './entrada.js';
import { dispararBusca } from './despacho.js';
import { reservarDisparo, liberarDisparo } from './limite.js';
import { relatorioInvalido, relatorioFalha, relatorioInline } from './relatorio.js';
import { enviarCartao, editarCartao } from './envio.js';
import { cartaoPesquisa, cartaoErro } from './cartao.js';
import { diagnosticoErro, mensagemErro, FalhaEntrega } from './erros.js';

export async function consultar(texto, contexto) {
  const entrada = typeof texto === 'string' ? lerEntrada(texto) : texto;
  if (entrada.erro) return relatorioInvalido(entrada);
  if (contexto.canal !== 'privado') return relatorioInline(entrada);
  const modo = contexto.modo === 'resumo' ? 'resumo' : 'completo';

  let reserva;
  try {
    reserva = await reservarDisparo(contexto.chatId);
  } catch (erroLimite) {
    console.error('controle de limite indisponível:', diagnosticoErro(erroLimite));
    return relatorioFalha(entrada, 'O controle de limite das buscas está indisponível. Tente novamente em instantes.');
  }
  if (!reserva.permitido) return relatorioFalha(entrada, reserva.motivo);

  let mensagemId = contexto.mensagemId ?? null;
  try {
    if (mensagemId) {
      await editarCartao(contexto.chatId, mensagemId, cartaoPesquisa(entrada, contexto.dadosCompartilhados, modo));
    } else {
      const mensagem = await enviarCartao(contexto.chatId, cartaoPesquisa(entrada, contexto.dadosCompartilhados, modo));
      mensagemId = mensagem?.message_id;
    }
    await dispararBusca(entrada, contexto.chatId, mensagemId, modo, contexto.origemMensagemId);
    return { enviado: true, mensagemId };
  } catch (erroDespacho) {
    console.error('pesquisa ou despacho falhou:', diagnosticoErro(erroDespacho));
    const motivo = mensagemErro(erroDespacho);
    await liberarDisparo(reserva.id).catch(erro => console.error('falha ao liberar reserva:', diagnosticoErro(erro)));
    if (erroDespacho instanceof FalhaEntrega) throw erroDespacho;
    if (mensagemId) {
      try {
        await editarCartao(
          contexto.chatId,
          mensagemId,
          cartaoErro(entrada, motivo)
        );
      } catch (erroEdicao) {
        console.error('falha ao editar erro da ficha:', diagnosticoErro(erroEdicao));
        throw erroEdicao;
      }
    }
    throw new FalhaEntrega(erroDespacho, 'dispatch_unconfirmed');
  }
}
