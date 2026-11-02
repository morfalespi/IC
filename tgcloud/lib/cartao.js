function esc(valor) {
  return String(valor ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function linha(campo, valor) {
  return '<tr><th>' + esc(campo) + '</th><td>' + esc(String(valor).slice(0, 180)) + '</td></tr>';
}

function controles(alvo) {
  const ref = 'r:' + alvo;
  return '<tg-button-row align="center">' +
    '<tg-button type="callback_data" style="primary" data="' + esc(ref) + '">🔄 Atualizar</tg-button>' +
    '</tg-button-row>';
}

export function cartaoPesquisa(entrada, dados = null) {
  const linhas = [
    linha('Consulta', entrada.rotulo),
    linha('Etapa', 'Aguardando resolução MTProto'),
  ];
  if (dados) {
    linhas.push(linha('Origem', dados.origem));
    linhas.push(linha('ID informado', dados.id));
    if (dados.nome) linhas.push(linha('Nome informado', dados.nome));
    if (dados.username) linhas.push(linha('Username informado', '@' + dados.username));
    if (dados.fotoInformada) linhas.push(linha('Foto informada', 'Sim, referência compartilhada'));
  }
  return '<h2>🔎 Infocard</h2>' +
    '<p><b>⏳ Pesquisando…</b></p>' +
    '<table bordered compact><tr><th>Campo</th><th>Valor</th></tr>' + linhas.join('') + '</table>' +
    '<p><i>A ficha será atualizada após a consulta oficial ao Telegram.</i></p>' +
    controles(entrada.alvo);
}

export function cartaoErro(entrada, motivo) {
  return '<h2>⚠️ Infocard</h2>' +
    '<p><b>Pesquisa não concluída</b></p>' +
    '<table bordered compact>' + linha('Consulta', entrada.rotulo) +
    linha('Motivo', motivo) + '</table>' + controles(entrada.alvo);
}
