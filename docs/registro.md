# Implementado — 2026-11-02: entrega integral, MTProto e Bot API 10.3

**IMPLEMENTADO NO CÓDIGO:** retirada da abreviação dos nove campos no resultado normal, ampliação de campos opcionais oficiais de usuários/bots/canais, suporte ao método `messages.getFullChat` para grupos básicos e entrega rica paginada com fallback HTML. Transporte trata `retry_after`, tenta partes subsequentes mesmo após recusa parcial e envia o Markdown em uma etapa independente. Relatório só é classificado completo quando o conjunto obrigatório foi aceito pela Bot API. Sem testes autorais nem comentários/docstrings adicionados ao código, conforme AGENTS.md.

**NÃO COMPROVADO AO VIVO AINDA:** os novos campos e todo o fluxo de falhas parciais. Provar com execução MTProto não-healthcheck e inspeção das mensagens e do arquivo no Telegram.

---

# Auditoria corretiva — 2026-11-02

**IMPLEMENTADO:** correção do botão de cartão de erro, remoção de código de formatação obsoleto e seus truncamentos, correção da mensagem de ID esperado inválido e atualização do texto do workflow. **REVISADO:** AGENTS.md, README.md, SECURITY.md e docs/launch-checklist.md com inventário em docs/auditoria-operacional.md. Preservadas as decisões sem comentários em código e sem testes autorais.

**VERIFICADO POR LEITURA DE CÓDIGO:** a base contém somente /start e /help como comandos com barra, seletor oficial para usuário/canal/grupo, parser tipado de callback, MTProto por contacts.resolveUsername e relatório integral por sendDocument. Repositório confirmado público; GitHub Actions recebe metadados de consulta. A checagem sintática/CI ainda não é prova do comportamento real.

**PENDENTE:** registrar CI/deploy deste commit e provar no chat o callback Atualizar e Completo + Markdown. Ver docs/auditoria-operacional.md.

---

# IMPLEMENTADO — 2026-11-02: remover a referência caseira `ID|username`

**Causa verificada no código:** uma representação interna de referência (`ID|username`) era colocada no payload dos botões e devolvida ao parser de entrada do usuário, que aceitava `ID @username` mas não o separador interno. A mensagem "Não foi possível interpretar a referência" vinha do próprio parser e não do Telegram.

**Correção implementada:** callback_data tipado e validado (`r/f:u:ID:username`, `r/f:n:username`, `r/f:i:ID`) com limite 64 bytes; parser de callback independente; `alvo` e `expected_id` separados em workflow_dispatch; consulta oficial por `contacts.resolveUsername` com comparação do peer antes de produzir o relatório; texto `ID @username` reservado à interface do usuário. Payloads legados são rejeitados com indicação de nova busca.

**DECISÃO do AGENTS.md preservada:** não escrever comentários/docstrings no código e não manter testes escritos pelo autor. Removido o teste Python autoral, desligada a chamada a `unittest` do check, preservadas verificações de sintaxe e placeholders. Documentação em Markdown não se confunde com comentários dentro de código.

**Fontes oficiais:** https://core.telegram.org/bots/api#callbackquery; https://core.telegram.org/method/contacts.resolveUsername; https://core.telegram.org/type/contacts.ResolvedPeer; https://core.telegram.org/api/peers; https://core.telegram.org/bots/api#senddocument.

**Estado atual:** implementação publicada apenas após CI/deploy, sem pressupor que o callback real tenha sido testado. Para marcar VERIFICADO é necessário obter evidência de execução MTProto e recebimento da ficha e documento no chat; o healthcheck do GitHub é insuficiente. A ausência de erro em testes anteriores não é evidência de que o novo payload está correto.

---

# AUDITORIA — 2026-11-02: fonte oficial, comentários e fidelidade dos arquivos

**Referência normativa:** Bot API em https://core.telegram.org/bots/api e banco de peers MTProto em https://core.telegram.org/api/peers. O código antigo é usado apenas para regressões; uma execução verde sem consulta e entrega reais não comprova funcionamento do botão.

**VERIFICADO (antes desta correção):** CI passou seis testes de paginação/Markdown e o deploy publicou os módulos; a execução 41529276863, anterior ao botão de download, executou Telethon, identificou um bot, editou a ficha e registrou foto incorporada. A execução 41530877958 foi apenas healthcheck (Telethon ignorado). **NÃO VERIFICADO:** clique no botão `f:`, reconsulta com `modo=completo` e entrega de `sendDocument` ao Telegram após o último deploy.

**ERRO IDENTIFICADO:** o fallback HTML fazia novo escape em texto já escapado quando o valor era muito longo, modificando o conteúdo exibido. A divisão do `.md` acima do limite preservava bytes quando concatenados, mas podia produzir anexos separados com cercas Markdown incompletas. A correção prepara cada parte como documento Markdown válido e divide valores por caracteres UTF-8, sem cortes de dados. Verificação simulada por testes Python não equivale a entrega Bot API real.

**CONFLITO COM DECISÕES EXISTENTES:** `AGENTS.md` contém "Sem comentários no código" e "Sem testes escritos por quem escreveu o código". O projeto já inclui comentários/docstrings em `scripts/ficha_completa.py` e testes `scripts/test_ficha_completa.py`. Não há registro de mudança da decisão do dono. A presença desses arquivos não é evidência de autorização. Não modificar `AGENTS.md` sem confirmação expressa do dono.

**PRÓXIMA PROVA DE PONTA A PONTA:** consultar perfil conhecido; ver o resumo; clicar `Completo + Markdown`; confirmar workflow não-healthcheck com `MODO=completo`; confirmar logs de `sendRichMessage` e `sendDocument` com respostas `ok=true`; conferir recebimento e conteúdo do(s) anexo(s) no chat. Usar um perfil público de teste e não exibir dados particulares nos logs.

---

# Atualização — 2026-11-02: opção para receber relatório completo e Markdown

Foi adicionado callback `f:alvo` ao cartão de resumo, opção de workflow `modo=completo`, nova coleta MTProto, envio paginado do relatório completo e anexos `.md` por `sendDocument`, com preservação de UTF-8 e de valores sem truncamento. A ficha completa é enviada em mensagens separadas, sem sobrescrever a mensagem original de resumo. O botão também existe no fallback HTML. Rate limit por chat ajustado para dois disparos por minuto, preservando o limite global de seis. O módulo Python agora conecta efetivamente `rich_pages` e `basic_pages` ao resolver. **Implementado, sujeito a CI/deploy e teste real de callback/anexo**.

---

# Implementação — 2026-11-02: paginação integral do Infocard

Foi criado `scripts/ficha_completa.py`, que agrupa todos os campos extraídos em páginas de Rich Messages, com continuidade numerada e margem para os limites oficiais. O primeiro cartão é editado; eventuais páginas adicionais são enviadas como respostas, sem perder dados por exceder 13 linhas, 4.096 caracteres da mensagem clássica, ou tamanhos individuais de campo. O fallback HTML clássico também pagina os dados e tem testes próprios em `scripts/test_ficha_completa.py`. Foram expostos novos campos condicionais de estrelas, negócios, perfil e canais retornados oficialmente, sem mostrar credenciais. **Estado: implementado; necessário CI aprovado e teste real no Telegram antes de afirmar resultado de produção**.

---

# Implementado — 2026-11-02: ficha consolidada por categorias

A ficha rica final passou a mostrar identificação básica + todos os dados adicionais disponibilizados via MTProto em categorias distintas; os blocos após os primeiros 13 campos deixaram de ser um agrupamento único. O formato HTML de fallback também apresenta seções e evita recortar uma tag na metade. O processo mostra fases intermediárias de coleta e então substitui o cartão pelo resultado final. **CI aprovado no commit 80eaa4d83b3aacf37f5402879e6c92b0877fce08; renderização final dessa revisão ainda depende de uma consulta real.** A execução 41525872904 confirmou que o fluxo Rich Message anterior editava a mensagem sem foto, mas não valida esta nova organização de categorias. O compartilhamento inicial de dados não é transportado de forma persistente para o worker; a ficha MTProto só contém o que foi confirmado no próprio protocolo.

---

# Mudança implementada — 2026-11-02: cartões Rich Message Bot API 10.3

A consulta cria um cartão persistente via `sendRichMessage`, transmite seu `message_id` ao workflow e usa `editMessageText` para exibir progresso e resultado final, com tabela compacta, botões e foto via multipart na própria Rich Message quando permitido. Adicionado `tgcloud/handlers/callback_query.js` para atualizar o cartão. Há fallback para HTML convencional e foto separada se a integração rica falhar. **IMPLEMENTADO; requer verificar renderização e atualização ao vivo do Telegram.** Preservados os cinco secrets originais, a pesquisa MTProto e o limite de dispatch.

---

# Complementação — 2026-11-02: novas fontes MTProto

**IMPLEMENTADO NO CÓDIGO, SUJEITO À CONFIRMAÇÃO EM PESQUISA REAL.** Foi acrescentada a coleta opcional do total ou amostra de fotos com `photos.getUserPhotos`, e do total de músicas com `users.getSavedMusic` quando a ficha completa indica música disponível. Foram expostos novos campos condicionais já presentes em `userFull` (`stars_rating`, `saved_music`, `business_work_hours`) e `channelFull`. Falhas de consultas opcionais não devem impedir a ficha principal. A documentação oficial confirma a existência dos métodos e sua disponibilidade a bots; isso não confirma que uma conta específica retornará valores. A evidência de execução deve ser coletada no resolver após o próximo teste real.

---

# Ajuste de robustez — 2026-11-02: resultado parcial das referências do Telegram

O handler passa a aproveitar imediatamente os campos opcionais recebidos pelo Telegram em `users_shared`, `chat_shared`, encaminhamentos, contatos e menções, sem consultar perfis pela Bot API. Campos de seleção são exibidos com origem, separados do resultado posterior do MTProto. Também foram acrescentados seletores de canal e grupo. Esse comportamento só está **IMPLEMENTADO** até teste manual do bot. O servidor pode recusar enriquecimento por ID; nenhum dado adicional é fabricado. Persistência de sessão e base de peers foram identificadas como aperfeiçoamento arquitetural futuro, não implementado nem recomendado em repositório público sem medidas de proteção.

---

# Atualização vigente — 2026-11-02: IDs e referências oficiais

A pesquisa por ID **não é mais rejeitada no handler**. O resolver usa as formas oficiais de referência do MTProto: métodos de usuário, canal ou grupo, com `access_hash=0` somente quando previsto para bots e permitido pelo Telegram; alternativa `ID @username` com comparação estrita da identidade devolvida por `contacts.resolveUsername`; e seleção/encaminhamento oficial fornecendo ID e eventual username. O Telegram pode negar a consulta por ID isolado. Não há pesquisa de perfis via `api.getChat`; o Bot API só transporta mensagens e referências compartilhadas. A seção histórica abaixo descreve versões substituídas. Evidência operacional exige uma busca real, não apenas CI, deploy ou healthcheck.

---

# AVISO — Histórico arquivado, não é a arquitetura vigente

Em 2026-11-02, a implementação passou a usar **MTProto como único mecanismo de consulta de perfis**. O Bot API permanece somente no transporte de mensagens e updates. Todas as menções abaixo ao `getChat`, ao fallback por erro 400, ao botão "Escolher usuário" e a relatórios obtidos por Bot API registram **uma versão antiga e descontinuada** e não servem mais como guia de execução, requisitos ou testes atuais. Para o comportamento atual, use `README.md`, `docs/launch-checklist.md` e o código publicado.

## Alteração vigente — 2026-11-02

- Pesquisa por `@username` no privado solicita diretamente o workflow de Telethon/MTProto.
- Inline apresenta um botão que abre o privado; nenhum lookup é feito inline.
- IDs numéricos isolados são rejeitados sem consulta porque não fornecem um `access_hash` confiável.
- Compartilhamentos de usuário, encaminhamentos, contatos e menções não usam o antigo relatório Bot API.
- Não há `api.getChat`; os recursos Bot API restantes se limitam a interface e entrega.
- Critério de verificação: CI, deploy e uma pesquisa real via workflow (não confundir com healthcheck).

---

# Registro de verificações, implementações, hipóteses e decisões

Data-base: 2026-11-01. Classificações:

- **VERIFICADO:** confirmado por execução reproduzível ou por fonte técnica citada.
- **IMPLEMENTADO:** existe no código; não foi exercitado ao vivo, ou só em parte.
- **HIPÓTESE:** explicação plausível, ainda não confirmada.
- **DECISÃO:** escolha do responsável pelo projeto, não exigência técnica universal.

Um teste confirma apenas o cenário que foi exercitado. Um deploy concluído demonstra que a publicação terminou, e não que o comportamento do bot está correto. As evidências são execuções do GitHub Actions: `https://github.com/romastefale/infocard/actions/runs/<número>`. Fontes lidas por cópia local: cópias da documentação do Serverless (extraídas em 10/10/2026 e 12/10/2026, no LoggerView e em `docs/`) e do Bot API (extraídas em 10/10, 12/10 e 17/10/2026, no LoggerView) (as páginas ao vivo de `core.telegram.org`, `docs.github.com` e `tl.telethon.dev` não abriram nesta sessão).

## 1. Verificações

| Comportamento | Condições | Esperado | Observado | Evidência | Situação |
|---|---|---|---|---|---|
| `getChat` com `@username` de usuário comum | SDK `api` do Serverless; `@tigrao` e um username inexistente; handlers rodados com `tgcloud run`; 2026-11-01 | dados do usuário | `400 Bad Request: chat not found` | runs 41306849416 e 41307104691 | Confirmado para esses dois casos |
| Causa do item anterior | leitura parcial do `Client.cpp` do `telegram-bot-api` (resumo de ferramenta, arquivo de 873 mil caracteres, não lido inteiro) | — | por username só são aceitos supergrupo, canal e bot | `tdlib/telegram-bot-api`, `TdOnCheckChatCallback` | Confirmado por leitura parcial |
| `fetch` do Serverless a hosts externos | `tgcloud run`; 2026-11-01 | resposta | falha: `t.me`, `telegram.me`, `telegram.dog`. Responde: `telegram.org`, `api.telegram.org`, `example.com`, `api.github.com` | runs 41307104691 e 41330709877 | Confirmado para esses hosts |
| Globais do runtime | `tgcloud run`; 2026-11-01 | — | existem: `crypto`, `crypto.subtle`, `crypto.getRandomValues`, `BigInt`, `TextEncoder`, `TextDecoder`, `WebAssembly`, `DataView`. Não existem: `atob`, `btoa`, `URL`, `setTimeout`, `performance`, `WebSocket`. Medições com `Date.now()` deram 0 ms | run 41326381391 | Confirmado |
| `fetch` com resposta binária | PNG de `telegram.org`; 2026-11-01 | bytes iguais | 28159 bytes, assinatura `89504e47…` correta | run 41326381391 | Confirmado para esse arquivo |
| MTProto por HTTP a partir do Serverless | POST de `req_pq_multi`; 2026-11-01 | `resPQ` | `http://149.154.167.51:80/api` e outros IPs: `403 access denied` do `squid/6.13`. `https://venus.web.telegram.org/api`: `403` do nginx | runs 41326381391 e 41326461110 | Confirmado |
| O mesmo pacote a partir do runner do Actions | 2026-11-01 | `resPQ` | IPs por HTTP: `200` com `resPQ` e nonce igual. `https://venus.web.telegram.org/api`: `403` | run 41326518485 | Confirmado |
| `contacts.resolveUsername` com o token do bot | Telethon 1.45.0 no Actions; `tigrao`; 2026-11-01 | ID do usuário | resolveu para o ID `8921622168`; `username` principal vazio | run 41325053290 | Confirmado para esse caso. A conta já tinha falado com o bot, então **não** prova o caso de quem nunca falou |
| `GH_DISPATCH_TOKEN` de dentro do Serverless | `tgcloud run`; 2026-11-01 | ler e disparar | lê o workflow (`200`); o disparo devolve `403 Resource not accessible by personal access token` | runs 41330709877, 41330779192 e 41332393101 | Confirmado: o token atual não pode disparar |
| Permissão do `GH_DISPATCH_TOKEN` depois da troca | deploy manual (`workflow_dispatch`) nº 18, 2026-11-01 17:53 UTC, mesmo código do nº 17 | passo "Validar a permissão…" verde | a execução inteira concluiu com sucesso, incluindo o passo de validação; o nº 17, 5 minutos antes, falhou nesse passo | runs 41333359017 (falha) e 41333747195 (sucesso) | Confirmado: o token agora tem permissão de disparo. Não prova que o bot dispara e que o job resolve |
| `push` com módulo vazio | `schema.js` com 0 bytes | publicar | `Error: Module code is empty`; nada foi publicado | run 41325623276 | Confirmado |
| Migração aditiva | tabela `disparos` nova | criar a tabela | `Migration complete. Applied: 1` | run 41329731536 | Confirmado |
| `migrate --safe --local` antes do `push` | sem mudança de schema; 2026-11-01 | sem erro | `No schema changes`, depois o `push` normal | run 41332145298 | Confirmado só para o caso sem mudança de schema |
| Webhook | vários deploys | handlers e webhook coerentes | `allowed updates: message, inline_query`, `in sync`, 0 pendentes | run 41332145298 | Confirmado nesses deploys |
| Envio de resposta HTML ao privado | `handlers/message` com chat real; versão anterior do relatório; 2026-11-01 | envio aceito | terminou sem exceção | run 41306849416 | Confirmado só para essa versão do texto |

## 2. Implementado, sem verificação ao vivo

| Comportamento | Onde | Já observado | Falta |
|---|---|---|---|
| Disparo do workflow pelo bot e resposta "Buscando…" | `consulta.js`, `despacho.js` | o token atual passa na validação do deploy | um disparo real feito pelo bot (204) e a resposta chegando |
| Relatório MTProto completo (bio, aniversário, dados comerciais, bot, canal) e envio da foto | `scripts/resolver.py` | usuário e bot lidos, foto enviada (seção 8) | `getFullChannel` com sucesso, e um usuário com bio, aniversário ou dados comerciais |
| Botão "Escolher usuário", leitura de mensagem encaminhada e de contato | `envio.js`, `message.js`, `relatorio.js` | nada | uma execução real de cada |
| Limite por chat e total, em uma instrução SQL | `limite.js` | a tabela existe | uma execução, inclusive concorrente |
| Reserva desfeita se o disparo falha; bloqueio se o controle falha | `consulta.js` | nada | provocar as duas falhas |
| Aviso ao chat quando o workflow falha sem responder | `resolver.yml` | nada | uma falha real do job |
| Validação do token no deploy | `deploy.yml` | detectou o 403 | o caso `422`, com token correto |

As correções do commit `4f634de` foram feitas em lote (oito alterações juntas); não há verificação individual de cada uma.

## 3. Hipóteses

- O MTProto resolve o ID de um usuário comum que nunca falou com o bot (`access_hash` 0). **Não sustentada pela primeira execução com usuário comum** (seção 8: ID 5249367417, sem dados e `UserIdInvalidError`); resolveu só o 777000, conta de serviço. Base original: o TDLib monta `inputUser(id, 0)` e `inputChannel(id, 0)` para bots (`UserManager.cpp`, `ChatManager.cpp`). Falta confirmar que o servidor aceita. Como confirmar: consultar o ID de alguém que nunca falou com o bot.
- `tigrao` é um username adicional da conta. Base: o campo `username` principal veio vazio. Como confirmar: ler os `usernames` ativos no relatório.
- O Telethon 1.45.0 expõe os campos lidos em `resolver.py`. A leitura é defensiva, então um campo ausente apenas não aparece.
- Reutilizar a sessão MTProto entre buscas poderia causar `AuthKeyDuplicatedError` com execuções simultâneas (aviso da documentação do Telethon). Não foi testado.
- O tempo de espera do job no Actions e o limite de uso do `resolveUsername` são desconhecidos.

## 4. Decisões vigentes

- Sem comentários no código; sem testes escritos por quem escreve o código; publicar direto na `main` (responsável pelo projeto).
- A busca MTProto só roda no privado; grupos são ignorados.
- No `resolver.py`, a espera pedida pelo Telegram (`FloodWait`) é cumprida e a operação é repetida, em qualquer chamada MTProto da busca, até 600 s de espera somada; o job tem `timeout-minutes: 15`. Acima disso o chat recebe a falha com o tempo pedido. Base: a política do TDLib de aguardar `FLOOD_WAIT_X` por X s. O valor 600 é escolha minha. Antes desta mudança o teto era 120 s e o run 41340057109 (espera de 129 s) desistiu.
- Limite das buscas: 1 por chat e 6 no total a cada 60 s. Valores escolhidos por mim, não são limites do Telegram.
- Se o controle de limite falhar, o bot não dispara e avisa.
- Apenas `400` do `getChat` cuja descrição indique `chat not found` é tratado como entrada não resolvida. Para username, isso pode iniciar o fallback MTProto no privado; outros erros 400 são reportados sem disparo. Esta regra evita transformar erros de requisição distintos em “usuário não encontrado”.
- Escrita e disparo não são repetidos; só o `getChat` é repetido uma vez, em falha de rede ou 5xx. Base: `NetQueryDelayer.cpp` do TDLib (o TDLib só repete em falha de transporte e em 500 com mensagem específica).
- O segredo do GitHub é gravado em `tgcloud/lib/segredos.js` no deploy, porque o runtime não tem variáveis de ambiente.
- A migração roda antes do `push` (`migrate --safe --local`).

## 5. Decisões superadas

| Decisão antiga | Motivo | Atual |
|---|---|---|
| Achar o ID dentro do `file_id` da foto enviada ao chat de cache (`CACHE_CHAT_ID`) | O código do TDLib atribui `PhotoSizeSource::thumbnail` às fotos de mensagem, sem `dialog_id` | Leitura pelo `getChat` e pelo MTProto |
| Ler a página pública `t.me` | O `fetch` do Serverless a bloqueia | MTProto no Actions |
| Seguir sem limite se o banco falhar | Fail-open | Fail-closed |
| Repetir o disparo do workflow | Um disparo duplicado inicia dois workflows | Sem repetição |
| `migrate` depois do `push` | Janela com código novo e schema antigo | `migrate --local` antes do `push` |

## 6. Revisão de 2026-11-01 e limites

| Verificação | Resultado | Limite |
|---|---|---|
| Sintaxe de `scripts/resolver.py` (`ast.parse`) | sem erro | não executa o script nem exercita a API do Telethon |
| Sintaxe dos módulos `.js` (`node --check`) | sem erro | não resolve os imports do SDK nem executa nada |
| YAML dos workflows (`yaml.safe_load`) | sem erro | não prova que o GitHub aceita os passos |
| Busca por comentários em `tgcloud/` e `scripts/` | nenhum; as duas ocorrências de `//` são parte de `tg://` | só texto |
| Releitura de `consulta.js`, `despacho.js`, `limite.js`, `message.js`, `inline_query.js` | nenhum defeito novo encontrado | releitura por quem escreveu o código; não substitui execução |

Pendente: o token já passa na validação do deploy (seção 1, run 41333747195). Falta exercitar o bot: enviar o `@username` e o ID de alguém que nunca usou o bot e anotar aqui o resultado observado.

Os itens corrigidos em lote no commit `4f634de` não têm verificação individual; o registro os mantém na seção 2.

## 7. Lista de 15 apontamentos: situação no código em 2026-11-01

Conferido por leitura do código atual; nenhum item foi exercitado ao vivo.

| # | Apontamento | Situação no código | Observação |
|---|---|---|---|
| 1 | Limite falha aberto | Corrigido: sem controle de limite, o bot não dispara e avisa | IMPLEMENTADO |
| 2 | Limite não atômico | Corrigido: um `INSERT … SELECT … WHERE` e `rowsAffected` | IMPLEMENTADO |
| 3 | Disparo duplicado | Corrigido: só o `getChat` é repetido | IMPLEMENTADO |
| 4 | Retentativa sem espera | Não corrigido: o runtime não tem `setTimeout` (run 41326381391), então não há como esperar dentro do handler. Há uma única repetição imediata, só para `getChat` | Limitação |
| 5 | 429 / `retry_after` | 429 não é repetido; o `retry_after` é mostrado ao usuário | IMPLEMENTADO |
| 6 | Qualquer 400 aciona o MTProto | Mantido por decisão: não há classificação por texto de erro | DECISÃO |
| 7 | Fallback HTML perde conteúdo | Os relatórios só usam `<a href>`, `<b>` e `<code>` (conferido por busca no código). O link vira `texto (url)` no JavaScript e, desde esta revisão, também no `resolver.py`; `<b>` e `<code>` só perdem a formatação; o texto é escapado antes, e as entidades são desfeitas depois | IMPLEMENTADO |
| 8 | Indicador de foto | Corrigido: o relatório diz "enviada junto", "existe, mas não foi possível enviar" ou "não" | IMPLEMENTADO |
| 9 | Tamanho do relatório | Corrigido: o corte considera campos e avisos | IMPLEMENTADO |
| 10 | Erro HTTP vira erro de JSON | Corrigido: `chamar` tolera corpo não JSON | IMPLEMENTADO |
| 11 | Primeira entidade sem conferir | Corrigido: casamento por ID do peer | IMPLEMENTADO |
| 12 | `curl` sem falhar em 4xx/5xx | Corrigido: `--fail-with-body` | IMPLEMENTADO |
| 13 | Aceite do disparo como conclusão | Corrigido: o texto diz que a busca foi pedida e que a resposta só chega se ela concluir | IMPLEMENTADO |
| 14 | Reserva fica após falha | Corrigido: a reserva é liberada se o disparo falha | IMPLEMENTADO |
| 15 | Publicar antes de migrar | Corrigido: `migrate --safe --local` roda antes do `push` | VERIFICADO só para o caso sem mudança de schema (run 41332145298) |

## 8. Execuções do resolver em 2026-11-01 (19:05–19:14 UTC)

Salvo onde está indicado, disparadas por mim com `workflow_dispatch`, com resposta para o chat do responsável. Alvos: contas oficiais ou públicas. Logs só têm nomes de campos, não valores.

| Comportamento | Condições | Esperado | Observado | Evidência | Situação |
|---|---|---|---|---|---|
| Consulta por ID `777000` | ID `777000` (conta de serviço do Telegram) | resolver pelo ID | resolveu como usuário; foto e mensagem enviadas; job verde | run 41339952480 | Confirmado só para essa conta. O TDLib trata o 777000 como usuário conhecido, fixo no código, com hash embutido (`td/telegram/UserManager.cpp:5143-5149`); **não** é evidência para outros usuários |
| Username de bot | `@BotFather` | relatório completo | tipo `bot`; campos de bot e `about` lidos; foto e mensagem enviadas; job verde | run 41340054405 | Confirmado |
| `getFullUser` e `download_profile_photo` | os dois itens acima | campos do perfil completo e foto | perfil completo lido; foto enviada nos dois casos | runs 41339952480 e 41340054405 | Confirmado nesses dois casos |
| Username de canal sob limite do Telegram | `@telegram`, depois de duas buscas no mesmo minuto | resultado ou aviso | `FloodWaitError 129`, acima do `ESPERA_MAXIMA` de 120 s; o script enviou o aviso ao chat e saiu com erro (job vermelho); o passo de aviso final não reenviou | run 41340057109 | Confirmado: a falha chegou a quem consultou. O motivo do limite (três buscas em ~1 min) é hipótese |
| Username comum | `@enriquecimentos`, run que **não** foi disparada por mim | relatório | tipo `usuário`; só `first_name`, `id`, `username`, `status` na entidade; sem foto; mensagem enviada; job verde | run 41340128699 | Confirmado para o resolver. A origem do disparo não foi verificada; pode ter vindo do bot ou de um disparo manual |
| Consulta por ID de usuário comum, sem `access_hash` | ID `5249367417`, run **não** disparada por mim; depois repetido por mim com o código novo | dados do usuário | `users.getUsers` não devolveu o usuário (run 41340413917). Com a segunda via, `users.getFullUser` respondeu `UserIdInvalidError` (run 41340622977). Em ambos o chat recebeu a explicação; jobs vermelhos | runs 41340413917 e 41340622977 | Confirmado para esse ID: a consulta por ID sem hash não funcionou. Não generaliza para todo usuário comum; contradiz a expectativa tirada do código do TDLib |
| `@telegram` (canal) depois de ajustar a espera | mesmo alvo que antes deu `FloodWait` | relatório de canal | resolveu como canal; `getFullChannel` e foto; sem `FloodWait` desta vez | run 41340514301 | Confirmado para o canal. O caminho de espera nunca foi exercitado: o limite não voltou a ocorrer |

O que isto não prova: o bot disparar o workflow sozinho (nenhum log do bot foi lido), o botão "Escolher usuário", mensagem encaminhada, contato, o limite de 1 busca por chat e a liberação da reserva.

## 9. IDs numéricos deixam de disparar a busca MTProto (2026-11-01)

Base: (a) no `td`, um bot monta `inputUser(id, 0)` para usuário desconhecido (`UserManager.cpp:5332-5335`), mas o código não diz que o servidor aceita; (b) o 777000 é caso fixo do TDLib (`UserManager.cpp:5143-5149`); (c) o único ID de usuário comum testado falhou nas duas chamadas, `users.getUsers` e `users.getFullUser` (seção 8); (d) a documentação do `getChat` cobre ID ou username de supergrupo ou canal.

Mudança: para entrada numérica que o `getChat` não resolve, o bot responde na hora com o erro da API e indica o botão "Escolher usuário", a mensagem encaminhada e o `@username`, sem reservar limite nem disparar o workflow. Só `@username` dispara a busca MTProto. Canais e supergrupos por ID não foram testados e também deixam de disparar. Situação: IMPLEMENTADO; a resposta real do bot a um ID não foi observada. O caminho por ID do `resolver.py` foi removido, por não ter mais chamador.

## 9.1. Correção de robustez após confronto com fontes oficiais (2026-11-01)

- A documentação oficial de `contacts.resolveUsername` afirma que **bots e usuários podem usar o método**. Isso promove a capacidade do fallback por username de hipótese de permissibilidade para comportamento DOCUMENTADO; sucesso para um alvo específico continua dependente da resposta do Telegram.
- O fallback deixou de classificar todo HTTP 400 do `getChat` como “não resolvido”: agora exige `chat not found`.
- O cliente de workflow aceita HTTP 200 e 204 como sucesso. O endpoint atual do GitHub documenta 200; o projeto mantém a versão REST `2022-11-28`, na qual 204 foi observado.
- O README foi atualizado porque os runs 41345590300 e 41345609607 já comprovam um disparo do resolver originado pelo handler.
- Referências oficiais consolidadas em `docs/fontes-oficiais.md`.

## 10. Revisão do código contra a documentação do Bot API (2026-11-01)

Fonte: cópia de 17/10/2026 da documentação do Bot API (`ChatFullInfo`, `MessageEntity`, `tg://user?id=`).

| Item | Antes | Depois | Situação |
|---|---|---|---|
| Nota sobre o link `tg://user?id=` | afirmava que só funciona se a pessoa já falou com o bot, sem fonte | a documentação diz que o link funciona "se permitido pelas configurações de privacidade"; `has_private_forwards` indica que só vale em chats com a pessoa; o texto passou a dizer isso | IMPLEMENTADO |
| Campos do `getChat` | tipo, ID, nome, título, username, usernames ativos, bio, descrição, foto | também aniversário, apresentação e endereço comerciais, canal pessoal, localização, fórum, chat vinculado, modo lento, apagar mensagens, entrada por pedido, membros ocultos, conteúdo protegido, link de convite, todos campos documentados do `ChatFullInfo`, mostrados só quando vêm preenchidos | IMPLEMENTADO |
| Menção com `text_mention` | ignorada | a mensagem com menção a um usuário sem username traz o `user` (documentação de `MessageEntity`); o bot mostra ID, nome e username dele | IMPLEMENTADO |
| ID desconhecido no modo inline | pedia o "botão abaixo", que não existe no inline | orienta a abrir o privado com o bot | IMPLEMENTADO |
| Erro inesperado nos handlers | sem resposta ao usuário | responde com o nome e a mensagem do erro | IMPLEMENTADO |

Nenhum dos itens foi exercitado ao vivo.

## 11. Busca inline de @username continua no privado (2026-11-01)

Problema no código: no modo inline, um `@username` que o `getChat` não resolve (400) sempre terminava em erro, porque a busca por MTProto só pode rodar no privado e o inline responde na hora.

Base: documentação do Bot API (cópia de 17/10/2026): `answerInlineQuery` aceita `button` (`InlineQueryResultsButton`) com `text` e `start_parameter` (1 a 64 caracteres, `A-Za-z0-9_-`); ao tocar, o usuário vai ao privado com o bot e o bot recebe `/start <parâmetro>`.

Mudança: o resultado inline do 400 traz o botão "Buscar @usuario no privado" com o username (1 a 32 caracteres `A-Za-z0-9_`) como parâmetro; no privado, `/start usuario` é tratado como a consulta `usuario`. A nota "só roda no privado" aponta o botão. Também saiu "ou bot" do texto de falha do username: a documentação do `getChat` cita só supergrupo e canal. Situação: IMPLEMENTADO; o botão e o `/start` com parâmetro não foram exercitados.

## 12. Handlers executados na plataforma e remoção do reenvio em texto puro (2026-11-01)

Execução: workflow temporário com `tgcloud run`, que roda o código local na plataforma, com o SDK real (`getChat`, `sendMessage`, `fetch`), payloads montados por mim e resposta para o chat do responsável. Run 41345590300, commit `3453e3e`.

| Comportamento | Condições | Esperado | Observado | Evidência | Situação |
|---|---|---|---|---|---|
| ID numérico desconhecido, privado | `text: "5249367417"` | `getChat` falha, resposta imediata, sem disparo | `getChat` 400 `chat not found`; o handler terminou sem exceção em 556 ms; nenhum workflow novo no resolver nesse instante | run 41345590300 | Confirmado nessa execução com payload sintético; a mensagem entregue ao usuário não foi lida por mim |
| `/start <username>`, privado | `text: "/start tigrao"` | `getChat` 400, disparo do resolver | `getChat` 400; o handler terminou sem exceção em 1,8 s; o resolver ganhou um run `workflow_dispatch` às 20:12:00, que terminou com sucesso | runs 41345590300 e 41345609607 | Confirmado nessa execução: o código do handler dispara o resolver com o token do deploy |
| `/start` sem parâmetro | `text: "/start"` | resposta de entrada não reconhecida | terminou sem exceção em 156 ms | run 41345590300 | Confirmado só a ausência de exceção |
| Inline de username | `query: "tigrao"`, `id: "1"` | `getChat` 400, resposta inline com botão | `getChat` 400; `answerInlineQuery` falhou com `query is too old ... or query ID is invalid` (esperado, o ID da consulta era inventado); o código então repetia em texto puro e falhava de novo, com exceção | run 41345590300 | Defeito confirmado: o reenvio por qualquer 400 não tinha efeito. O botão **não** pôde ser validado: a consulta inline real é necessária |

Mudança: `envio.js` e `resolver.py` deixam de reenviar em texto puro após um 400; o HTML é montado com escape e as marcas fixas `<b>`, `<code>` e `<a href>`, e uma recusa do Telegram aparece como erro registrado. Situação: IMPLEMENTADO; depende de redeploy.

## 13. Endurecimento para novo repositório e lançamento (2026-11-01)

Situação: **IMPLEMENTADO localmente; requer primeiro deploy no novo repositório para verificação operacional.**

- Removido o owner/repo hardcoded de `tgcloud/lib/despacho.js`. O destino do workflow passa a ser injetado pelo deploy a partir de `github.repository`, evitando que uma cópia do projeto dispare acidentalmente o repositório histórico.
- Atualizado `X-GitHub-Api-Version` para `2026-03-10`, versão exibida na documentação REST corrente consultada em 2026-11-01. O cliente mantém aceitação defensiva de 200 e 204 como sucesso.
- A injeção do token foi movida para depois de `tgcloud status`; o arquivo versionado continua contendo somente placeholders vazios.
- Adicionado workflow `CI`, `npm run check` e verificação explícita de que `tgcloud/lib/segredos.js` não contém segredo commitado.
- A validação do token no deploy deixou de depender de um dispatch inválido/HTTP 422: agora dispara `resolver.yml` com `healthcheck=true`, caminho que não acessa Telegram/MTProto.
- `.gitignore` passou a excluir `.env`, sessões Telethon e ambientes virtuais.
- `/start` sem parâmetro e `/help` agora retornam ajuda em vez de cair na validação de entrada.
- Adicionados `SECURITY.md`, `.env.example` e `docs/launch-checklist.md`.

Critério de conclusão: CI verde no novo repositório, deploy verde com todos os secrets configurados e execução dos smoke tests do checklist. Até isso ocorrer, o pacote é **launch-ready**, não “produção comprovada”.
