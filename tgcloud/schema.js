import { table, integer } from 'sdk/db';

export const disparos = table('disparos', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  chatId: integer('chat_id').notNull(),
  em: integer('em').notNull(),
});
