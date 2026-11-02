# Checklist de lançamento

## 1. Repositório

- Criar o repositório como **privado** para o primeiro lançamento.
- Branch padrão: `main`.
- Subir este código sem nenhum token no histórico.
- Confirmar que o workflow `CI` fica verde.

## 2. Telegram

- Criar/selecionar o bot no @BotFather.
- Ativar Telegram Serverless para o bot.
- Obter o token separado de CLI do Serverless (`TGCLOUD_TOKEN`).
- Obter o token normal da Bot API (`BOT_TOKEN`) para o resolver MTProto.
- Ativar inline mode se o fluxo inline for desejado.

## 3. MTProto

- Criar/usar uma aplicação em `my.telegram.org/apps` e obter `API_ID` e `API_HASH`.
- Guardar ambos exclusivamente como GitHub Actions secrets.

## 4. GitHub Actions secrets

Criar os secrets abaixo em **Settings → Secrets and variables → Actions**:

- `TGCLOUD_TOKEN`
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `GH_DISPATCH_TOKEN`

`GH_DISPATCH_TOKEN` deve ser fine-grained, restrito somente a este repositório, com **Actions: Read and write**. O nome do repositório não é secret e é injetado automaticamente pelo workflow a partir de `github.repository`.

## 5. Primeiro deploy

- Executar `Deploy (Telegram Serverless)` manualmente ou fazer um push válido na `main`.
- Confirmar as etapas: secret → `npm ci` → `fetch` → `status` → migração → injeção privada → `push` → `webhook` → validação do dispatch.
- Não considerar o deploy concluído se a etapa de validação do `GH_DISPATCH_TOKEN` falhar.

## 6. Smoke tests

No privado com o bot:

1. `/start` deve mostrar ajuda.
2. Consultar um `@username` de canal/supergrupo conhecido.
3. Consultar um ID conhecido pelo Bot API.
4. Testar “Escolher usuário”.
5. Encaminhar uma mensagem de usuário com remetente visível.
6. Consultar um username de usuário comum e confirmar a criação do run `Resolver username ou ID (MTProto)`.
7. Confirmar que o resultado ou a falha chega ao mesmo chat.
8. Testar inline mode, se habilitado.

## 7. Critério de eficácia

Registre cada teste com entrada, horário, caminho usado (Bot API ou MTProto), status do workflow e resultado. Um teste bem-sucedido demonstra apenas aquele cenário; não deve ser generalizado para usernames, contas ou condições de privacidade diferentes.
