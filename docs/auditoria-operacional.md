# Auditoria operacional integral — 2026-11-02

## Critério

Este documento diferencia **fonte normativa**, **código inspecionado**, **verificação estática/CI**, **publicação** e **execução real**. Documentos históricos não são baseline normativo. A ausência de testes autorais no repositório decorre da decisão expressa do proprietário, não demonstração de qualidade por si só.

Revisão-base: main no commit 0bef0e38ebeec2eaa18bb73b8170d99d6f5dba60. As complementações atuais em branch estão registradas abaixo e ainda requerem execução real.

### Fontes oficiais prioritárias

- Bot API 10.3: https://core.telegram.org/bots/api e https://core.telegram.org/bots/api-changelog
- Peer database e limites de access_hash: https://core.telegram.org/api/peers
- Resolver username: https://core.telegram.org/method/contacts.resolveUsername e https://core.telegram.org/type/contacts.ResolvedPeer
- Telegram Serverless: https://core.telegram.org/bots/serverless e cópia do projeto docs/Serverless-OFFICIAL
- GitHub workflow_dispatch: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
- Interfaces SDK usadas: docs/tgcloud-sdk.md, confrontadas com versão instalada; não criar APIs por analogia

## Inventário dos executáveis e fluxos

| Arquivos | O que executam | Conclusão |
|---|---|---|
| tgcloud/handlers/message.js | /start, /help, referências recebidas no privado, encaminhamentos, contatos, menções | IMPLEMENTADO; dados compartilhados podem ser substituídos pela ficha |
| tgcloud/handlers/callback_query.js | Valida comando r/f e mesma pessoa do chat privado; responde callback | IMPLEMENTADO; botão real deve ser validado por execução |
| tgcloud/handlers/inline_query.js | Produz resultado inline que orienta ao privado | IMPLEMENTADO, sem resolução MTProto no chat externo |
| tgcloud/lib/entrada.js | Valida @username, ID, ID @username e callback_data tipado | IMPLEMENTADO; separador ID|username obsoleto |
| tgcloud/lib/consulta.js | Controle de limite, envio/edição de cartão, dispatch | IMPLEMENTADO; erro da Bot API pode impedir entrega |
| tgcloud/lib/despacho.js | Chama GitHub workflow_dispatch com alvo e expected_id separados | IMPLEMENTADO; inputs não são canal privado |
| tgcloud/lib/limite.js, tgcloud/schema.js | Janela 60 s, 2 por chat, 6 globais, tabela disparos | IMPLEMENTADO; migração via workflow deploy |
| tgcloud/lib/cartao.js | Apresentação de cartão e botão Atualizar | CORRIGIDO: botão no cartão de erro recebe entrada tipada |
| tgcloud/lib/envio.js | Seletores oficiais, sendRichMessage/editMessageText e fallback clássico | IMPLEMENTADO; disponibilidade depende da Bot API |
| tgcloud/lib/relatorio.js | Ajuda, erros, modo inline e avisos | IMPLEMENTADO; não é fonte de dados do Telegram |
| tgcloud/lib/segredos.js | Placeholders vazios versionados | VERIFICAR em cada CI; token real injetado no deploy |
| scripts/resolver.py | Telethon, identidade, enriquecimento, foto, Rich Messages e sendDocument | IMPLEMENTADO; métodos podem recusar por privacidade/acesso |
| scripts/ficha_completa.py | Paginação rica, fallback HTML e arquivos .md UTF-8 | IMPLEMENTADO; conferir limite real e recebimento pelo Telegram |
| scripts/check.sh, .github/workflows/ci.yml | Sintaxe JavaScript/Python, placeholder de secrets | Não são testes de integração funcional |
| .github/workflows/deploy.yml | fetch, status, migrate, push, webhook, healthcheck | Deploy pode migrar o esquema; healthcheck não executa Telethon |
| .github/workflows/resolver.yml | Consulta MTProto ou healthcheck sem consulta | CORRIGIDO: descrição do input não aceita ID|username |
| tgcloud.jsonc, package.json, package-lock.json | Configuração e dependências | Conferir versões em CI |
| .env.example, .gitignore, SECURITY.md | Configurações e orientações de segredo | Não versionar tokens/IDs privados |
| AGENTS.md, README.md, docs/launch-checklist.md | Orientações operacionais | REVISADOS para não afirmar capacidades inexistentes |
| docs/Serverless-OFFICIAL, docs/tgcloud-sdk.md, docs/fontes-oficiais.md | Documentação referenciada | Fontes a confrontar com páginas oficiais atuais |
| docs/registro.md | Evidência histórica, inclusive erros antigos | Não substituir especificações atuais |

## Correções comprováveis da auditoria

1. **Cartão de falha sem botão funcional:** tgcloud/lib/cartao.js passava entrada.alvo (não mais existente) em vez do objeto entrada ao gerador. Corrigido o tipo do argumento.
2. **Código legado em Python:** texto_simples_consolidado, ficha_final, relatorio e auxiliares inativos conservavam truncamentos e montagens antigas que não eram usados no fluxo final. Foram eliminados para reduzir ambiguidade. As funções atualmente em uso permanecem em ficha_completa.py, ficha_falha e na rotina de envio principal.
3. **Erro de expected_id inválido:** rotina anterior retornava status não zero sem criar a ficha de erro específica; agora entra no tratamento normal de falha e tenta informar o usuário.
4. **Workflow com descrição desatualizada:** removida referência obsoleta a ID|username; expected_id continua input independente de alvo.
5. **AGENTS.md contraditório:** instruções anteriores tratavam deploy/Actions como prova real, descreviam seletor por nome antigo, não distinguiam migração de push e misturavam fontes de terceiros às normativas. Agora distingue papel de cada fonte e execução.
6. **README/checklist contraditórios:** versões antigas diziam que os dados compartilhados eram sempre preservados; que o limite era 1 por chat; que testes Python já excluídos ainda eram executados; e que todos os campos do MTProto eram extraídos. A documentação atual descreve os comportamentos realmente codificados.
7. **SECURITY.md incorreto:** o projeto era descrito como privado. O repositório foi confirmado público em 2026-11-02. A visibilidade do workflow_dispatch e dos logs impõe risco de exposição das consultas.

## Segurança residual e limites não solucionados

- O dispatch do GitHub recebe alvo, expected_id, chat, message_id e origem_id como inputs; o repositório é público. Não afirmar privacidade dos identificadores pesquisados. Resolver exige redesenho do transporte, não apenas mascarar logs.
- A Bot API e MTProto não garantem qualquer informação adicional para um ID desconhecido. O access_hash é vinculado ao contexto e pode ser necessário.
- O seletor fornece metadados oficiais, mas não concede necessariamente acesso MTProto e o worker não persiste esses metadados em separado até a ficha final.
- Não há mecanismo para provar que o usuário recebeu/abriu um documento apenas porque sendDocument retornou ok; isso confirma aceitação pelo servidor. A inspeção do chat dá evidência adicional.
- Falhas após entrega parcial de páginas ricas podem produzir mensagens complementares pelo fallback. Esse caso não foi reproduzido em runtime real nesta auditoria.
- O menu / do BotFather não é configurado via setMyCommands no repositório; os handlers reconhecem /start e /help independentemente do menu.

## Verificação sem testes autorais

Por decisão expressa do proprietário, não são criados testes escritos pelo próprio autor. A rotina automatizada faz checagens sintáticas e de placeholders. A avaliação funcional deve ser conduzida no Telegram, com observação dos resultados e execução do workflow resolver sem healthcheck.

| Prova | O que é permitido concluir |
|---|---|
| CI verde | Código compilável e placeholders preservados |
| Deploy verde | Publicação e migração declaradas concluídas |
| Healthcheck verde | workflow_dispatch aceito; sem Telethon |
| Workflow MTProto não-healthcheck verde | O processo executou; analisar linhas de envio e resolução |
| Bot API retornou ok | Servidor aceitou a operação correspondente |
| Mensagem e .md vistos no chat | Evidência de ponta a ponta para aquele caso concreto |

## Fontes históricas de execução

- 41531172969 e 41531283280: consultas reais em modo resumo; os logs registraram entidade de bot, campos adicionais e foto incorporada, anteriores a esta auditoria.
- 41533495539: healthcheck, sem execução do resolver MTProto.
- O fluxo de Exportação completa (Markdown + JSONL + mídia) e as correções desta auditoria **não devem ser marcados VERIFICADO** sem clique real, workflow com MODO=completo, recebimento e inspeção dos anexos no Telegram.

## Sequência sugerida para validação real

1. /start e /help no privado com seletor visível.
2. @username público de teste; comprovar ID, nome, Rich Message e foto quando houver.
3. ID @username correspondente; conferir comparação exata. Em seguida testar ID divergente.
4. Atualizar a ficha pelo botão novo; observar o mesmo message_id.
5. Exportação completa; confirmar workflow com MODO=completo, páginas ricas, Markdown, JSONL e ZIP no Telegram; conferir hashes e abrir cada anexo.
6. Provocar erro de referência e observar botão Atualizar na ficha de erro.
7. Conferir login e permissões do Telegram e erros de Bot API, sem divulgar dados pessoais nos logs ou issues.

Esta auditoria não autoriza inferir novos campos do Telegram nem contornar restrições de privacidade.

## Revisão de entrega integral — 2026-11-02

Foi removido o corte fixo de nove campos da apresentação usual, mantendo paginação integral. O método MTProto `messages.getFullChat` foi introduzido para grupos básicos acessíveis. O transporte da Bot API respeita `retry_after`; somente leituras idempotentes repetem respostas 429 e 5xx, e erros ambíguos de rede não são repetidos automaticamente. Se a Rich Message for recusada, há tentativa de envio paginado em HTML; os arquivos Markdown são tentados independentemente da formatação das mensagens. O sucesso exige todas as partes obrigatórias aceitas pela Bot API. Ainda é necessário demonstrar esse comportamento na execução real posterior ao commit, especialmente o botão de Markdown.

## Revisão de confirmação da entrega — 2026-11-02

**IMPLEMENTADO:** exigir o `result.message_id` retornado pelo servidor Bot API nos métodos de envio/edição em chat, adicionar hash SHA-256 à legenda de cada Markdown, contar partes de Rich Messages, HTML e anexos separadamente, respeitar `retry_after` em 429 sem repetir 5xx de resultado de envio ambíguo e ampliar timeout do job para 30 minutos. **NÃO VERIFICADO EM PRODUÇÃO:** falhas reais de todas as modalidades e recebimento do arquivo após esta revisão. CI e healthcheck são insuficientes. A skill Partners selecionada pela pessoa governa esta evolução; as instruções locais divergentes foram ajustadas em `AGENTS.md`. Referências técnicas: https://core.telegram.org/bots/api, https://core.telegram.org/api e https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax.


## Escopo ativo decidido em 2026-11-02

A meta é ampliar o Infocard para entregar a cobertura máxima e verificável dos dados de leitura acessíveis às sessões Bot API e MTProto do bot, em vez de limitar o produto aos campos já mapeados. A autenticação permanece como bot. Os métodos `messages.getHistory` e `stories.getPeerStories` são exclusivos de contas de usuário; `channels.getParticipants` pode exigir administração. A cobertura técnica precisa ser inventariada campo a campo e método a método conforme a layer oficial e o Telethon instalado. Não alegar conclusão até que os dados retornados, a paginação e a entrega recebida no Telegram sejam confirmados. Ver [docs/partners-mtproto-coverage.md](partners-mtproto-coverage.md).


## Correção de estados na exportação completa — 2026-11-02

O bot separa a entrega de anexos da cobertura dos dados. Quando o Telegram recebeu as partes montadas, mas um método não retornou dados, a resposta é “Resultado parcial enviado”; “Entrega incompleta” fica reservado a páginas/anexos sem confirmação. A lacuna continua explícita no relatório e o resultado não é tratado como integral. A regra do proprietário contra testes escritos pelo próprio implementador foi preservada, pois não conflitava com Partners.


## Ampliação da cobertura de leitura — branch codex/bot-api-profile-coverage

**IMPLEMENTADO NO CÓDIGO:** a exportação completa tenta leituras Bot API adicionais por entidade: `getChat`; para usuários, pagina fotos e áudios de perfil e obtém até 20 mensagens do chat pessoal indicado no perfil; para grupos e canais, obtém administradores e contagem. As respostas completas e falhas de método são incluídas no JSONL junto às respostas MTProto. Arquivos compatíveis são baixados por `getFile`, deduplicados e agrupados nos ZIPs; downloads Bot API acima de 20 MiB são marcados indisponíveis. Retentativas 5xx ficam restritas a leituras idempotentes.

**REVISADO:** README, AGENTS e matriz de cobertura passaram a descrever as duas APIs. Foram removidas afirmações normativas antigas que excluíam `getChat` e campos MTProto repetidos no relatório.

**NÃO VERIFICADO:** execução real com o bot e inspeção do JSONL, campos obtidos, mídias e anexos recebidos. Um endpoint que falhar em uma entidade fica registrado como falha/limite e não prova inexistência do dado.
