function esc(valor) {
  return String(valor).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function recorte(valor, limite = 350) {
  const caracteres = Array.from(String(valor));
  return caracteres.length > limite ? caracteres.slice(0, limite).join('') + '…' : caracteres.join('');
}

export function relatorioAjuda() {
  return {
    titulo: 'Infocard — MTProto',
    html: [
      '<b>Infocard — pesquisa via MTProto</b>',
      'Envie um <code>@username</code>, um ID numérico ou <code>ID @username</code> para comprovar a referência.',
      'A busca por ID usa os métodos oficiais do MTProto. Ela pode falhar quando o Telegram não concede acesso à entidade.',
      'Também é possível usar “Escolher usuário como referência” ou encaminhar uma mensagem com remetente identificado.',
      'O resultado chega aqui após a execução do GitHub Actions. O Telegram controla os dados disponíveis e sua privacidade.',
    ].join('\n'),
    teclado: true,
  };
}

export function relatorioInvalido(entrada) {
  return {
    titulo: 'Informe um ID ou @username',
    html: [
      '<b>Não foi possível interpretar a referência</b>',
      entrada.rotulo ? 'Entrada: <code>' + esc(recorte(entrada.rotulo, 100)) + '</code>' : 'Entrada vazia',
      esc(entrada.erro),
    ].join('\n'),
    teclado: true,
  };
}

export function relatorioFalha(entrada, motivo) {
  return {
    titulo: 'Busca não iniciada: ' + recorte(entrada.rotulo, 65),
    html: [
      '<b>Não foi possível iniciar a pesquisa MTProto</b>',
      'Entrada: ' + esc(entrada.rotulo),
      esc(recorte(motivo, 700)),
    ].join('\n'),
    teclado: true,
  };
}

export function relatorioBuscando(entrada) {
  return {
    titulo: 'Buscando ' + recorte(entrada.rotulo, 100),
    html: [
      '<b>Pesquisa MTProto solicitada</b>',
      'Entrada: ' + esc(entrada.rotulo),
      'A execução foi solicitada no GitHub Actions. Um ID isolado pode não ser reconhecido pelo Telegram; se houver erro, tente ID @username ou a seleção oficial de usuário.',
      'A conclusão ou falha deve chegar nesta conversa.',
    ].join('\n'),
  };
}

export function relatorioInline(entrada) {
  const direto = entrada.tipo !== 'referencia' && /^[A-Za-z0-9_-]{1,64}$/.test(entrada.alvo);
  return {
    titulo: 'Pesquisar ' + recorte(entrada.rotulo, 75) + ' via MTProto',
    html: [
      '<b>Pesquisa via MTProto</b>',
      'Entrada: ' + esc(entrada.rotulo),
      'Abra o privado com o bot para iniciar a pesquisa e receber os resultados.',
    ].join('\n'),
    botaoPrivado: direto ? entrada.alvo : null,
  };
}

export function relatorioErro(erro) {
  return {
    titulo: 'Erro',
    html: '<b>Não foi possível responder</b>\nErro: ' + esc(erro?.name ?? 'Error') + ': ' + esc(recorte(erro?.message ?? erro)),
  };
}
