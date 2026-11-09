// Deployment supplies explicit IDs. Empty lists deny all application operations.
export const ALLOWED_USER_IDS = [];
export const ALLOWED_CHAT_IDS = [];

export function autorizado(userId, chatId) {
  return ALLOWED_USER_IDS.includes(String(userId)) && ALLOWED_CHAT_IDS.includes(String(chatId));
}
