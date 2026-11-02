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
      'Envie um <code>@username</code> público de usuário, bot, canal ou supergrupo.',
      'A pesquisa acontece no GitHub Actions com Telethon. O resultado será enviado aqui quando terminar.',
      'IDs numéricos isolados não são suportados: o MTProto geralmente exige um access_hash associado ao usuário ou canal.',
      'A disponibilidade de dados depende do Telegram e das configurações de privacidade.',
    ].join('\n'),
  };
}

export function relatorioInvalido(entrada) {
  return {
    titulo: 'Envie um @username',
    html: [
      '<b>Não foi possível pesquisar</b>',
      entrada.rotulo ? 'Entrada: <code>' + esc(recorte(entrada.rotulo, 100)) + '</code>' : 'Entrada vazia',
      esc(entrada.erro),
    ].join('\n'),
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
  };
}

export function relatorioBuscando(entrada) {
  return {
    titulo: 'Buscando ' + recorte(entrada.rotulo, 100),
    html: [
      '<b>Pesquisa MTProto solicitada</b>',
      'Entrada: ' + esc(entrada.rotulo),
      'O GitHub Actions recebeu o pedido. Se a resolução terminar, o resultado chegará nesta conversa. Se falhar, o sistema tentará informar a causa.',
    ].join('\n'),
  };
}

export function relatorioInline(entrada) {
  return {
    titulo: 'Pesquisar ' + recorte(entrada.rotulo, 75) + ' via MTProto',
    html: [
      '<b>Pesquisa via MTProto</b>',
      'Entrada: ' + esc(entrada.rotulo),
      'Abra a conversa privada com o bot para iniciar a pesquisa e receber os resultados.',
    ].join('\n'),
    botaoPrivado: entrada.username,
  };
}

export function relatorioErro(erro) {
  return {
    titulo: 'Erro',
    html: '<b>Não foi possível responder</b>\nErro: ' + esc(erro?.name ?? 'Error') + ': ' + esc(recorte(erro?.message ?? erro)),
  };
}
