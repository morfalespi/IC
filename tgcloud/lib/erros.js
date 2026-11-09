import { GH_DISPATCH_TOKEN } from './segredos.js';
import { BotApiError } from 'sdk';

export function textoSeguro(valor) {
  return String(valor ?? '').split(GH_DISPATCH_TOKEN || '\u0000').join('[REDACTED]').replace(/\b\d{5,}:[A-Za-z0-9_-]{15,}/g, '[REDACTED]').slice(0, 500);
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
  if (dados.origin === 'telegram') {
    return `Telegram ${dados.error_code}: ${dados.description}`;
  }
  if (dados.origin === 'github') return [dados.description, dados.message].filter(Boolean).join(' ');
  return 'Falha no processamento. Consulte os diagnósticos privados.';
}

