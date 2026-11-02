const NUMERICO = /^-?\d{1,16}$/;
const USERNAME = /^@?([A-Za-z0-9_]{1,32})$/;
const COM_REFERENCIA = /^(-?\d{1,16})\s+@?([A-Za-z0-9_]{1,32})$/;
const LIMITE_ID = 4503599627370495;

function validarId(texto) {
  if (!NUMERICO.test(texto)) return null;
  const numero = Number(texto);
  return Number.isSafeInteger(numero) && numero !== 0 && Math.abs(numero) <= LIMITE_ID ? texto : null;
}

export function lerEntrada(texto) {
  const valor = String(texto ?? '').trim();
  const comReferencia = COM_REFERENCIA.exec(valor);
  if (comReferencia) {
    const id = validarId(comReferencia[1]);
    if (!id) return { rotulo: valor, erro: 'ID fora do intervalo permitido pelo Telegram.' };
    return { tipo: 'referencia', id, username: comReferencia[2], alvo: id + '|' + comReferencia[2], rotulo: id + ' @' + comReferencia[2] };
  }
  const id = validarId(valor);
  if (id) return { tipo: 'id', id, alvo: id, rotulo: id };
  if (/^-?\d+$/.test(valor)) return { rotulo: valor, erro: 'ID inválido ou fora do intervalo permitido.' };
  const encontrado = USERNAME.exec(valor);
  if (encontrado) return { tipo: 'username', username: encontrado[1], alvo: encontrado[1], rotulo: '@' + encontrado[1] };
  return { rotulo: valor, erro: 'Envie @username, ID numérico ou ID @username como referência verificável.' };
}
