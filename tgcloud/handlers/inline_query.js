import { api } from 'sdk';
export default async function (query) {
  await api.answerInlineQuery({ inline_query_id: query.id, results: [], cache_time: 0, is_personal: true });
}
