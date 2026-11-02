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
