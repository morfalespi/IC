function validarId(value) {
  if (!/^-?[1-9]\d{0,15}$/.test(value) || !Number.isSafeInteger(Number(value))) throw new Error('ID canônico inválido.');
  return value;
}
function validarUsername(value) {
  if (!/^[A-Za-z][A-Za-z0-9_]{3,31}$/.test(value)) throw new Error('Username inválido.');
  return value;
}
function referencia(id, username) {
  return { tipo: 'referencia', id: validarId(id), username: validarUsername(username), rotulo: id + ' @' + username };
}
function usuario(username) {
  return { tipo: 'username', username: validarUsername(username), rotulo: '@' + username };
}
function numerico(id) {
  return { tipo: 'id', id: validarId(id), rotulo: id };
}
export function lerEntrada(texto) {
  const valor = String(texto ?? '').trim();
  const par = /^(-?[1-9]\d{0,15})\s+@([A-Za-z][A-Za-z0-9_]{3,31})$/.exec(valor);
  if (par) return referencia(par[1], par[2]);
  if (/^-?\d+$/.test(valor)) return numerico(valor);
  return usuario(valor.replace(/^@/, ''));
}
export function codigoCallback(acao, entrada) {
  if (!['r', 'f'].includes(acao)) throw new Error('Ação inválida.');
  const value = entrada?.tipo === 'referencia' ? `${acao}:u:${entrada.id}:${entrada.username}` : entrada?.tipo === 'id' ? `${acao}:i:${entrada.id}` : `${acao}:n:${entrada.username}`;
  // All permitted characters are ASCII, so length equals UTF-8 bytes.
  if (value.length > 64) throw new Error('Callback excede 64 bytes.');
  return value;
}
export function lerCallback(dados) {
  const match = /^([rf]):([uin]):(.*)$/.exec(String(dados ?? ''));
  if (!match || String(dados).length > 64) throw new Error('Callback inválido.');
  const [, acao, tipo, value] = match;
  if (tipo === 'u') {
    const parts = value.split(':');
    if (parts.length !== 2) throw new Error('Referência inválida.');
    return { acao, entrada: referencia(...parts) };
  }
  return { acao, entrada: tipo === 'i' ? numerico(value) : usuario(value) };
}
