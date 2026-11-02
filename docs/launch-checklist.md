# Checklist de lançamento — pesquisa somente por MTProto

## Configuração

- O repositório deve preferencialmente ser privado no lançamento.
- Confirme a branch `main` e o CI verde.
- Cadastre em GitHub Actions Secrets: `TGCLOUD_TOKEN`, `GH_DISPATCH_TOKEN`, `API_ID`, `API_HASH` e `BOT_TOKEN`.
- `GH_DISPATCH_TOKEN` deve ser fine-grained, restrito ao repositório e com permissão de Actions: Read and write.
- `github.repository` deve ser injetado pelo workflow, sem nome de owner/repo fixado no código.
- Ative o Serverless do bot no @BotFather; obtenha seu token CLI em Serverless → CLI Access.
- Configure inline mode no @BotFather caso deseje esse fluxo.

## Deploy

- Acione `Deploy (Telegram Serverless)` ou altere o runtime na `main`.
- Confirme: autenticação TGCloud, `npm ci`, `fetch`, `status`, migração, injeção de configuração, `push`, webhook e dispatch healthcheck.
- Healthcheck valida o disparo do workflow, mas **não** uma consulta real.

## Testes de funcionamento

1. Envie `/start` ao bot no privado: deve explicar a pesquisa por MTProto.
2. Envie `@BotFather` ou outro username público conhecido: deve mostrar que solicitou a pesquisa, sem chamar `getChat`.
3. Confira uma execução **não-healthcheck** de `Resolver @username (MTProto)` no GitHub Actions.
4. Confira que o resultado ou a falha da pesquisa chega ao mesmo chat.
5. Envie um ID numérico: deve explicar que um ID isolado sem `access_hash` não é confiável; não deve disparar o resolver.
6. Se o inline mode estiver ativo, teste o botão que abre a conversa privada.
7. Confirme que não existem tokens, `.env`, sessões ou credenciais versionados.

## Critério de eficácia

Registre a entrada, o horário, o run do resolver, seu status e a resposta recebida. Um deploy concluído não prova a resolução de todos os usernames. O Telegram pode limitar solicitações e ocultar campos conforme a configuração do perfil.
