# Fontes oficiais — implementação MTProto

Atualizado em 2026-11-02. O **fluxo operacional de pesquisa** usa exclusivamente Telegram MTProto por `contacts.resolveUsername`. Referências anteriores ao `getChat` como consulta de perfil foram descontinuadas e permanecem apenas no registro histórico.

## Pesquisa via MTProto

- `contacts.resolveUsername`: https://core.telegram.org/method/contacts.resolveUsername — resolve usernames; a documentação explicita o uso permitido por bots e usuários. Pode responder `USERNAME_INVALID` e `USERNAME_NOT_OCCUPIED`.
- Login de bot via MTProto: https://core.telegram.org/api/bots — autorização usando `BOT_TOKEN`, `API_ID` e `API_HASH`.
- `access_hash` e IDs: https://core.telegram.org/api/peers — um ID de usuário/canal isolado não fornece necessariamente a referência necessária para consultas MTProto.
- A disponibilidade de dados é limitada pelas respostas e pela privacidade do Telegram.

## Bot API usada apenas como transporte

- `sendMessage`: https://core.telegram.org/bots/api#sendmessage — entrega de mensagens ao usuário.
- `answerInlineQuery`: https://core.telegram.org/bots/api#answerinlinequery — resposta inline que direciona ao privado.
- `InlineQueryResultsButton`: https://core.telegram.org/bots/api#inlinequeryresultsbutton — uso de `start_parameter` para abrir o privado.
- A Bot API não realiza a pesquisa de perfis neste projeto.

## GitHub Actions

- Dispatch do workflow: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event — requer permissão Actions: write no token fine-grained.
- Referência dinâmica: `github.repository`. O dispatcher aceita HTTP 200 e 204 como indicação de disparo aceito, mas isso não é prova de que a resolução MTProto tenha concluído.

## Evidências

A documentação oficial fundamenta comportamentos possíveis, não garante um resultado para todas as contas. O arquivo `docs/registro.md` contém observações históricas, inclusive de uma versão substituída e que não deve ser usada como referência da arquitetura atual.
