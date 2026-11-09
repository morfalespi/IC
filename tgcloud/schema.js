import { table, integer, text } from 'sdk/db';

export const disparos = table('disparos', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  chatId: integer('chat_id').notNull(),
  em: integer('em').notNull(),
});

export const operacoes = table('ic_operations', {
  id: text('id').primaryKey(),
  estado: text('estado').notNull(),
});
