import { lerEntrada } from './entrada.js';
import { dispararBusca } from './despacho.js';
import { reservarDisparo, liberarDisparo } from './limite.js';
import { relatorioInvalido, relatorioFalha, relatorioBuscando, relatorioInline } from './relatorio.js';

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

  try {
    await dispararBusca(entrada.username, contexto.chatId);
    return relatorioBuscando(entrada);
  } catch (erroDespacho) {
    console.error('dispararBusca falhou:', erroDespacho);
    await liberarDisparo(reserva.id).catch((erroLiberar) => console.error('não consegui liberar a reserva:', erroLiberar));
    return relatorioFalha(entrada, 'Não foi possível iniciar a busca MTProto: ' + erroDespacho.name + ': ' + erroDespacho.message);
  }
}
