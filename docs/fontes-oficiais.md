# Fontes oficiais da pesquisa MTProto

Atualizado em 2026-11-02. O fluxo de pesquisa usa MTProto/Telethon; a Bot API só recebe updates, referências compartilhadas pelo usuário e entrega mensagens.

- Banco de peers e `access_hash`: https://core.telegram.org/api/peers — documenta referências completas, mínimas, de mensagens e o `access_hash` zero para bots, além da exigência de referências para IDs não conhecidos. Valores são ligados a contextos de autenticação e não devem ser intercambiados indiscriminadamente.
- `users.getUsers`: https://core.telegram.org/method/users.getUsers — aceita `InputUser`, inclusive com referência zero onde o servidor permitir.
- `users.getFullUser`: https://core.telegram.org/method/users.getFullUser — requer `InputUser`; pode recusar usuário indisponível.
- `contacts.resolveUsername`: https://core.telegram.org/method/contacts.resolveUsername — resolve username e retorna peer e entidades que podem conter o hash apropriado.
- `messages.getChats`: https://core.telegram.org/method/messages.getChats — grupos básicos usam ID, sem `access_hash`.
- `channels.getChannels`: https://core.telegram.org/method/channels.getChannels — canais e supergrupos precisam de referência de canal válida.
- `KeyboardButtonRequestUsers` e `users_shared`: https://core.telegram.org/bots/api#keyboardbuttonrequestusers — permitem obter a identificação do usuário compartilhado, mas **não garantem** que o bot possa consultar a entidade apenas pelo ID.
- `MessageOrigin` e `MessageEntity`: https://core.telegram.org/bots/api — referências fornecidas por encaminhamentos e menções podem conter ID e username; o remetente pode ser oculto.
- Entidades e cache do Telethon: https://docs.telethon.dev/en/stable/concepts/entities.html — a biblioteca precisa de ID e hash no contexto certo. O resolver usa sessão temporária, sem cache persistente.
- Dispatch: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event — requer permissão Actions: write no GitHub token.

A existência desses métodos oficiais não garante retorno de dados para quaisquer IDs. O projeto mantém verificação explícita de ID contra username em consultas por referência composta.

## Dados adicionais no relatório (2026-11-02)

- `photos.getUserPhotos`: https://core.telegram.org/method/photos.getUserPhotos — usuários e bots podem solicitar as fotos acessíveis; respostas podem conter amostra ou total.
- `users.getSavedMusic`: https://core.telegram.org/method/users.getSavedMusic — usuários e bots podem solicitar músicas do perfil, sujeitas à privacidade.
- `userFull`: https://core.telegram.org/constructor/userFull — contém `stars_rating`, `saved_music`, `business_work_hours` e outros campos condicionais.
- `channelFull`: https://core.telegram.org/constructor/channelFull — campos opcionais de canais e supergrupos.
- `Peer database`: https://core.telegram.org/api/peers — um ID sem referência conhecida não garante acesso; `access_hash` depende do contexto da autenticação.
- `Telethon Session`: https://docs.telethon.dev/en/stable/concepts/sessions.html — uma sessão persistida pode reutilizar entidades já vistas, mas exige armazenamento seguro.

## Rich Messages — Bot API 10.3 (2026-08-24)

- `sendRichMessage` e `InputRichMessage`: https://core.telegram.org/bots/api#sendrichmessage e https://core.telegram.org/bots/api#inputrichmessage.
- Tabelas compactas, botões dentro da mensagem, imagem e blocos expansíveis: https://core.telegram.org/bots/api#rich-messages.
- `editMessageText` com `rich_message`: https://core.telegram.org/bots/api#editmessagetext — atualiza mensagens de texto ou Rich Messages.
- `InputRichMessageMedia`: https://core.telegram.org/bots/api#inputrichmessagemedia — `tg://photo?id=` no HTML e arquivo associado via multipart.
- `answerCallbackQuery`: https://core.telegram.org/bots/api#answercallbackquery — responde à ação do botão **Atualizar**.
- `sendRichMessageDraft`: https://core.telegram.org/bots/api#sendrichmessagedraft — rascunho temporário, não usado como ficha persistente.

O SDK do TGCloud encaminha nomes de métodos Bot API dinamicamente. A nova edição com tabela e mídia precisa de verificação manual real porque CI apenas compila o código.

## Capacidade e limites reais da Rich Message

- Limites de 32.768 caracteres, 500 blocos, 16 níveis, 50 anexos, 20 colunas: https://core.telegram.org/bots/api#rich-message-formatting-options
- `sendRichMessage`, `editMessageText` (com `rich_message`), `InputRichMessageMedia`: https://core.telegram.org/bots/api
- `userFull` e campos condicionais: https://core.telegram.org/constructor/userFull
- `channelFull` e campos condicionais: https://core.telegram.org/constructor/channelFull
- Pontuação Telegram Stars: https://core.telegram.org/api/stars

Mesmo com paginação, o relatório só contém campos oficialmente recebidos; o Telegram não garante acesso irrestrito a IDs desconhecidos.
