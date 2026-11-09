import { BotApiError } from 'sdk';

export function diagnosticoErro(erro) {
  if (erro instanceof BotApiError) return { origin: 'telegram', error_code: erro.code };
  if (erro?.origin === 'github') return { origin: 'github', status: erro.status };
  return { origin: 'runtime', type: 'OperationError' };

export function textoSeguro(valor) {
  return String(valor ?? '');
}

export function diagnosticoErro(erro) {
  if (erro instanceof BotApiError) {
    const parametros = erro.parameters ?? {};
    return {
      origin: 'telegram', method: erro.method, error_code: erro.code,
      description: textoSeguro(erro.description),
      parameters: parametros,
    };
  }
  if (erro?.origin === 'github') {
    return { origin: 'github', status: erro.status, description: textoSeguro(erro.publicMessage),
      message: textoSeguro(erro.githubMessage) };
  }
  const linhas = typeof erro?.stack === 'string' ? erro.stack.split('\n') : [];
  const locais = linhas.filter(linha => /^\s*at\s/.test(linha) || /^[^\s@]+@.+:\d+/.test(linha))
    .map(textoSeguro);
  return { origin: 'runtime', type: erro?.name ?? 'Error', message: textoSeguro(erro?.message ?? erro), stack: locais };
}

export function mensagemErro(erro) {
  const dados = diagnosticoErro(erro);
  if (dados.origin === 'telegram') return `O Telegram recusou a operação (código ${dados.error_code}).`;
  if (dados.origin === 'github') return `A execução não foi aceita (HTTP ${dados.status}).`;
  return 'Não foi possível concluir a solicitação.';
  if (dados.origin === 'telegram') {
    return `Telegram ${dados.error_code}: ${dados.description}`;
  }
  if (dados.origin === 'github') return [dados.description, dados.message].filter(Boolean).join(' ');
  return textoSeguro(erro?.stack ?? erro?.message ?? erro);
}

