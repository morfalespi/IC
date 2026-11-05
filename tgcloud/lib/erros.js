import { BotApiError } from 'sdk';
import { GH_DISPATCH_TOKEN } from './segredos.js';

export class FalhaEntrega extends Error {
  constructor(causa, estado = 'unconfirmed') {
    super('Resposta não confirmada; envio alternativo bloqueado.', { cause: causa });
    this.name = 'FalhaEntrega';
    this.estado = estado;
  }
}

export function textoSeguro(valor) {
  let texto = String(valor ?? '');
  if (GH_DISPATCH_TOKEN) texto = texto.split(GH_DISPATCH_TOKEN).join('[redigido]');
  return texto.replace(/(?:bot)?\d+:[A-Za-z0-9_-]+/g, '[redigido]')
    .replace(/(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)/g, '[redigido]');
}

export function diagnosticoErro(erro) {
  if (erro instanceof FalhaEntrega) {
    return { ...diagnosticoErro(erro.cause), delivery_state: erro.estado };
  }
  if (erro instanceof BotApiError) {
    const parametros = erro.parameters ?? {};
    return {
      origin: 'telegram', method: erro.method, error_code: erro.code,
      description: textoSeguro(erro.description),
      parameters: Object.fromEntries(Object.entries(parametros)
        .filter(([chave, valor]) => ['retry_after', 'migrate_to_chat_id'].includes(chave) && Number.isSafeInteger(valor))),
    };
  }
  if (erro?.origin === 'github') {
    return { origin: 'github', status: erro.status, description: textoSeguro(erro.publicMessage),
      message: textoSeguro(erro.githubMessage) };
  }
  const linhas = typeof erro?.stack === 'string' ? erro.stack.split('\n') : [];
  const locais = linhas.filter(linha => /^\s*at\s/.test(linha) || /^[^\s@]+@.+:\d+/.test(linha))
    .map(textoSeguro);
  return { origin: 'runtime', type: erro?.name ?? 'Error', stack: locais };
}

export function mensagemErro(erro) {
  const dados = diagnosticoErro(erro);
  if (dados.origin === 'telegram') {
    const espera = dados.parameters.retry_after;
    return `Telegram ${dados.error_code}: ${dados.description}` +
      (Number.isSafeInteger(espera) ? ` Aguarde ${espera} s antes de repetir.` : '');
  }
  if (dados.origin === 'github') return [dados.description, dados.message].filter(Boolean).join(' ');
  return 'A comunicação com o serviço falhou. Tente novamente em instantes.';
}
