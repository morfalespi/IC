# Fontes oficiais e escopo das afirmações

Revisão: 2026-11-01. Este arquivo separa comportamento documentado oficialmente de observações locais do projeto.

## Telegram Bot API

- `getChat`: https://core.telegram.org/bots/api#getchat — aceita `chat_id` numérico; quando o identificador é textual, a documentação do método especifica username de supergrupo ou canal. Não documenta resolução arbitrária de username de usuário comum.
- `ChatFullInfo`: https://core.telegram.org/bots/api#chatfullinfo — fonte dos campos opcionais exibidos pelo relatório Bot API. Campo ausente não deve ser interpretado como inexistência do dado fora do Bot API.
- `KeyboardButtonRequestUsers`: https://core.telegram.org/bots/api#keyboardbuttonrequestusers — fonte do fluxo “Escolher usuário”.
- `InlineQueryResultsButton` / `answerInlineQuery`: https://core.telegram.org/bots/api#inlinequeryresultsbutton e https://core.telegram.org/bots/api#answerinlinequery — fonte do botão que abre o privado com `start_parameter`.
- links `tg://user?id=...`: https://core.telegram.org/bots/api#formatting-options — a possibilidade de mencionar/abrir pelo ID depende das configurações de privacidade; não afirmar que o link sempre funciona.

## Telegram MTProto

- `contacts.resolveUsername`: https://core.telegram.org/method/contacts.resolveUsername — resolve username para peer e a documentação afirma explicitamente que usuários e bots podem usar o método. Isso sustenta o fallback por **username**, mas não garante sucesso para todo username nem acesso a todos os campos do perfil.
- Erros documentados do método incluem `USERNAME_INVALID` e `USERNAME_NOT_OCCUPIED`; limites/flood control continuam dependentes do servidor e devem ser tratados como condição operacional, não como um número fixo inferido pelo projeto.

## GitHub Actions / REST API

- Create a workflow dispatch event: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event — fine-grained PAT requer permissão de repositório `Actions: write`. Na versão REST atual usada pelo projeto (`2026-03-10`), a documentação registra sucesso com HTTP 200 e dados do run. O cliente também aceita 204 por compatibilidade defensiva com comportamento de versões anteriores.
- O projeto fixa `X-GitHub-Api-Version: 2026-03-10` no dispatcher e na validação do deploy. Mudanças futuras de versão devem ser confrontadas novamente com a documentação oficial antes de alterar a interpretação de respostas.

## Regra de evidência do projeto

1. **DOCUMENTADO:** a fonte oficial afirma o comportamento.
2. **OBSERVADO:** um run reproduzível mostrou o comportamento nas condições registradas.
3. **IMPLEMENTADO:** o caminho existe no código, mas ainda não há execução suficiente.
4. **HIPÓTESE:** explicação ainda não demonstrada; não deve aparecer ao usuário como fato.
5. Um HTTP 400 genérico não é evidência de `chat not found`. O fallback MTProto só deve ocorrer quando o erro do Bot API for 400 e a descrição indicar `chat not found`; outros 400 são reportados sem iniciar workflow.
