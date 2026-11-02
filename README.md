# Infocard

Bot de Telegram cuja **única forma de pesquisa de perfis é MTProto (Telethon)**. O Telegram Serverless recebe mensagens e entrega respostas usando a Bot API, mas não realiza consultas de perfis com `getChat` nem tenta uma pesquisa alternativa por Bot API.

## Como funciona

1. No privado, envie `@username` público (usuário, bot, supergrupo ou canal) ou `/start username`.
2. O Serverless valida a entrada, aplica limite de solicitações (1 por chat e 6 no total por 60 segundos) e dispara `.github/workflows/resolver.yml` no próprio repositório.
3. O GitHub Actions utiliza `API_ID`, `API_HASH` e `BOT_TOKEN` para autenticar o bot por MTProto com Telethon e executar `contacts.resolveUsername`.
4. O resultado ou o motivo da falha é entregue ao mesmo chat. O Telegram define quais campos serão acessíveis.

**IDs numéricos isolados não são pesquisáveis de modo confiável por MTProto sem `access_hash` ou contexto correspondente.** Não há fallback pela Bot API. Encaminhamentos, compartilhamentos de contatos e o antigo botão "Escolher usuário" não são usados como fonte alternativa de dados.

### Modo inline

Uma pesquisa inline não executa a consulta imediatamente: ela exibe a opção de abrir o privado com `/start username`, onde o workflow de MTProto pode ser disparado. Mensagens normais de grupos são ignoradas.

## Arquitetura

- `tgcloud/handlers/message.js`: recebe comandos e usernames no privado.
- `tgcloud/handlers/inline_query.js`: apresenta a opção de continuar no privado.
- `tgcloud/lib/entrada.js` e `consulta.js`: validação, rate limit e acionamento do resolver.
- `tgcloud/lib/despacho.js`: chamada ao GitHub Actions no repositório obtido dinamicamente.
- `scripts/resolver.py`: resolução por Telethon/MTProto, relatório e entrega da resposta.
- `.github/workflows/ci.yml`: verificações de sintaxe e placeholders.
- `.github/workflows/deploy.yml`: publicação no TGCloud.
- `.github/workflows/resolver.yml`: pesquisa MTProto sob demanda.

## Segredos

Nunca grave tokens no Git. `tgcloud/lib/segredos.js` só contém placeholders vazios no repositório. No deploy, o workflow insere temporariamente `GH_DISPATCH_TOKEN` e a referência de repositório derivada de `github.repository` no runner.

| GitHub Actions Secret | Uso |
|---|---|
| `TGCLOUD_TOKEN` | Autenticar o CLI de publicação TGCloud |
| `GH_DISPATCH_TOKEN` | Disparar `resolver.yml`, restrito ao repositório com Actions Read/Write |
| `API_ID` | Autenticação MTProto |
| `API_HASH` | Autenticação MTProto |
| `BOT_TOKEN` | Autenticação do bot no Telethon e entrega de mensagens |

## Verificação e publicação

Em Node.js 22 / Python 3.12: `npm ci` e `npm run check`.

O CI verifica sintaxe e placeholders. A publicação ocorre automaticamente na `main` quando arquivos do runtime são alterados; o deploy executa migração segura, publica módulos e valida o token de dispatch por um healthcheck sem contato com o MTProto.

Para o primeiro teste real, envie `/start` e depois `@BotFather` no privado. A resposta inicial deve indicar que a pesquisa MTProto foi solicitada; acompanhe a execução do resolver no GitHub Actions e espere a resposta final na conversa. Healthcheck e deploy verdes não comprovam pesquisa real.

O código respeita as informações que o Telegram disponibiliza e suas regras de privacidade. Consulte `docs/launch-checklist.md` e as fontes em `docs/fontes-oficiais.md`. `docs/registro.md` preserva resultados históricos, inclusive de uma implementação anterior com Bot API, que não é mais o fluxo operacional.
