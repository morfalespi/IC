const ID_NUMERICO = /^-?\d{1,16}$/;
const USERNAME = /^@?([A-Za-z0-9_]{1,32})$/;

export function lerEntrada(texto) {
  const t = String(texto ?? '').trim();
  if (ID_NUMERICO.test(t)) {
    const n = Number(t);
    if (!Number.isSafeInteger(n)) return { erro: 'id fora do intervalo seguro' };
    return { tipo: 'id', chat_id: n, rotulo: t };
  }
  const m = USERNAME.exec(t);
  if (m) return { tipo: 'username', chat_id: `@${m[1]}`, rotulo: `@${m[1]}` };
  return { erro: 'entrada não reconhecida' };
}
