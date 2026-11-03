# Infocard — Telegram Serverless + APIs do Telegram

O Infocard recebe uma referência no privado e consulta MTProto e Bot API para compor uma ficha completa. A evolução do código segue a capacidade descrita nas fontes oficiais vigentes; o código existente mostra apenas o que já foi implementado e não define o limite do que deve ser coletado.

## Regra de evolução

Use a documentação oficial vigente da Bot API e do MTProto como referência normativa para evoluir o Infocard. Não derive o escopo do código atual, de commits anteriores, de comentários ou de exemplos de terceiros. Consulte o código somente para localizar o comportamento atual e implementar a diferença em relação às APIs oficiais.

Para cada tipo de peer, identifique nos métodos oficiais os dados retornados, os parâmetros, a paginação, o suporte a bots e os contextos necessários. Implemente as leituras aplicáveis, preserve as respostas completas e entregue os dados coletados em páginas e anexos. Uma chamada ausente do código é trabalho de evolução; não é motivo para excluir uma capacidade que a API documenta.

Não classifique uma leitura como indisponível antes de executá-la. Use fallback oficial para IDs numéricos e os construtores com hash zero nas chamadas MTProto de bot quando a documentação os prevê. Registre recusas com o método e a resposta real. Exclua um método somente quando a documentação oficial vigente declarar a incompatibilidade ou quando faltar o contexto/identificador exigido pela própria API.

Fontes normativas: [Telegram Bot API](https://core.telegram.org/bots/api), [Bot API changelog](https://core.telegram.org/bots/api-changelog), [MTProto peer database](https://core.telegram.org/api/peers), [schema MTProto atual](https://core.telegram.org/schema) e a página oficial de cada método usado.

## Uso

| Entrada ou ação | Resultado |
|---|---|
| /start | Mensagem de ajuda com teclado de seleção |
| /help | Mesma ajuda |
| @username | Resolve pelo método oficial contacts.resolveUsername |
| ID numérico | Tenta MTProto; se necessário consulta `getChat` e prossegue com os métodos de bot oficialmente compatíveis usando hash zero |
| ID @username | Resolve username e exige que o ID retornado coincida |
| Escolher usuário/canal/grupo | Recebe o ID e dados opcionais fornecidos pelo seletor oficial |
| Encaminhar mensagem, contato, menção | Usa somente as referências disponibilizadas pelo Telegram |
| Atualizar | Faz nova busca e edita o cartão, quando possível |
| Consulta privada | Faz a coleta completa automaticamente e envia páginas legíveis, Markdown, JSONL bruto e arquivos de mídia ZIP quando acessíveis |
| Modo inline | Exibe convite para pesquisar no privado; não lê perfis no outro chat |

Não existem comandos /buscar, /completo ou /download. O repositório não configura setMyCommands; o menu do BotFather pode divergir dos handlers.

O formato ID @username é convenção de entrada **deste bot**. Não utilizar o antigo separador ID|username. O callback_data é um campo definido pelo aplicativo sob o limite da Bot API (1 a 64 bytes). O TGCloud interpreta o callback separadamente do texto e passa alvo e expected_id como inputs distintos ao workflow. O worker resolve @username por contacts.resolveUsername e compara o peer a expected_id quando informado.

## Resultado

1. **Ficha de andamento:** cartão rico do Telegram com identificação de consulta e status.
2. **Resultado na tela:** identificação e todos os campos das respostas efetivamente coletadas, em tantas Rich Messages quanto necessárias; a ficha curta fica apenas como andamento. O JSONL e o Markdown preservam também dados sem mapeamento visual. O exportador percorre respostas da Bot API em busca de anexos aninhados com `file_id`, deduplica arquivos e registra os que excedem o limite de download.
3. **Relatório completo:** cada busca privada gera as páginas ricas e os anexos Markdown, JSONL e ZIP de mídia quando disponíveis. A ficha inicial é apenas o estado de andamento da coleta.
4. **Falhas:** mensagem de erro e possibilidade de nova pesquisa. Quando o Telegram/GitHub estiver indisponível, a notificação não é garantida.

**A exportação completa tenta leituras adicionais pelas duas APIs.** Para usuários, chama `getChat`, `getUserProfilePhotos`, `getUserProfileAudios` e `getUserPersonalChatMessages`; para grupos e canais, chama `getChat`, `getChatAdministrators` e `getChatMemberCount`, além dos filtros de participantes recentes, administradores, bots, membros restritos e banidos via MTProto em canais/supergrupos. Se MTProto não resolver um ID numérico, tenta `getChat`; mesmo se `getChat` também recusar, continua as leituras independentes que aceitam o ID numérico, usando o tipo de peer inferido apenas para escolher chamadas compatíveis. Para peer de canal, a Bot API não confirma se é canal ou supergrupo. As respostas bem-sucedidas acrescentam dados; erros são preservados como erros e não são tratados como dados, sucesso ou prova de inexistência. Em grupos básicos, usa a lista de participantes que `messages.getFullChat` retornou para tentar `getChatMember`; em todos os grupos/canais registra o status do próprio bot (`getMe` + `getChatMember`). Em canais/supergrupos, consulta também o próprio status por `channels.getParticipant` via MTProto, além dos boosts Bot API dos participantes obtidos, sujeitos a direitos de administrador. Presentes MTProto são consultados para usuário, canal/supergrupo e grupo básico; no último caso a chamada usa `InputPeerChat` e a resposta do servidor confirma se esse peer é aceito. Se `ChatFullInfo` indicar um chat pessoal, pai ou vinculado, também tenta obter seus dados completos com `getChat`. Respostas Bot API, inclusive erros de acesso, e conteúdo das mensagens fixadas recuperadas por ID via MTProto vão para o JSONL. Para usuários, também pagina `messages.getPersonalChannelHistory` quando a API retorna mensagens do canal pessoal associado ao perfil; esse método bot-only acessa esse canal pessoal, não o histórico geral de conversas. A exportação consulta conjuntos de stickers referenciados, emojis personalizados retornados em perfis/mensagens e, em fóruns, os stickers permitidos para ícones de tópico; tenta incluir os arquivos que as APIs deixam baixar. Consulta presentes do usuário/chat pela Bot API e por MTProto, além dos catálogos globais. Para canais e supergrupos, consulta detalhes de boosts por usuário somente quando a Bot API identifica participantes com boosts. Documentos anexados a atributos de presentes colecionáveis também são percorridos para o ZIP de mídia. Ausência de um campo ou erro de permissão não prova que os dados não existam. MTProto continua limitado à sessão de bot e às permissões concedidas pelo Telegram. Histórico geral de chats não é incluído; a coleta não chama o método user-only `stories.getPeerStories`, mas preserva stories caso venham dentro da resposta bot-callable de perfil completo. Log administrativo e lista completa de tópicos que exigem sessão de usuário permanecem fora desta autenticação.

Os dados opcionais compartilhados no seletor podem ser mostrados no cartão inicial, mas não são preservados em armazenamento temporário independente; uma edição posterior pode substituí-los. O relatório registra aquilo que cada resposta do Telegram confirmou.

## Entrega integral e tolerância a falhas (2026-11-02)

Cada busca privada inicia a coleta completa por padrão; não depende do botão de exportação. A ficha curta aparece como estado de andamento. O resultado imprime cada campo de cada resposta coletada em Rich Messages paginadas, com caminho e valor, e envia anexos Markdown, JSONL com respostas MTProto e Bot API e pacotes ZIP de mídia acessível. O modo resumido permanece disponível apenas para disparos manuais explicitamente definidos como `MODO=resumo`. A confirmação do envio não comprova que todos os dados possíveis foram retornados nem substitui uma consulta real de ponta a ponta. A entrega integral exige que todas as páginas ricas e anexos previstos sejam aceitos; se a Bot API só aceitar o fallback HTML, o conteúdo ainda é enviado, mas o bot sinaliza entrega incompleta.

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

O limite atual é de **2 consultas por chat e 6 globalmente em 60 segundos**. O workflow usa sessão MTProto temporária, sem cache persistente de peers. Para bots, peers sem hash conhecido usam o `access_hash=0` previsto na documentação; a chamada ainda pode falhar por permissões, privacidade ou rate limit, e a resposta do Telegram é registrada.

## Garantia de confirmação na entrega

No resolver Python, cada envio com `sendRichMessage`, `sendMessage`, `sendPhoto` ou `sendDocument` é considerado confirmado somente se a resposta oficial retornar `ok=true` **e um objeto de mensagem com `message_id`**. Isso comprova aceitação do servidor Telegram, mas não que o cliente já exibiu ou que a pessoa abriu a mensagem.

Quando houver falha de uma parte, o bot continua tentando as outras mensagens e o arquivo Markdown, contabilizando separadamente partes ricas, páginas HTML de compatibilidade e documentos enviados. Se faltar um componente obrigatório, comunica **Entrega incompleta** e não registra o sucesso integral. A legenda de cada arquivo Markdown contém o SHA-256 dos bytes do próprio anexo, para conferência de integridade.

O worker respeita `parameters.retry_after` em erros 429. Não repete automaticamente respostas 5xx de métodos que criam mensagens: sem identificador de idempotência fornecido pela API, repetir uma operação de resultado ambíguo poderia gerar mensagens duplicadas. O limite do job é de até 6 horas para acomodar consultas por participante, esperas e páginas extensas. Isso segue o máximo do runner hospedado e continua sendo um limite, não garantia de execução ilimitada.

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

Documentação oficial vigente determina as capacidades disponíveis. O código executável comprova somente as capacidades implementadas até aquele commit; toda lacuna oficial elegível deve avançar para implementação e execução real.
