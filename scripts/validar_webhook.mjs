import { pathToFileURL } from 'node:url';
import { resolveToken } from '../node_modules/@tgcloud/cli/src/core/credentials.js';
import { getWebhook } from '../node_modules/@tgcloud/cli/src/api/endpoints.js';
import { diagnosticoNode } from './diagnostico_node.mjs';

export async function conferirWebhook(token) {
  const estado = await getWebhook(token);
  if (estado?.in_sync !== true || typeof estado.url !== 'string' || !estado.url.startsWith('https://') ||
      !Array.isArray(estado.allowed_updates) || !Array.isArray(estado.expected?.allowed_updates) ||
      estado.url !== estado.expected.url ||
      estado.allowed_updates.length !== estado.expected.allowed_updates.length ||
      !estado.expected.allowed_updates.every(tipo => estado.allowed_updates.includes(tipo))) {
    throw new Error('Webhook não corresponde aos handlers publicados. Nenhuma sincronização automática foi executada.');
  }
  if (!Number.isSafeInteger(estado.pending_update_count) || estado.pending_update_count < 0) {
    throw new Error('Estado do webhook sem contagem válida de updates pendentes.');
  }
  console.log(JSON.stringify({ origin: 'webhook_validation', in_sync: true, pending_updates: estado.pending_update_count,
    historical_error: typeof estado.last_error_message === 'string' && estado.last_error_message.length > 0 }));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    await conferirWebhook(await resolveToken());
  } catch (erro) {
    console.error(JSON.stringify(diagnosticoNode(erro, 'webhook_validation')));
    process.exitCode = 1;
  }
}
