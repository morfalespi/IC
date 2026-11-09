import { BotApiError } from 'sdk';

export function diagnosticoErro(erro) {
  if (erro instanceof BotApiError) return { origin: 'telegram', error_code: erro.code };
  if (erro?.origin === 'github') return { origin: 'github', status: erro.status };
  return { origin: 'runtime', type: 'OperationError' };
}

export function mensagemErro(erro) {
  const dados = diagnosticoErro(erro);
  if (dados.origin === 'telegram') return `O Telegram recusou a operação (código ${dados.error_code}).`;
  if (dados.origin === 'github') return `A execução não foi aceita (HTTP ${dados.status}).`;
  return 'Não foi possível concluir a solicitação.';
}
