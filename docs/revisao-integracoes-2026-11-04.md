# Revisão das integrações — 2026-11-04

Base: `main`, commit `1d3433a5c2cc7eb73fd6d9294b08eced23cb2fab`.

## IMPLEMENTADO

- Remoção de README.md, AGENTS.md e SECURITY.md, conforme pedido do proprietário.
- Autenticação de bot com validação da configuração antes de conectar, sessão somente em memória e conferência do ID e do tipo da conta autenticada. O cliente não recebe updates e a espera por FloodWait fica sob controle explícito do worker.
- IDs fora do intervalo são rejeitados antes do fallback. Erros de autenticação e FloodWait esgotado não viram falha de resolução por falta de contexto.
- Resolução de username distingue canais de grupos mesmo quando o ID interno coincide. ChatEmpty não confirma uma entidade acessível.
- getChat no fallback exige resultado com ID e tipo válidos. A coleta subsequente usa o ID estável, evitando consultar outro peer se o username mudar. A resposta já obtida no fallback é reutilizada.
- Construtores de entrada usam o hash completo quando disponível e hash zero para entidades min ou sem hash, no contexto autenticado de bot.
- O cliente HTTP rejeita JSON sem o envelope esperado, confirma mensagens apenas com message_id inteiro positivo e respeita retry_after integralmente. Quando a espera ultrapassa o orçamento, retorna a falha sem antecipar a repetição. Escritas não repetem 5xx automaticamente.
- Logs de exceções JavaScript deixam de imprimir o objeto completo. Erros inesperados e respostas brutas do GitHub deixam de ser apresentados ao usuário. A notificação de falha do workflow descarta o corpo da resposta Telegram, sem imprimir a mensagem e o chat retornados.
- Deploy manual limitado à main. Checagens locais e validação do token de dispatch antecedem migração e publicação. O healthcheck confirma somente aceitação do dispatch.
- CI com Node 22/Python 3.12 e Node 24/Python 3.13, instalação do Telethon fixado e inspeção das importações e assinaturas executadas pelo resolver. Todos os módulos Python entram na checagem sintática.

Permanecem os seletores, referências compartilhadas, comandos, callbacks, modo inline, coleta MTProto/Bot API, páginas ricas, fallback HTML, arquivos Markdown/JSONL e pacotes de mídia. Esta revisão corrige as rotas descritas; não comprova cobertura exaustiva de todos os métodos oficiais.

## Fontes oficiais consultadas

| Referência | Aplicação nesta revisão |
|---|---|
| [Telegram Bot API](https://core.telegram.org/bots/api) | Envelope de resposta, getChat, identificadores, mensagens e erros |
| [ResponseParameters](https://core.telegram.org/bots/api#responseparameters) | retry_after informa a espera mínima antes de repetir |
| [MTProto](https://core.telegram.org/mtproto) | Separação entre transporte, autorização e chamadas RPC |
| [Bots no MTProto](https://core.telegram.org/api/bots) e [auth.importBotAuthorization](https://core.telegram.org/method/auth.importBotAuthorization) | Token de bot, API ID/hash e autorização |
| [Peer database](https://core.telegram.org/api/peers#access-hash) | Hash completo, min e zero para bots |
| [contacts.resolveUsername](https://core.telegram.org/method/contacts.resolveUsername) | Associação entre peer retornado e entidade correspondente |
| [Telethon: entidades](https://docs.telethon.dev/en/stable/concepts/entities.html) | Entidades, cache e construtores Input* |
| [Telethon: cliente](https://docs.telethon.dev/en/stable/modules/client.html) | start, get_me, receive_updates e flood_sleep_threshold |
| [Assinaturas no GitHub](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification) | Exigir confirmação de verification.verified pelo GitHub |

A compatibilidade executável foi conferida contra Telethon 1.45.0, layer 229. A documentação web consultada pode ter um layer diferente; a checagem de assinaturas não prova que todos os métodos serão autorizados pelo servidor.

## VERIFICADO localmente

| Verificação | Resultado observado |
|---|---|
| npm ci --ignore-scripts | 22 pacotes instalados; lockfile preservado |
| npm run check, Node 24.22.1 e 22.23.4 / Python 3.12.14 | Passou: sintaxe JavaScript/Python e placeholders vazios |
| Python 3.13.5: compileall e compatibility.py | Passou |
| Python 3.12.14: compatibility.py | Passou: 58 importações, 52 assinaturas e importação do resolver sem rede |
| Sondagens Python com respostas simuladas | 33 verificações passaram: envelope inválido, confirmação de mensagem, falha de transporte, 429/espera, escrita sem repetição de 503, hashes min/completos, tipo de peer, IDs inválidos, getChat divergente, erro de autenticação, ChatEmpty e configuração ausente |
| Sondagens JavaScript | 17 verificações passaram: entrada, roundtrip dos callbacks r/f, rejeição de dados inválidos e mensagem de erro sem conteúdo sensível |
| actionlint 1.7.12 | Todos os workflows passaram |
| tgcloud --version | CLI 0.2.0 executada |
| git diff --check | Passou |

As sondagens exploratórias foram executadas com dados sintéticos e não constituem uma suíte de regressão persistida. Uma primeira execução assíncrona foi interrompida durante o encerramento do executor de threads local; a rodada concluída substituiu a delegação para thread por execução direta nas sondagens simuladas. A concorrência real não foi validada por essas sondagens.

## Limites e próximos critérios de aceitação

Não há credenciais Telegram ou TGCloud configuradas neste ambiente. Não foram executados login real, consultas autorizadas, envio de mensagens, download real de mídia, migração ou deploy. A CI remota e a verificação de assinatura são conferidas separadamente na entrega do PR; não são presumidas pelos resultados locais acima.

Antes de afirmar funcionamento em produção, executar uma consulta autorizada, conferir a entidade e o conteúdo entregue no Telegram e observar as recusas/parcialidades registradas. Não publicar tokens, sessões nem credenciais para realizar essa validação. O transporte atual por workflow_dispatch em repositório público continua expondo metadados das entradas; esta revisão não altera essa arquitetura.

## DECISÃO

Entregar as mudanças por PR para main, mantendo as regras ativas de assinaturas obrigatórias, proteção contra exclusão de branches e contra force-push. Não executar merge nem deploy como parte desta revisão.
