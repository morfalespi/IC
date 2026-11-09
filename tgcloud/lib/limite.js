import { db } from 'sdk';
import { operacoes } from '../schema.js';

export async function reservarAtualizacao(updateId) {
  if (!Number.isSafeInteger(updateId)) throw new Error('Update sem identificador estável.');
  // A claimed update is never automatically replayed after a crash or an uncertain dispatch.
  const rows = await db.insert(operacoes).values({ id: String(updateId), estado: 'claimed' })
    .onConflictDoNothing({ target: operacoes.id }).returning({ id: operacoes.id });
  return rows.length === 1;
}

export async function reservarDisparo(chatId) {
  const now = Date.now();
  // SQLite executes the test and insert atomically, including concurrent handlers.
  const rows = await db.all('INSERT INTO disparos (chat_id, em) SELECT :chat, :now WHERE NOT EXISTS (SELECT 1 FROM disparos WHERE chat_id = :chat AND em > :cutoff) RETURNING id',
    { ':chat': Number(chatId), ':now': now, ':cutoff': now - 30000 });
  return { permitido: rows.length === 1, id: rows[0]?.id ?? null };
}
export async function reservarDisparo() {
  return { permitido: true, id: null };
}

export async function liberarDisparo() {}
