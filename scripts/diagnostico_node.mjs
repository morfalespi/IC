export function diagnosticoNode(erro, origem) {
  let descricao = String(erro?.description ?? erro?.message ?? erro?.name ?? 'Erro');
  for (const nome of ['BOT_TOKEN', 'API_HASH', 'TGCLOUD_TOKEN', 'GH_DISPATCH_TOKEN']) {
    if (process.env[nome]) descricao = descricao.split(process.env[nome]).join('[redigido]');
  }
  descricao = descricao.replace(/(?:app|bot)?\d+:[A-Za-z0-9_-]+/g, '[redigido]')
    .replace(/(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)/g, '[redigido]');
  return { origin: origem, type: erro?.name, status: erro?.status, description: descricao };
}
