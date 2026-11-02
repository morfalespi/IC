import { db } from 'sdk';
import { and, eq, gt, lt, sql } from 'sdk/db';
import { disparos } from '../schema.js';

const JANELA_SEGUNDOS = 60;
const POR_CHAT = 1;
const NO_TOTAL = 6;
const RETENCAO_SEGUNDOS = 3600;

export async function reservarDisparo(chatId) {
  const agora = Math.floor(Date.now() / 1000);
  const desde = agora - JANELA_SEGUNDOS;
  const resultado = await db.run(sql`INSERT INTO disparos (chat_id, em) SELECT ${chatId}, ${agora} WHERE (SELECT COUNT(*) FROM disparos WHERE chat_id = ${chatId} AND em > ${desde}) < ${POR_CHAT} AND (SELECT COUNT(*) FROM disparos WHERE em > ${desde}) < ${NO_TOTAL}`);
  if (resultado.rowsAffected === 1) {
    await db.delete(disparos).where(lt(disparos.em, agora - RETENCAO_SEGUNDOS)).run();
    return { permitido: true, id: resultado.lastInsertRowid };
  }
  const doChat = await db.select().from(disparos).where(and(eq(disparos.chatId, chatId), gt(disparos.em, desde))).all();
  if (doChat.length >= POR_CHAT) {
    const maisRecente = Math.max(...doChat.map((linha) => linha.em));
    const espera = Math.max(1, maisRecente + JANELA_SEGUNDOS - agora);
    return { permitido: false, motivo: `Aguarde ${espera} s para fazer outra busca por MTProto.` };
  }
  return { permitido: false, motivo: 'Há muitas buscas por MTProto em andamento. Tente de novo em instantes.' };
}

export async function liberarDisparo(id) {
  await db.delete(disparos).where(eq(disparos.id, id)).run();
}
