# Infocard — Telegram Serverless + APIs do Telegram

O Infocard recebe uma referência no privado, resolve a entidade por MTProto e, na exportação completa, combina leituras MTProto e Bot API. A exportação preserva as respostas brutas de cada método tentado e baixa mídia quando a API e as permissões permitem. Um ID arbitrário não garante acesso.

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
| Exportação completa | Faz nova busca e envia páginas legíveis, Markdown, JSONL bruto e arquivos de mídia ZIP quando acessíveis |
| Modo inline | Exibe convite para pesquisar no privado; não lê perfis no outro chat |

Não existem comandos /buscar, /completo ou /download. O repositório não configura setMyCommands; o menu do BotFather pode divergir dos handlers.

O formato ID @username é convenção de entrada **deste bot**. Não utilizar o antigo separador ID|username. O callback_data é um campo definido pelo aplicativo sob o limite da Bot API (1 a 64 bytes). O TGCloud interpreta o callback separadamente do texto e passa alvo e expected_id como inputs distintos ao workflow. O worker resolve @username por contacts.resolveUsername e compara o peer a expected_id quando informado.

## Resultado

1. **Ficha de andamento:** cartão rico do Telegram com identificação de consulta e status.
2. **Resultado na tela:** identificação e campos mapeados que as APIs retornarem, em tantas Rich Messages quanto necessárias, com foto e botões quando permitidos. A exportação JSONL preserva também respostas brutas que ainda não tenham mapeamento visual.
3. **Obter Markdown completo:** ação opcional que faz uma nova consulta, repete as informações na tela em páginas ricas e envia o anexo .md em UTF-8. Se a API recusar Rich Messages, tenta HTML convencional paginado; se recusar a mídia embutida, tenta foto separada.
4. **Falhas:** mensagem de erro e possibilidade de nova pesquisa. Quando o Telegram/GitHub estiver indisponível, a notificação não é garantida.

**A exportação completa tenta leituras adicionais pelas duas APIs.** Para usuários, chama `getChat`, `getUserProfilePhotos`, `getUserProfileAudios` e `getUserPersonalChatMessages`; para grupos e canais, chama `getChat`, `getChatAdministrators` e `getChatMemberCount`. Respostas Bot API, inclusive erros de acesso, vão para o JSONL. Ausência de um campo ou erro de permissão não prova que os dados não existam. MTProto continua limitado à sessão de bot e às permissões concedidas pelo Telegram.

Os dados opcionais compartilhados no seletor podem ser mostrados no cartão inicial, mas não são preservados em armazenamento temporário independente; uma edição posterior pode substituí-los. O relatório registra aquilo que cada resposta do Telegram confirmou.

## Entrega integral e tolerância a falhas (2026-11-02)

A consulta comum mostra os campos mapeados. O botão **Exportação completa** solicita páginas legíveis, Markdown, JSONL com respostas MTProto e Bot API e pacotes ZIP de mídia acessível. A confirmação do envio não comprova que todos os dados possíveis foram retornados nem substitui uma consulta real de ponta a ponta.

A Bot API 10.3 limita cada Rich Message a 32.768 caracteres UTF-8, 500 blocos, 16 níveis de aninhamento, 50 anexos de mídia e 20 colunas por tabela. A implementação usa uma margem inferior de tamanho e divide em páginas. Um limite por mensagem não significa que o Telegram conceda campos que não foram retornados pelas APIs.

Em falhas temporárias **com resposta do Telegram**, leituras Bot API idempotentes repetem HTTP 429 e 5xx até cinco tentativas; operações de envio repetem HTTP 429, respeitando `parameters.retry_after` quando fornecido. Erros de transporte ambíguos não são repetidos automaticamente para evitar duplicar mensagens. Cada página rica é tentada mesmo se outra falhar; se o conjunto rico não for concluído, o HTML paginado também é tentado. A coleta de arquivos Markdown é independente do sucesso das páginas de texto e continua tentando as partes restantes quando uma delas é recusada.

Na exportação completa, o envio e a cobertura são avaliados separadamente. Se páginas e anexos foram enviados, mas uma consulta não retornou dados disponíveis, o bot informa **Resultado parcial enviado**; se partes foram recusadas pela Bot API, informa **Entrega incompleta**. O estado parcial também é registrado quando alguma mídia não pôde ser incluída. A confirmação de envio não prova que o conteúdo recebido foi inspecionado nem que todos os métodos de leitura relevantes estão cobertos. Caso contrário, tenta comunicar **Entrega incompleta**, com totais confirmados, e termina com código de falha. O resultado pode ser parcialmente entregue por limites de tempo, conectividade, permissões ou privacidade: não existe garantia técnica de entrega ilimitada.

A sessão MTProto do worker é temporária; o Telegram controla `access_hash`, FloodWait e o conjunto de dados permitido à identidade autenticada. `GetFullChatRequest` foi acrescentado para grupos básicos nos quais o bot tenha acesso.

Fontes: https://core.telegram.org/bots/api#rich-message-formatting-options ; https://core.telegram.org/bots/api#responseparameters ; https://core.telegram.org/bots/faq ; https://core.telegram.org/method/messages.getFullChat ; https://core.telegram.org/api/peers .

## Arquitetura

| Etapa | Código | API usada |
|---|---|---|
| Receber mensagem | tgcloud/handlers/message.js | Telegram Serverless Update Message |
| Seletores e callback | tgcloud/lib/envio.js, tgcloud/handlers/callback_query.js | Telegram Bot API |
| Interpretar referência | tgcloud/lib/entrada.js | Convenção local validada |
| Limite de disparo | tgcloud/lib/limite.js | Banco Serverless |
| Disparar worker | tgcloud/lib/despacho.js | GitHub workflow_dispatch |
| Resolver identidade e campos detalhados | scripts/resolver.py | Telegram MTProto via Telethon e Bot API |
| Gerar Rich Messages e .md | scripts/resolver.py, scripts/ficha_completa.py | sendRichMessage, editMessageText, sendDocument |

O limite atual é de **2 consultas por chat e 6 globalmente em 60 segundos**. O workflow usa sessão MTProto temporária, sem cache persistente de peers. Sua consulta pode falhar por permissões, ausência de access_hash, privacidade ou rate limit.

## Garantia de confirmação na entrega

No resolver Python, cada envio com `sendRichMessage`, `sendMessage`, `sendPhoto` ou `sendDocument` é considerado confirmado somente se a resposta oficial retornar `ok=true` **e um objeto de mensagem com `message_id`**. Isso comprova aceitação do servidor Telegram, mas não que o cliente já exibiu ou que a pessoa abriu a mensagem.

Quando houver falha de uma parte, o bot continua tentando as outras mensagens e o arquivo Markdown, contabilizando separadamente partes ricas, páginas HTML de compatibilidade e documentos enviados. Se faltar um componente obrigatório, comunica **Entrega incompleta** e não registra o sucesso integral. A legenda de cada arquivo Markdown contém o SHA-256 dos bytes do próprio anexo, para conferência de integridade.

O worker respeita `parameters.retry_after` em erros 429. Não repete automaticamente respostas 5xx de métodos que criam mensagens: sem identificador de idempotência fornecido pela API, repetir uma operação de resultado ambíguo poderia gerar mensagens duplicadas. O limite do job é de 30 minutos para acomodar esperas e páginas extensas. Isso é um orçamento de execução, não garantia de sucesso ilimitado.

Fonte: https://core.telegram.org/bots/api#making-requests , https://core.telegram.org/bots/api#responseparameters , https://core.telegram.org/bots/api#senddocument , https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax .

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
