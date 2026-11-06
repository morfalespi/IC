function referencia(id, username) {
  return { tipo: 'referencia', id, username, rotulo: id + ' @' + username };
}

function usuario(username) {
  return { tipo: 'username', username, rotulo: '@' + username };
}

function numerico(id) {
  return { tipo: 'id', id, rotulo: id };
}

export function lerEntrada(texto) {
  const valor = String(texto ?? '').trim();
  const par = /^(\S+)\s+@(.*)$/.exec(valor);
  if (par) return referencia(par[1], par[2]);
  if (/^[+-]?\d+$/.test(valor)) return numerico(valor);
  return usuario(valor.replace(/^@/, ''));
}

export function codigoCallback(acao, entrada) {
  if (entrada?.tipo === 'referencia') return acao + ':u:' + entrada.id + ':' + entrada.username;
  if (entrada?.tipo === 'id') return acao + ':i:' + entrada.id;
  return acao + ':n:' + String(entrada?.username ?? '');
}

export function lerCallback(dados) {
  const [acao = 'r', tipo, ...partes] = String(dados ?? '').split(':');
  if (tipo === 'u') return { acao, entrada: referencia(partes.shift() ?? '', partes.join(':')) };
  if (tipo === 'i') return { acao, entrada: numerico(partes.join(':')) };
  return { acao, entrada: usuario(tipo === 'n' ? partes.join(':') : String(dados ?? '')) };
}
