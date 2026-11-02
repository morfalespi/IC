const ID_NUMERICO = /^-?\d+$/;
const USERNAME = /^@?([A-Za-z][A-Za-z0-9_]{0,31})$/;

export function lerEntrada(texto) {
  const valor = String(texto ?? '').trim();
  if (ID_NUMERICO.test(valor)) {
    return { tipo: 'id', rotulo: valor, erro: 'Um ID isolado não pode ser pesquisado de forma confiável por MTProto sem o access_hash. Envie um @username público.' };
  }
  const encontrado = USERNAME.exec(valor);
  if (!encontrado) {
    return { tipo: 'invalido', rotulo: valor, erro: 'Envie um @username público (letras, números e _, começando por letra).' };
  }
  return { tipo: 'username', username: encontrado[1], rotulo: '@' + encontrado[1] };
}
