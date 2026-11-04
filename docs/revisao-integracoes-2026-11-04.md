# Integrações orientadas pelas APIs — revisão de 2026-11-04

Este relatório substitui a lista anterior de políticas locais. A documentação oficial determina os contratos; os testes determinam o que foi observado. As funcionalidades de consulta, relatórios, arquivos e seletores permanecem no projeto. README.md, AGENTS.md e SECURITY.md continuam excluídos na branch do PR #32.

## Substituições implementadas

| Item revisto | Solução implementada | Referência |
|---|---|---|
| Regex locais de credenciais, StringSession vazia, timeouts de autenticação 90/30 s e segunda conferência de identidade | TelegramClient.start(bot_token=...) e SQLiteSession do Telethon, com desconexão e fechamento garantidos. Foram removidos os overrides receive_updates=False e flood_sleep_threshold=0. O SDK conserva seu tratamento nativo; FLOOD_WAIT propagado aguarda a duração do servidor, sem teto local de 600 s nem acréscimo de um segundo. | [Cliente Telethon](https://docs.telethon.dev/en/stable/modules/client.html), [sessões](https://docs.telethon.dev/en/stable/concepts/sessions.html), [bots MTProto](https://core.telegram.org/api/bots) |
| Teto genérico de 52 bits para qualquer ID | Intervalos oficiais distintos para usuários, grupos, canais/supergrupos e monoforums, aplicados no worker, parser e callbacks. O intervalo reservado a secret chats não é aceito, pois a instância oficial da Bot API não os suporta. | [Bot API dialog IDs](https://core.telegram.org/api/bots/ids) |
| Seleção manual de entidade por ID interno | Comparação do peer marcado retornado por contacts.resolveUsername com os peers marcados das entidades, usando utils.get_peer_id. Assim, IDs sobrepostos de tipos diferentes não colidem. ChatEmpty não é convertido em perfil confirmado. | [contacts.resolveUsername](https://core.telegram.org/method/contacts.resolveUsername), [peers](https://core.telegram.org/api/peers) |
| Fallback rígido que rejeitava toda mudança de ID | getChat pode seguir migrate_to_chat_id informado pelo servidor e preservar a cadeia de migração. A resolução aceita o novo ID quando a migração foi documentada na resposta. Um ID divergente sem migração continua sendo uma resposta inconsistente. As consultas seguintes usam o ID retornado, e a resposta obtida é reutilizada. | [ResponseParameters](https://core.telegram.org/bots/api#responseparameters), [getChat](https://core.telegram.org/bots/api#getchat) |
| Construtores manuais como primeira opção | O cache da sessão fornece o hash completo para consultas numéricas; utils.get_input_peer/get_input_user/get_input_channel fazem as conversões. Se faltar um peer completo utilizável, o bot usa os construtores com hash zero previstos pelo protocolo. Não se reaproveitam hashes entre contas ou sessões de autorização. | [Access hash](https://core.telegram.org/api/peers#access-hash), [entidades Telethon](https://docs.telethon.dev/en/stable/concepts/entities.html) |
| Cinco tentativas, orçamento de 600 s, atraso inventado e confirmação genérica por ID positivo | O campo ok determina o resultado da Bot API. retry_after governa a repetição sem reduzir a espera. migrate_to_chat_id atualiza chat_id em JSON e multipart, preservando os bytes do arquivo. Sem instrução de repetição do servidor, o erro é devolvido com seus parâmetros. message_id=0 é aceito sem disparar fallback duplicado, mas deixa a entrega pendente e impede anunciar conclusão integral. | [Making requests](https://core.telegram.org/bots/api#making-requests), [ResponseParameters](https://core.telegram.org/bots/api#responseparameters), [Message](https://core.telegram.org/bots/api#message) |
| Erros reduzidos apenas ao nome e notificação curl que descartava o contrato de resposta | JavaScript inspeciona BotApiError: method, code, description e parameters. Falhas de transporte e 429 não viram automaticamente um segundo envio em outro formato. Edição inalterada é tratada sem novo envio. A notificação usa o mesmo cliente Bot API, processa espera/migração, verifica a resposta e registra diagnóstico estruturado. A resposta JSON de erro do GitHub também fornece sua mensagem oficial e status, em vez de imprimir o corpo bruto ou reduzir tudo ao nome da exceção. Campos de credenciais não entram no diagnóstico; descrições passam por redação. | [Making requests](https://core.telegram.org/bots/api#making-requests), [erros MTProto](https://core.telegram.org/api/errors), SDK 0.2.0 instalado e sua interface BotApiError |

Os comportamentos que são exigências do contrato — tipos de peer, resposta ok/result, hash zero para bots sem hash completo e representação de mensagens pendentes — não foram removidos para permitir resultados incorretos. Foram vinculados às fontes acima e integrados ao fluxo real. A API não fornece uma autorização para tratar erro como sucesso.

## Sessão e limites operacionais

TELETHON_SESSION_DIR permite selecionar um diretório privado para reutilizar a sessão SQLite e o cache de entidades. O diretório é criado com modo 0700; os nomes de sessão derivam do token sem publicá-lo. Arquivos de sessão não são exportados nem entram no Git. Não configurar essa variável em um diretório compartilhado entre processos concorrentes.

Sem diretório configurado, o worker usa um diretório temporário privado e o remove ao desconectar. Há persistência SQLite e cache durante a execução; isso não cria persistência entre runners efêmeros do GitHub Actions. Não foi provisionado armazenamento durável de credenciais nem cache de sessão em artifacts/Actions cache.

O limite de cinco minutos da etapa de validação foi removido para não interromper uma espera legítima de rate limit. O timeout geral do job continua sendo um limite operacional do GitHub Actions, não um prazo definido pelo Telegram. O timeout de transporte HTTP também é uma decisão operacional, distinta das esperas retry_after/FLOOD_WAIT.

Erros sem resposta conclusiva não autorizam repetir uma escrita cegamente: a assinatura consultada de sendMessage não contém chave de idempotência. O cliente apresenta a falha; não afirma que a API garante entrega exatamente uma vez. Migração e rate limit com parâmetros oficiais têm tratamento explícito.

## Validação desta substituição

- 39 verificações Python passaram: limites oficiais, intervalos excluídos, retry_after de 1000 s simulado sem corte, FLOOD_WAIT de 1000 s simulado sem acréscimo, migração JSON, resposta inválida, escrita 503 sem duplicação, mensagem pendente, redação, hashes completos/min, persistência SQLite do cache e migração na resolução.
- Uma sondagem adicional de migração multipart confirmou a troca de chat_id preservando os bytes do documento.
- Quatro cenários da notificação passaram: recusa, aceitação pendente, sucesso com marcador e prevenção de segundo envio.
- 30 verificações JavaScript passaram para os limites oficiais e roundtrip dos callbacks r/f.
- 13 verificações JavaScript com modelo do SDK passaram para diagnóstico, redação, ausência de fallback em 429/transporte, fallback após recusa 400 e edição inalterada. Isso não equivale a executar o runtime Serverless publicado.
- npm run check, actionlint 1.7.12 e git diff --check passaram. A inspeção do Telethon 1.45.0, layer 229, passou em Python 3.12 e 3.13: 58 importações e 54 assinaturas, além da importação dos módulos sem rede.

A [CI do commit aeef595](https://github.com/morfalespi/IC/actions/runs/41928421679) passou. A [validação real dessa substituição](https://github.com/morfalespi/IC/actions/runs/41928450861) também passou: getMe confirmou o bot, getChat leu o canal público, TelegramClient.start autenticou com SQLiteSession e o perfil completo MTProto correspondeu ao mesmo canal. O resumo registrou zero erros MTProto nessa consulta. Não houve envio de mensagens. Foram verificadas adicionalmente as mensagens estruturadas de erro do GitHub, redação de tokens sintéticos, resposta sem JSON e aceitação de dispatch; esse complemento JavaScript não altera o caminho Python testado nessa execução real.

## Evidências anteriores, com escopo restrito

A [consulta MTProto anterior](https://github.com/morfalespi/IC/actions/runs/41906828053) confirmou autenticação e perfil completo antes desta substituição. A [validação entre APIs anterior](https://github.com/morfalespi/IC/actions/runs/41923236979) confirmou getMe, getChat, igualdade do canal e leitura MTProto, após retry_after=203 s e FLOOD_WAIT=80 s. Essas execuções são históricas; usaram o código anterior.

O PR permanece sem merge ou deploy. Não foi validada entrega real de mensagens/arquivos ao usuário nem cobertura exaustiva de todos os métodos oficiais. Não houve exposição de tokens ou sessões como parte das verificações registradas.
