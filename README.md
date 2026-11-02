# Infocard — Telegram Serverless + MTProto

O Infocard recebe uma referência de Telegram no privado, cria uma ficha de andamento, solicita o resolver MTProto no GitHub Actions e entrega os **campos mapeados que o Telegram efetivamente retornou**. Não consulta perfis pelo Bot API getChat. Um ID arbitrário não garante acesso.

## Uso

| Entrada ou ação | Resultado |
|---|---|
| /start | Mensagem de ajuda com teclado de seleção |
| /help | Mesma ajuda |
| @username | Resolve pelo método oficial contacts.resolveUsername |
| ID numérico | Tenta as operações MTProto para o tipo de peer; pode falhar sem contexto |
| ID @username | Resolve username e exige que o ID retornado coincida |
| Escolher usuário/canal/grupo | Recebe o ID e dados opcionais fornecidos pelo seletor oficial |
| Encaminhar mensagem, contato, menção | Usa somente as referências disponibilizadas pelo Telegram |
| Atualizar | Faz nova busca e edita o cartão, quando possível |
| Completo + Markdown | Faz nova busca, envia páginas ricas e arquivo .md por sendDocument |
| Modo inline | Exibe convite para pesquisar no privado; não lê perfis no outro chat |

Não existem comandos /buscar, /completo ou /download. O repositório não configura setMyCommands; o menu do BotFather pode divergir dos handlers.

O formato ID @username é convenção de entrada **deste bot**. Não utilizar o antigo separador ID|username. O callback_data é um campo definido pelo aplicativo sob o limite da Bot API (1 a 64 bytes). O TGCloud interpreta o callback separadamente do texto e passa alvo e expected_id como inputs distintos ao workflow. O worker resolve @username por contacts.resolveUsername e compara o peer a expected_id quando informado.

## Resultado

1. **Ficha de andamento:** cartão rico do Telegram com identificação de consulta e status.
2. **Resumo:** dados confirmados, alguns campos extras, foto se retornada e botões. A abreviação do resumo é intencional.
3. **Completo + Markdown:** nova consulta que entrega os campos efetivamente mapeados no resolver, tabelas paginadas e anexo .md em UTF-8. Se a API recusar Rich Messages, tenta HTML convencional paginado; se recusar a mídia embutida, tenta foto separada.
4. **Falhas:** mensagem de erro e possibilidade de nova pesquisa. Quando o Telegram/GitHub estiver indisponível, a notificação não é garantida.

Os campos possíveis incluem nome, ID, usernames, bio, informações de bot, indicadores públicos, dados comerciais, algumas métricas Telegram Stars, fotos e músicas acessíveis, dados de canais e grupos. **Não são todos os campos possíveis do MTProto**: são os que scripts/resolver.py extrai e que a API disponibiliza à sessão do bot. Campo ausente não equivale a inexistência.

Os dados opcionais compartilhados no seletor podem ser mostrados no cartão inicial, mas não são preservados em armazenamento temporário independente; uma edição posterior pode substituí-los. O relatório MTProto só apresenta aquilo que o worker confirmou no protocolo.

## Arquitetura

| Etapa | Código | API usada |
|---|---|---|
| Receber mensagem | tgcloud/handlers/message.js | Telegram Serverless Update Message |
| Seletores e callback | tgcloud/lib/envio.js, tgcloud/handlers/callback_query.js | Telegram Bot API |
| Interpretar referência | tgcloud/lib/entrada.js | Convenção local validada |
| Limite de disparo | tgcloud/lib/limite.js | Banco Serverless |
| Disparar worker | tgcloud/lib/despacho.js | GitHub workflow_dispatch |
| Resolver identidade | scripts/resolver.py | Telegram MTProto via Telethon |
| Gerar Rich Messages e .md | scripts/resolver.py, scripts/ficha_completa.py | sendRichMessage, editMessageText, sendDocument |

O limite atual é de **2 consultas por chat e 6 globalmente em 60 segundos**. O workflow usa sessão MTProto temporária, sem cache persistente de peers. Sua consulta pode falhar por permissões, ausência de access_hash, privacidade ou rate limit.

## Publicação e verificação

- CI: npm ci e npm run check executam checagem de sintaxe de JS/Python e de placeholders. As regras do proprietário não permitem testes escritos pelo autor da mudança.
- Deploy TGCloud: em alterações de tgcloud/** ou configuração, executa fetch, status, **migrate**, push, webhook e healthcheck. O push sozinho não migra o banco.
- Resolver: scripts/** são usados no próximo workflow_dispatch na main. O healthcheck **não executa Telethon**.
- Prova de ponta a ponta: consulta real, entidade resolvida corretamente, envio confirmado por Bot API e resultado recebido no chat, incluindo anexos, se solicitados.

Referência da auditoria: [docs/auditoria-operacional.md](docs/auditoria-operacional.md). Evidências históricas com seus commits ficam em [docs/registro.md](docs/registro.md).

## Segurança

**O repositório é público.** Os inputs do workflow GitHub Actions incluem referências pesquisadas e identificadores de chat/mensagem e podem aparecer em metadados e logs acessíveis. Não utilizar este fluxo como solução confidencial para pesquisas sensíveis. O bot também não possui autorização universal para obter dados privados de terceiros. Redesenhar o transporte e o armazenamento é necessário para garantir confidencialidade do contexto de consulta.

Os cinco secrets existentes são TGCLOUD_TOKEN, GH_DISPATCH_TOKEN, API_ID, API_HASH e BOT_TOKEN. Devem permanecer somente em Actions Secrets e nos ambientes de execução apropriados, nunca em commits, logs deliberados ou documentação. O deploy injeta o token de dispatch no módulo publicado, não no arquivo versionado.

## Documentação oficial

- https://core.telegram.org/bots/api
- https://core.telegram.org/bots/api-changelog
- https://core.telegram.org/api/peers
- https://core.telegram.org/method/contacts.resolveUsername
- https://core.telegram.org/bots/serverless
- https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event

Documentação de API e código executável determinam capacidades; documentação histórica e healthchecks não substituem confirmação real.
