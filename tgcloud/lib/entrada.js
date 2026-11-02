const ID = /^-?\d{1,16}$/;
const USERNAME = /^@?([A-Za-z0-9_]{1,32})$/;
const PAR = /^(-?\d{1,16})\s+@([A-Za-z0-9_]{1,32})$/;
const LIMITE_ID = 4503599627370495;

function idValido(valor) {
  if (!ID.test(valor)) return null;
  const n = Number(valor);
  return Number.isSafeInteger(n) && n !== 0 && Math.abs(n) <= LIMITE_ID ? String(n) : null;
}

function referencia(id, username) {
  return {
    tipo: 'referencia',
    id,
    username,
    rotulo: id + ' @' + username,
  };
}

function usuario(username) {
  return { tipo: 'username', username, rotulo: '@' + username };
}

function numerico(id) {
  return { tipo: 'id', id, rotulo: id };
}

export function lerEntrada(texto) {
  const valor = String(texto ?? '').trim();
  const par = PAR.exec(valor);
  if (par) {
    const id = idValido(par[1]);
    return id
      ? referencia(id, par[2])
      : { rotulo: valor, erro: 'ID fora do intervalo válido para identificação.' };
  }
  const id = idValido(valor);
  if (id) return numerico(id);
  if (ID.test(valor) || /^-?\d+$/.test(valor)) {
    return { rotulo: valor, erro: 'ID numérico inválido ou fora do intervalo permitido.' };
  }
  const username = USERNAME.exec(valor);
  if (username) return usuario(username[1]);
  return {
    rotulo: valor,
    erro: 'Envie @username, ID numérico ou ID @username. Exemplo: 8786464392 @myJAMrobot.',
  };
}

export function codigoCallback(acao, entrada) {
  if (acao !== 'r' && acao !== 'f') return null;
  let dados = '';
  if (entrada?.tipo === 'referencia' && idValido(String(entrada.id))) {
    if (!USERNAME.test(entrada.username) || entrada.username.startsWith('@')) return null;
    dados = acao + ':u:' + entrada.id + ':' + entrada.username;
  } else if (entrada?.tipo === 'username' && USERNAME.test(entrada.username) &&
             !entrada.username.startsWith('@')) {
    dados = acao + ':n:' + entrada.username;
  } else if (entrada?.tipo === 'id' && idValido(String(entrada.id))) {
    dados = acao + ':i:' + entrada.id;
  }
  return dados && dados.length <= 64 ? dados : null;
}

export function lerCallback(dados) {
  if (typeof dados !== 'string' || dados.length > 64) return null;
  const par = /^([rf]):u:(-?\d{1,16}):([A-Za-z0-9_]{1,32})$/.exec(dados);
  if (par) {
    const id = idValido(par[2]);
    return id ? { acao: par[1], entrada: referencia(id, par[3]) } : null;
  }
  const username = /^([rf]):n:([A-Za-z0-9_]{1,32})$/.exec(dados);
  if (username) return { acao: username[1], entrada: usuario(username[2]) };
  const id = /^([rf]):i:(-?\d{1,16})$/.exec(dados);
  if (id) {
    const idCanonico = idValido(id[2]);
    return idCanonico ? { acao: id[1], entrada: numerico(idCanonico) } : null;
  }
  return null;
}
