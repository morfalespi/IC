# Infocard

Bot de Telegram para consultar informações que o próprio Telegram disponibiliza por APIs oficiais. O caminho principal usa o **Bot API**; quando um `@username` de usuário comum não é resolvido por `getChat`, o bot pode solicitar uma busca complementar por **MTProto** em um workflow do GitHub Actions.

O projeto distingue comportamento **documentado**, **observado**, **implementado** e **hipótese**. Consulte `docs/fontes-oficiais.md` e `docs/registro.md` antes de transformar um resultado isolado em afirmação geral.

## Fluxos

- **ID numérico ou @username:** tenta `getChat` pelo Telegram Bot API.
- **@username de usuário comum não resolvido pelo Bot API:** no privado, tenta disparar `.github/workflows/resolver.yml`, que usa Telethon/MTProto. O fallback só ocorre quando o Bot API responde HTTP 400 com descrição `chat not found`.
- **Inline mode:** se a consulta exigir MTProto, o resultado oferece um botão para abrir o privado com `/start <username>`.
- **Sem MTProto:** “Escolher usuário”, mensagem encaminhada, contato compartilhado e `text_mention` podem fornecer dados diretamente pelo Bot API quando o Telegram os inclui.
- **Grupos:** mensagens normais em grupos são ignoradas pelo handler.

O bot não contorna configurações de privacidade. Campo ausente significa apenas que aquela API não o entregou naquela consulta.

## Arquitetura

- `tgcloud/handlers/message.js`: mensagens privadas e `/start`/`/help`.
- `tgcloud/handlers/inline_query.js`: consultas inline.
- `tgcloud/lib/consulta.js`: leitura via Bot API e decisão de fallback.
- `tgcloud/lib/despacho.js`: dispara o resolver no mesmo repositório GitHub do deploy.
- `tgcloud/lib/limite.js`: limite operacional para solicitações MTProto.
- `scripts/resolver.py`: resolução MTProto via Telethon e resposta ao chat.
- `.github/workflows/ci.yml`: validação sintática e proteção do placeholder de segredos.
- `.github/workflows/deploy.yml`: migração e deploy no Telegram Serverless.
- `.github/workflows/resolver.yml`: job de resolução MTProto.

## Segurança de configuração

O Git nunca deve conter tokens. `tgcloud/lib/segredos.js` fica versionado apenas com valores vazios. Durante o deploy, o GitHub Actions injeta temporariamente:

- `GH_DISPATCH_TOKEN`, vindo de GitHub Actions Secrets;
- `GH_REPOSITORY`, vindo automaticamente de `${{ github.repository }}`.

Isso evita acoplamento a um owner/repo específico. O token do GitHub deve ser **fine-grained**, restrito somente a este repositório e com `Actions: Read and write`.

Secrets necessários:

| Secret | Uso |
|---|---|
| `TGCLOUD_TOKEN` | deploy pelo CLI do Telegram Serverless |
| `GH_DISPATCH_TOKEN` | disparar `resolver.yml` a partir do bot |
| `API_ID` | MTProto / `my.telegram.org/apps` |
| `API_HASH` | MTProto / `my.telegram.org/apps` |
| `BOT_TOKEN` | autenticar o bot no resolver e responder ao chat |

## Validação local

Requer Node.js 22 e Python 3.12 para reproduzir o ambiente de CI:

```bash
npm ci
npm run check
```

O check valida sintaxe de todos os módulos JS, compila `scripts/resolver.py` e falha se `tgcloud/lib/segredos.js` contiver algo diferente dos placeholders vazios.

## Publicação

O primeiro lançamento deve começar em repositório privado. Siga `docs/launch-checklist.md` para criar os secrets, habilitar Serverless/inline mode e executar os smoke tests.

Pushes para `main` executam CI. Alterações de runtime também acionam `Deploy (Telegram Serverless)`, que faz `fetch`, `status`, migração segura, injeta a configuração privada somente no runner, publica os módulos, verifica o webhook e dispara um healthcheck do resolver que não acessa Telegram/MTProto, para testar de verdade a permissão do token.

## Limites conhecidos

- GitHub Actions é uma dependência externa do fallback MTProto; fila, indisponibilidade e rate limits podem atrasar ou impedir a resposta.
- O resolver tolera `FloodWait` do Telegram até o orçamento definido no script; acima dele, devolve falha ao chat.
- O projeto aplica um limite próprio de 1 pedido MTProto por chat e 6 no total a cada 60 segundos. Esses números são decisão operacional do projeto, não limites oficiais do Telegram.
- Um teste bem-sucedido para um username não demonstra que todos os usernames ou todos os campos serão resolvidos.

## Evidência e fontes

- `docs/fontes-oficiais.md`: fontes oficiais e escopo de cada afirmação.
- `docs/registro.md`: histórico de testes, defeitos encontrados e decisões.
- `SECURITY.md`: regras de segredos e tratamento de dados.