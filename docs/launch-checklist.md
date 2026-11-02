# Checklist do Infocard — pesquisa MTProto por ID ou referência

## Antes do deploy

- Use `main` e confirme CI verde; prefira repositório privado durante testes.
- Mantenha `.gitignore`, sem `.env`, sessões, tokens ou credenciais no Git.
- Confirme os cinco secrets no GitHub Actions: `API_ID`, `API_HASH`, `BOT_TOKEN`, `GH_DISPATCH_TOKEN`, `TGCLOUD_TOKEN`.
- O `GH_DISPATCH_TOKEN` precisa de Actions: Read and write; o repositório é obtido de `github.repository`, nunca fixado.
- No @BotFather, ative o Serverless; opcionalmente habilite inline mode.

## Deploy

- Execute `Deploy (Telegram Serverless)` na `main` ou faça push de mudanças do runtime.
- Confira: `npm ci`, `fetch`, `status`, migração, configuração privada no runner, `push`, webhook e dispatch.
- O healthcheck **não** prova a resolução real por MTProto.

## Smoke tests no privado

1. `/start` mostra as três formas: `@username`, `ID` e `ID @username` e o botão seletor.
2. `@BotFather` dispara um workflow MTProto real e retorna uma resposta.
3. Um ID numérico não é bloqueado localmente: inicia tentativa oficial por ID e apresenta o resultado ou causa de falha.
4. `ID @username` correspondente recebe resultado verificado; ID discordante deve dar erro sem associar pessoas erradas.
5. Teste o botão `Escolher usuário como referência`. O Telegram pode enviar apenas ID (sem username), sem garantir resolução.
6. Encaminhamento com remetente visível pode oferecer ID/username; remetente oculto deve ser informado como indisponível.
7. Confira que nenhuma consulta de perfil usa `api.getChat`.
8. Verifique execução e logs de `Resolver entidade (MTProto)`.

## Limites

Um `access_hash` é específico do contexto MTProto e não é fornecido universalmente a partir de IDs. O valor zero é uma forma documentada de referência para bots em certas condições, não um método para contornar restrições. Não prometa que qualquer ID terá resultado.
