// O BotFather restringe o acesso do bot gerenciado ao proprietário.
// Este módulo apenas impõe que comandos ocorram em uma conversa privada
// entre o remetente e o próprio bot, sem manter listas de IDs no código.
export function autorizado(userId, chatId, chatType, isBot = false) {
  if (chatType !== 'private' || isBot) return false;
  const user = String(userId ?? '');
  const chat = String(chatId ?? '');
  return /^\d+$/.test(user) && user === chat;
}
